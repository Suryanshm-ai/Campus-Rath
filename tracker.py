import streamlit as st
import pydeck as pdk
from streamlit_geolocation import streamlit_geolocation
import requests
import time
import json
import os

# ==========================================
# 1. PAGE CONFIG & CSS
# ==========================================
st.set_page_config(page_title="Campus Rath | Live Tracker", layout="wide")

FIREBASE_URL = "https://campusrath-default-rtdb.firebaseio.com/rath_01.json"
GEOJSON_ROUTE_PATH = "newcampusmap.geojson"

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

# ==========================================
# 2. DASHBOARD METRICS
# ==========================================
st.write("")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Active Rath", "01", "⚡ Online")
m_col2.metric("Wait Time", "2.5 min", "📉 Efficient")
m_col3.metric("Campus Route", "7.0 km", "📍 Mapped")
m_col4.metric("System Mode", "Hybrid 3D", "🚀 Optimized")

# ==========================================
# 3. FETCH FIREBASE DATA
# ==========================================
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
except:
    pass 

# ==========================================
# 4. UI & GEOLOCATION
# ==========================================
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

# ==========================================
# 5. BULLETPROOF 3D PARSER & TOOLTIPS
# ==========================================
layers = []

name_to_emoji = {
    "Main Gate": "⛩️", "Campus GYM": "🏋️", "Badminton Court": "🏸", "Multipurpose Block": "🏫",
    "Administrative Block": "💼", "Police Chowki": "🚓", "Boys Hostel": "🛌", "Water Tank": "💧",
    "Pariksha Bhawan": "📝", "Polly House": "🌱", "Block-A": "🅰️", "Block-B": "🅱️",
    "Block-C": "🅲️", "Block": "🏢", "Vice Chancellor Block": "🎓"
}

def hex_to_rgb(hex_color):
    hex_color = str(hex_color).lstrip('#')
    if len(hex_color) == 6:
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)] + [200]
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
            
            # Extract the custom height (Defaults to 40m for 3D extrusion)
            custom_height = props.get("height") or props.get("Height") or props.get("elevation") or 40
            
            emoji_icon = "📍" 
            for dict_name, emoji in name_to_emoji.items():
                if dict_name.lower() in name.lower():
                    emoji_icon = emoji
                    break
            
            # Save exact name, color, and height into the properties so PyDeck can read them
            feature["properties"]["name"] = f"{emoji_icon} {name}"
            feature["properties"]["fill_color"] = hex_to_rgb(color_hex)
            feature["properties"]["building_height"] = float(custom_height)
            
            landmarks.append(feature)

    # LAYER 1: NEON PATH (The glowing 7km line)
    if paths:
        layers.append(pdk.Layer(
            "GeoJsonLayer",
            data={"type": "FeatureCollection", "features": paths},
            stroked=True, filled=False,
            get_line_color="[0, 201, 255, 255]", get_line_width=8, opacity=0.8,
            pickable=False 
        ))

    # LAYER 2: 3D LANDMARKS (Polygons Extrude based on Height!)
    if landmarks:
        layers.append(pdk.Layer(
            "GeoJsonLayer",
            data={"type": "FeatureCollection", "features": landmarks},
            pickable=True, 
            stroked=True,
            filled=True,
            extruded=True,          
            wireframe=True,         
            get_elevation="properties.building_height", # Pulls the custom height!
            get_fill_color="properties.fill_color", 
            get_line_color="[255, 255, 255, 255]",
            get_line_width=2,
            get_point_radius=12, 
            auto_highlight=True 
        ))

# LAYER 3: USER LOCATION 
if user_lat and user_lon:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [user_lon, user_lat], "name": "📍 YOU ARE HERE"}],
        get_position="position", get_fill_color="[255, 215, 0, 255]", get_radius=10, stroked=True, pickable=True
    ))

# LAYER 4: ACTIVE AUTO RATH 
if auto_status == "Active":
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=[{"position": [curr_lon, curr_lat], "name": "🟢 ACTIVE RATH 01"}], 
        get_position="position", get_fill_color="[0, 255, 163, 255]", get_line_color="[255, 255, 255, 255]",
        get_radius=15, stroked=True, line_width_min_pixels=3, pickable=True 
    ))

# ==========================================
# 6. RENDER THE MAP
# ==========================================

# THIS IS THE FIXED TOOLTIP. Every layer now understands {properties.name}
universal_tooltip = {
    "html": "<b>{name}</b>", 
    "style": {
        "backgroundColor": "rgba(14, 17, 23, 0.95)", 
        "color": "#00FFA3",
        "fontFamily": "Courier New, monospace", 
        "fontSize": "16px",
        "border": "1px solid #00C9FF",
        "borderRadius": "8px", 
        "padding": "10px", 
        "boxShadow": "0 0 15px rgba(0, 201, 255, 0.3)"
    }
}


# SIDEBAR SLIDER FOR 3D CAMERA
st.sidebar.title("⚙️ Rath Control Center")
st.sidebar.markdown(f"**Engineers:** Suryansh, Shashank & Vineet")
user_pitch = st.sidebar.slider("🎥 Camera Tilt (3D Mode)", min_value=0, max_value=85, value=55, step=5)
st.sidebar.progress(85, text="Battery: 85%")
st.sidebar.markdown("---")

center_lat, center_lon = (user_lat, user_lon) if user_lat else (curr_lat, curr_lon)

st.pydeck_chart(pdk.Deck(
    map_style=selected_map_style, 
    initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=16.5, pitch=user_pitch, bearing=0),
    layers=layers,
    tooltip=universal_tooltip 
))

# ==========================================
# 7. LIVE ENGINE REFRESH
# ==========================================
live_tracking = st.sidebar.toggle("🔴 ENABLE LIVE TRACKING", value=True)

if st.sidebar.button("Force Manual Refresh"):
    st.rerun()

if live_tracking:
    time.sleep(3)
    st.rerun()

# --- END OF FILE ---