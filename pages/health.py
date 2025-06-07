import streamlit as st
import datetime
from utils.logger import app_logger as logger

# Simple health check page that returns HTTP 200
st.set_page_config(page_title="Health Check")

# Return a simple JSON response
st.json({
    "status": "healthy",
    "timestamp": str(datetime.datetime.now()),
    "service": "regnum-front"
})

# Hide the page from the sidebar
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul li:has(div[aria-label*="health.py"]) {
    display: none;
}
</style>
""", unsafe_allow_html=True) 