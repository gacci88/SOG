import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

###############################
# CONFIG
###############################
st.set_page_config(page_title="NHL SOG Edge Finder", layout="wide")

st.markdown(
    """
    <style>
        body { background-color: #f8f9fa; }
        .main > div { padding: 20px; }
        .stMetric { background: white; border-radius: 16px; padding: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏒 NHL Shots-on-Goal (SOG) Edge Finder")
st.write("Automated nightly SOG analysis with optional advanced stats.")

###############################
# FILTERS — interactive sliders
###############################
st.header("🔎 Filters & Weight Controls")
home_weight = st.slider("Home Ice Advantage Weight", 1.0, 3.0, 2.0)
min_toi = st.slider("Minimum TOI (minutes)", 12, 25, 16)
min_shots = st.slider("Minimum Avg Shots", 1.0, 6.0, 2.5)
min_attempts = st.slider("Minimum Shot Attempts (iCF)", 3, 15,
