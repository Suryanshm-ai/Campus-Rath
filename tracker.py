import streamlit as st
import pydeck as pdk
from streamlit_geolocation import streamlit_geolocation
import requests
import time
import json
import os

# ==========================================
# 1. UNIVERSAL PAGE CONFIG
# ==========================================
# We use "wide" layout for the map, but we will artificially center the admin panel later!
st.set_page_config(page_title="Campus Rath | Command Center", layout="wide")

FIREBASE_URL = "https://campusrath-default-rtdb.firebaseio.com/rath_01.json"
GEOJSON_ROUTE_PATH = "newcampusmap.geojson"
ADMIN_PIN = "9218"

# ==========================================
# 2. SESSION STATE & SECURITY
# ==========================================
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'admin_screen' not in st.session_state:
    st.session_state.admin_screen = 'question'

# --- THE SECRET SIDEBAR GATEWAY ---
st.sidebar.title("🔐 Admin Gateway")

if not st.session_state.is_admin:
    # Public Mode: Show Password Box
    passcode = st.sidebar.text_input("Driver PIN", type="password", placeholder="Enter PIN...")
    
    # Auto-login if PIN is correct
    if passcode == ADMIN_PIN:
        st.session_state.is_admin = True
        st.rerun()
    elif passcode != "":
        st.sidebar.error("❌ Access Denied")
else:
    # Admin Mode: Show Logout Button
    st.sidebar.success("✅ Driver Authenticated")
    if st.sidebar.button("🚪 Logout of Terminal"):
        st.session_state.is_admin = False
        st.session_state.admin_screen = 'question' # Reset terminal screen
        st.rerun()


