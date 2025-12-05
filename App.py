import streamlit as st
import pandas as pd
import numpy as np

# ---- APP CONFIG ----
st.set_page_config(page_title="NHL SOG Edge Finder", layout="wide")
st.title("🏒 NHL SOG Edge Finder — Upload CSV")

st.markdown("""
Upload your **Natural Stat Trick CSV** (Player Season Totals).  
The app will calculate top SOG players for tonight.
""")

# ---- 1. FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Please upload a CSV file to continue.")
    st.stop()

# ---- 2. READ CSV WITH ENCODING FIX ----
try:
    df = pd.read_csv(uploaded_file, encoding='latin1')
except UnicodeDecodeError:
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')

st.success("CSV loaded successfully!")

# ---- 3. CLEANUP & COLUMN STANDARDIZATION ----
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

rename_map = {
    "player": "player",
    "team": "team",
    "position": "pos",
    "gp": "gp",
    "toi": "toi",
    "cf": "cf",
    "ca": "ca",
    "ff": "ff",
    "fa": "fa",
    "sf": "sf",
    "sa": "sa",
    "g": "g",
    "ixg": "ixg",
    "shots": "shots"
}

df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

# ---- 4. SOG OPTIMIZATION METRICS ----
df["shots_per60"] = df["shots"] / (df["toi"] / 60)
df["ixg_per_shot"] = df["ixg"] / df["shots"].replace(0, pd.NA)
df["cf_per60"] = df["cf"] / (df["toi"] / 60)
df["ff_per60"] = df["ff"] / (df["toi"] / 60)
df["aggressiveness_index"] = (
    df["shots_per60"] * 0.50 +
    df["ff_per60"] * 0.30 +
    df["cf_per60"] * 0.20
)
df["individual_shot_share"] = df["shots"] / df["sf"]

# ---- 5. FILTER PLAYERS ----
min_gp = st.slider("Minimum Games Played", 1, 82, 10)
min_toi = st.slider("Minimum TOI (minutes)", 50, 1500, 150)
min_shots_per60 = st.slider("Minimum Shots per 60", 1.0, 20.0, 6.0)

filtered = df[
    (df["gp"] >= min_gp) &
    (df["toi"] >= min_toi) &
    (df["shots_per60"] >= min_shots_per60)
].sort_values("aggressiveness_index", ascending=False)

# ---- 6. DISPLAY RESULTS ----
st.header("🔥 Top SOG Players")
st.dataframe(filtered.head(20), use_container_width=True)

# ---- 7. DOWNLOAD BUTTON ----
csv_output = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_output,
    file_name="top_sog_players.csv",
    mime="text/csv"
)
