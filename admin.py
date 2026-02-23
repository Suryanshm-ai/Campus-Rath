import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import time

st.set_page_config(page_title="Rath Admin | Driver Terminal")

# Glassmorphism Styling for Admin
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .driver-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #00C9FF;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛺 Driver Control Center")
st.write("Project: **Campus Rath**")

with st.container():
    st.markdown('<div class="driver-card">', unsafe_allow_html=True)
    st.subheader("Shift Status: 🟢 ACTIVE")
    
    # 1. Capture Driver's Live GPS
    location = streamlit_geolocation()
    
    if location and location.get('latitude'):
        lat = location['latitude']
        lon = location['longitude']
        
        st.success(f"Broadcasting Live: {lat:.4f}, {lon:.4f}")
        
        # NOTE: We will add the Firebase "Push" code here in the next step
        # so the Passenger App can see these numbers.
    else:
        st.warning("Please click the 'Location' button to start broadcasting.")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.info("Keep this page open. Your location is being shared with students in real-time.")
