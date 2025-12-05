import streamlit as st
import pandas as pd

st.set_page_config(page_title="NHL SOG Edge Finder", layout="wide")

st.title("🏒 NHL SOG Edge Finder — Upload Your CSV")

st.markdown("Upload your Natural Stat Trick CSV: Player Season Totals.")

# ---- 1. FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Please upload the CSV file to continue.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

# ---- 2. BASIC CLEANUP ----
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

# ---- 3. BUILD SOG-OPTIMIZED FEATURES ----
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

# ---- 4. FILTER PLAYERS ----
filtered = df[
    (df["gp"] >= 10) &
    (df["toi"] >= 150) &
    (df["shots_per60"] >= 6.0)
].sort_values("aggressiveness_index", ascending=False)

# ---- 5. DISPLAY RESULTS ----
st.header("🔥 Top SOG Players")
st.dataframe(filtered.head(20), use_container_width=True)

# ---- 6. DOWNLOAD BUTTON ----
csv_output = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_output,
    file_name="top_sog_players.csv",
    mime="text/csv"
)
