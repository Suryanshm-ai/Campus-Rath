import streamlit as st
import pydeck as pdk
from streamlit_geolocation import streamlit_geolocation
import base64
import os
import json

# 1. PAGE CONFIG
st.set_page_config(page_title="Campus Rath | Suryansh", layout="wide")

# 2. FILE PATHS (CLOUD READY)
video_path = "campusrathvideo.mp4"
img_path = "ev_icon.png.png"
geojson_path = "campus_data.geojson"

def get_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

v_64 = get_base64(video_path)
i_64 = get_base64(img_path)

# 3. ADVANCED CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    
    #bg-video {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: -1; object-fit: cover; filter: brightness(0.3);
    }}

    .welcome-banner {{
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 40px;
        border: 1px solid rgba(144, 144, 144, 0.1);
        text-align: center;
        margin-top: 15px;
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.17);
    }}

    .project-title {{
        font-family: 'Orbitron', sans-serif;
        color: #FFFFFF;
        font-size: 3.5rem;
        letter-spacing: 5px;
        text-shadow: 0 0 20px rgba(0, 201, 255, 0.5);
    }}

    .rath-quote {{
        color: #00FFA3;
        font-size: 1.3rem;
        font-style: italic;
        margin-top: 10px;
    }}

    .stButton>button {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 15px !important;
        padding: 20px 40px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        transition: all 0.4s ease !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}

    .stButton>button:hover {{
        background: rgba(0, 201, 255, 0.2) !important;
        border: 1px solid #00C9FF !important;
        box-shadow: 0 0 20px rgba(0, 201, 255, 0.4) !important;
        transform: translateY(-3px);
    }}
    </style>

    <video id="bg-video" autoplay loop muted playsinline>
        <source src="data:video/mp4;base64,{v_64}" type="video/mp4">
    </video>

    <div class="welcome-banner">
        <h1 class="project-title">CAMPUS RATH</h1>
        <p style="color: #00C9FF; font-weight: 400; letter-spacing: 2px;">DEVELOPED BY SURYANSH, SHASHANK & VINEET | AI & DATA SCIENCE ENGINEERS</p>
        <p class="rath-quote">"Precision in Mobility, Intelligence in Every Mile."</p>
    </div>
    """, unsafe_allow_html=True)

# 4. DASHBOARD METRICS
st.write("")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Active Rath", "01", "⚡ Online")
m_col2.metric("Wait Time", "2.5 min", "📉 Efficient")
m_col3.metric("Campus Coverage", "1.5 km", "📍 Prayagraj")
m_col4.metric("Green Energy", "100%", "🌱 EV Only")

# 5. GEOLOCATION
st.write("---")

col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 2, 1])
with col_btn_2:
    st.write("###")
    location = streamlit_geolocation()

default_lat, default_lon = 25.4358, 81.8463

if location and location.get('latitude'):
    curr_lat = location['latitude']
    curr_lon = location['longitude']
    st.success(f"Satellite Link Established: {curr_lat:.4f}, {curr_lon:.4f}")
else:
    curr_lat, curr_lon = default_lat, default_lon
    st.info("🛰️ Connecting to Orbital GPS... (Click the 'Location' button above)")

# --- NEW: MOBILE CAMERA CONTROLS ---
st.subheader("🌐 Real-Time 3D Tracking")
cam_col1, cam_col2 = st.columns(2)
with cam_col1:
    # Allows mobile users to spin the map 360 degrees
    user_bearing = st.slider("Map Rotation (Spin)", min_value=0, max_value=360, value=180, step=5)
with cam_col2:
    # Allows mobile users to switch between Top-Down (0) and 3D Angled (60-85)
    user_pitch = st.slider("Camera Angle (3D Tilt)", min_value=0, max_value=85, value=60, step=5)

# 6. RENDER THE 3D MAP
view_state = pdk.ViewState(
    latitude=curr_lat,
    longitude=curr_lon,
    zoom=16,
    pitch=user_pitch,   # Controlled by user slider
    bearing=user_bearing # Controlled by user slider
)

layers = []
label_data = [] 

if os.path.exists(geojson_path):
    with open(geojson_path, "r") as f:
        campus_geojson = json.load(f)
        
    for feature in campus_geojson.get('features', []):
        props = feature.get('properties', {})
        if 'name' in props:
            geom_type = feature['geometry']['type']
            coords = feature['geometry']['coordinates']
            
            if geom_type == 'Polygon':
                text_pos = coords[0][0] 
            elif geom_type == 'LineString':
                text_pos = coords[0] 
            else:
                text_pos = coords
                
            label_data.append({"name": props['name'], "pos": text_pos})
            
    campus_layer = pdk.Layer(
        "GeoJsonLayer",
        data=campus_geojson,
        opacity=0.9, 
        stroked=True,
        filled=True,
        extruded=True,  
        wireframe=True,
        pickable=False, # FIX: Turned off to prevent the JSON nesting bug
        get_elevation=25,  
        get_fill_color="[220, 225, 230, 255]", 
        get_line_color="[150, 150, 150, 255]", 
    )
    layers.append(campus_layer)

    if label_data:
        text_layer = pdk.Layer(
            "TextLayer",
            data=label_data,
            get_position="pos",
            get_text="name",
            get_size=18,
            get_color="[255, 255, 255, 255]", 
            get_alignment_baseline="'bottom'", 
            get_text_anchor="'middle'",
            pickable=True # FIX: Made the text pickable instead!
        )
        layers.append(text_layer)

# The Glowing Auto Marker
car_layer = pdk.Layer(
    "ScatterplotLayer",
    data=[{"lat": curr_lat, "lon": curr_lon, "name": "Active Rath #01"}], # Flat dictionary, no nesting
    get_position="[lon, lat]",
    get_fill_color="[0, 255, 163, 255]", 
    get_line_color="[255, 255, 255, 255]",
    get_radius=15, 
    stroked=True,
    line_width_min_pixels=3,
    pickable=True # FIX: Car is pickable
)
layers.append(car_layer)

# Render the 3D Map
st.pydeck_chart(pdk.Deck(
    map_style="dark", 
    initial_view_state=view_state,
    layers=layers,
    # FIX: Reverted back to the simple {name} tag
    tooltip={
        "html": "<b style='color: white;'>{name}</b>", 
        "style": {"backgroundColor": "#0E1117", "border": "1px solid #00C9FF", "padding": "10px", "borderRadius": "10px"}
    } 
))

# 7. SIDEBAR STATUS
st.sidebar.title("Rath Control Center")
st.sidebar.markdown(f"**Engineers:** Suryansh, Shashank & Vineet")
st.sidebar.markdown("**Project:** Campus Rath")
st.sidebar.progress(85, text="Battery: 85%")
if st.sidebar.button("Simulate Auto Movement"):

    st.sidebar.warning("Initializing Pathing Algorithm...")