# ==========================================
# ==========================================
# 3. PUBLIC VIEW: THE 3D TRACKER
# ==========================================
# ==========================================
if not st.session_state.is_admin:
    
    # --- TRACKER CSS ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #0E1117; color: white; }
        .welcome-banner {
            background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 20px;
            padding: 40px; border: 1px solid rgba(144, 144, 144, 0.1); text-align: center;
            margin-top: 15px; box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.17);
        }
        .project-title { font-family: 'Orbitron', sans-serif; color: #FFFFFF; font-size: 3.5rem; letter-spacing: 5px; text-shadow: 0 0 20px rgba(0, 201, 255, 0.5); }
        .rath-quote { color: #00FFA3; font-size: 1.3rem; font-style: italic; margin-top: 10px; }
        .location-box {
            background: rgba(0, 201, 255, 0.1); border: 2px dashed #00C9FF;
            border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;
        }
        </style>
        <div class="welcome-banner">
            <h1 class="project-title">CAMPUS RATH</h1>
            <p style="color: #00C9FF; font-weight: 400; letter-spacing: 2px;">DEVELOPED BY SURYANSH, SHASHANK & VINEET | AI & DATA SCIENCE</p>
            <p class="rath-quote">"Precision in Mobility, Intelligence in Every Mile."</p>
        </div>
        """, unsafe_allow_html=True)

    # --- TRACKER METRICS ---
    st.write("")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Active Rath", "01", "⚡ Online")
    m_col2.metric("Wait Time", "2.5 min", "📉 Efficient")
    m_col3.metric("Campus Route", "7.0 km", "📍 Mapped")
    m_col4.metric("System Mode", "Hybrid 3D", "🚀 Optimized")

    # --- FETCH FIREBASE ---
    curr_lat, curr_lon = 25.35599, 81.88926 
    auto_status = "Unknown"
    try:
        resp = requests.get(FIREBASE_URL)
        if resp.status_code == 200 and resp.json():
            db_data = resp.json()
            if db_data.get("latitude") and db_data.get("longitude") and db_data.get("status") == "Active":
                curr_lat = db_data.get("latitude")
                curr_lon = db_data.get("longitude")
            auto_status = db_data.get("status", "Unknown")
    except: pass 

    # --- TRACKER UI CONTROLS ---
    st.write("---")
    ui_col1, ui_col2, ui_col3 = st.columns([1, 1, 1])

    with ui_col1:
        st.markdown("### 🗺️ Select Map View")
        map_style_choice = st.radio("", ["Dark Mode", "Satellite View", "Light Mode", "Street Map"], horizontal=True)
        style_mapping = {"Dark Mode": "dark", "Satellite View": "satellite", "Light Mode": "light", "Street Map": "road"}
        selected_map_style = style_mapping[map_style_choice]

    with ui_col2:
        st.markdown("### 📍 Find My Location")
        st.caption("Turn off Live Tracking before clicking!")
        user_loc = streamlit_geolocation()
        user_lat, user_lon = None, None
        if user_loc and user_loc.get('latitude'):
            user_lat, user_lon = user_loc['latitude'], user_loc['longitude']
            st.success("✅ Location Locked!")

    with ui_col3:
        status_color = "#00FFA3" if auto_status == "Active" else "#FF4B4B"
        st.markdown(f"""
            <div class="location-box" style="padding: 10px;">
                <h4 style='color: white; margin-bottom: 5px;'>📡 RATH STATUS: <span style='color: {status_color};'>{auto_status.upper()}</span></h4>
                <p style='color: #00C9FF; font-weight: bold; margin: 0;'>GPS: {curr_lat:.5f}, {curr_lon:.5f}</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 3D MAP ENGINE ---
    layers = []
    name_to_emoji = {
        "Main Gate": "⛩️", "Campus GYM": "🏋️", "Badminton Court": "🏸", "Multipurpose Block": "🏫",
        "Administrative Block": "💼", "Police Chowki": "🚓", "Boys Hostel": "🛌", "Water Tank": "💧",
        "Pariksha Bhawan": "📝", "Polly House": "🌱", "Block-A": "🅰️", "Block-B": "🅱️",
        "Block-C": "🅲️", "Block": "🏢", "Vice Chancellor Block": "🎓"
    }

    def hex_to_rgb(hex_color):
        hex_color = str(hex_color).lstrip('#')
        if len(hex_color) == 6: return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)] + [200]
        return [255, 75, 100, 220] 

    if os.path.exists(GEOJSON_ROUTE_PATH):
        with open(GEOJSON_ROUTE_PATH, "r") as f:
            raw_geojson = json.load(f)
            
        paths, landmarks = [], []
        for feature in raw_geojson.get("features", []):
            geom_type = feature.get("geometry", {}).get("type", "")
            props = feature.get("properties", {})
            
            if geom_type in ["LineString", "MultiLineString"]:
                paths.append(feature)
            elif geom_type in ["Point", "Polygon", "MultiPolygon"]:
                name = props.get("name") or props.get("Name") or props.get("title") or "Landmark"
                color_hex = props.get("marker-color") or props.get("fill") or "#FF4B64"
                custom_height = props.get("height") or props.get("Height") or props.get("elevation") or 40
                
                emoji_icon = "📍" 
                for dict_name, emoji in name_to_emoji.items():
                    if dict_name.lower() in name.lower():
                        emoji_icon = emoji
                        break
                
                feature["properties"]["name"] = f"{emoji_icon} {name}"
                feature["properties"]["fill_color"] = hex_to_rgb(color_hex)
                feature["properties"]["building_height"] = float(custom_height)
                landmarks.append(feature)

        if paths:
            layers.append(pdk.Layer(
                "GeoJsonLayer", data={"type": "FeatureCollection", "features": paths},
                stroked=True, filled=False, get_line_color="[0, 201, 255, 255]", get_line_width=8, opacity=0.8, pickable=False 
            ))

        if landmarks:
            layers.append(pdk.Layer(
                "GeoJsonLayer", data={"type": "FeatureCollection", "features": landmarks},
                pickable=True, stroked=True, filled=True, extruded=True, wireframe=True,         
                get_elevation="properties.building_height", get_fill_color="properties.fill_color", 
                get_line_color="[255, 255, 255, 255]", get_line_width=2, get_point_radius=12, auto_highlight=True 
            ))

    if user_lat and user_lon:
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=[{"position": [user_lon, user_lat], "name": "📍 YOU ARE HERE"}],
            get_position="position", get_fill_color="[255, 215, 0, 255]", get_radius=10, stroked=True, pickable=True
        ))

    if auto_status == "Active":
        layers.append(pdk.Layer(
            "ScatterplotLayer", data=[{"position": [curr_lon, curr_lat], "name": "🟢 ACTIVE RATH 01"}], 
            get_position="position", get_fill_color="[0, 255, 163, 255]", get_line_color="[255, 255, 255, 255]",
            get_radius=15, stroked=True, line_width_min_pixels=3, pickable=True 
        ))

    # --- RENDER MAP ---
    universal_tooltip = {
        "html": "<b>{name}</b>", 
        "style": {
            "backgroundColor": "rgba(14, 17, 23, 0.95)", "color": "#00FFA3",
            "fontFamily": "Courier New, monospace", "fontSize": "16px",
            "border": "1px solid #00C9FF", "borderRadius": "8px", "padding": "10px", "boxShadow": "0 0 15px rgba(0, 201, 255, 0.3)"
        }
    }

    # Sidebar map controls (Only visible in public mode!)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Engineers:** Suryansh, Shashank & Vineet")
    user_pitch = st.sidebar.slider("🎥 Camera Tilt (3D Mode)", min_value=0, max_value=85, value=55, step=5)
    st.sidebar.progress(85, text="Battery: 85%")
    st.sidebar.markdown("---")
    
    center_lat, center_lon = (user_lat, user_lon) if user_lat else (curr_lat, curr_lon)
    st.pydeck_chart(pdk.Deck(
        map_style=selected_map_style, 
        initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=16.5, pitch=user_pitch, bearing=0),
        layers=layers, tooltip=universal_tooltip 
    ))

    # Live Engine
    live_tracking = st.sidebar.toggle("🔴 ENABLE LIVE TRACKING", value=True)
    if st.sidebar.button("Force Manual Refresh"): st.rerun()
    if live_tracking:
        time.sleep(3)
        st.rerun()


# ==========================================
# ==========================================
# 4. PRIVATE VIEW: THE ADMIN TERMINAL
# ==========================================
# ==========================================
else:
    # --- ADMIN TERMINAL CSS ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
        
        .stApp {
            background: radial-gradient(circle at top, #1a202c, #000000);
            font-family: 'Inter', sans-serif; color: white;
        }
        .glass-card {
            background: rgba(15, 15, 25, 0.7); backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 255, 163, 0.3); border-radius: 20px;
            padding: 40px; text-align: center;
            box-shadow: 0 0 30px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(0, 255, 163, 0.1);
        }
        .neon-text {
            font-family: 'Orbitron', sans-serif; color: #00FFA3; text-align: center;
            text-shadow: 0 0 10px #00FFA3; margin-bottom: 20px;
        }
        div.stButton > button {
            background: transparent !important; border: 2px solid #00FFA3 !important;
            color: #00FFA3 !important; font-family: 'Orbitron', sans-serif;
            padding: 10px 24px !important; border-radius: 10px !important; width: 100%; transition: 0.3s;
        }
        div.stButton > button:hover { background: #00FFA3 !important; color: #000 !important; box-shadow: 0 0 15px #00FFA3; }
        </style>
    """, unsafe_allow_html=True)

    # We use columns to center the UI since the page layout is set to "wide" globally
    admin_col1, admin_col2, admin_col3 = st.columns([1, 2, 1])
    
    with admin_col2:
        # --- SCREEN 1: THE QUESTION ---
        if st.session_state.admin_screen == 'question':
            st.markdown("<h1 class='neon-text'>DRIVER TERMINAL</h1>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card"><h3>SYSTEM READY</h3><p>Start receiving requests?</p><br>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ GO ONLINE"): st.session_state.admin_screen = 'online'; st.rerun()
            with c2:
                if st.button("🛑 GO OFFLINE"): st.session_state.admin_screen = 'offline'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- SCREEN 2: LIVE BROADCAST ---
        elif st.session_state.admin_screen == 'online':
            st.markdown("<h1 class='neon-text'>🟢 LIVE BROADCAST</h1>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            
            loc = streamlit_geolocation()
            if loc and loc.get('latitude'):
                lat, lon = loc['latitude'], loc['longitude']
                st.success(f"📡 SIGNAL LOCKED: {lat:.5f}, {lon:.5f}")
                try:
                    requests.put(FIREBASE_URL, data=json.dumps({"latitude": lat, "longitude": lon, "status": "Active", "timestamp": time.time()}))
                    st.toast("Location synced to Server!")
                except: st.error("Server Error")
            else:
                st.info("Tap crosshair to lock GPS...")

            if st.button("🔚 END SHIFT"): st.session_state.admin_screen = 'question'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # --- SCREEN 3: OFFLINE STATUS ---
        elif st.session_state.admin_screen == 'offline':
            st.markdown("<h1 class='neon-text' style='color:#FF4B4B;'>🔴 OFFLINE</h1>", unsafe_allow_html=True)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            reason = st.selectbox("Reason:", ["Charging", "Lunch Break", "Shift Ended", "Out of Area"])
            if st.button("Confirm Status"):
                requests.put(FIREBASE_URL, data=json.dumps({"status": reason, "latitude": 0, "longitude": 0}))
                st.success("Students Notified!")
            if st.button("⬅️ BACK"): st.session_state.admin_screen = 'question'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- END OF UNIFIED FILE ---