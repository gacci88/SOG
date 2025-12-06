import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import re

# ---- APP CONFIG ----
st.set_page_config(page_title="🏒 NHL SOG Edge Finder", layout="wide")
st.title("🏒 NHL SOG Edge Finder — Upload or Paste CSV/Excel")

st.markdown("""
Upload your **Natural Stat Trick player totals** file, or **paste CSV/tab-delimited data** from a table.  
The app calculates top SOG players for tonight.
""")

# ---- 1. DATA INPUT ----
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
st.markdown("Or paste CSV/tab-delimited data below:")
csv_text = st.text_area("Paste your table here")

df = None

# --- Read uploaded file if available ---
if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_type == "csv":
            for enc in ["utf-8", "latin1", "ISO-8859-1"]:
                try:
                    df = pd.read_csv(uploaded_file, encoding=enc)
                    break
                except Exception:
                    continue
            if df is None:
                st.error("Failed to read CSV. Try saving as CSV UTF-8.")
                st.stop()
        elif file_type in ["xls", "xlsx"]:
            try:
                df = pd.read_excel(uploaded_file)
            except ImportError:
                st.error("Missing 'openpyxl'. Add it to requirements.txt and redeploy.")
                st.stop()
            except Exception as e:
                st.error(f"Failed to read Excel file: {e}")
                st.stop()
        else:
            st.error("Unsupported file type")
            st.stop()
    except Exception as e:
        st.error(f"Error reading uploaded file: {e}")
        st.stop()

# --- Read pasted CSV/tab-delimited text if no uploaded file ---
elif csv_text.strip() != "":
    try:
        # Clean pasted text: remove empty lines and trailing spaces
        clean_lines = [line.strip() for line in csv_text.splitlines() if line.strip()]
        clean_text = "\n".join(clean_lines)

        # Replace multiple spaces or tabs with a single comma
        clean_text = re.sub(r"[ \t]+", ",", clean_text)

        # Read cleaned text into DataFrame
        df = pd.read_csv(StringIO(clean_text))

        if df.empty:
            st.error("Pasted data is empty or malformed.")
            st.stop()
    except Exception as e:
        st.error(f"Failed to read pasted data: {e}")
        st.stop()

# --- Stop if no data ---
if df is None:
    st.warning("Please upload a file or paste data to continue.")
    st.stop()

st.success("Data loaded successfully!")
st.write("Columns detected:", df.columns.tolist())

# ---- 2. CLEANUP & STANDARDIZE COLUMNS ----
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

# ---- 3. SOG METRICS WITH CLEANING ----
numeric_cols = ["shots", "toi", "ixg", "cf", "ff", "sf"]

# Keep only columns that exist in the DataFrame
existing_numeric_cols = [col for col in numeric_cols if col in df.columns]

for col in existing_numeric_cols:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce")

df[existing_numeric_cols] = df[existing_numeric_cols].fillna(0)

# Safe calculations using only existing columns
if "shots" in df.columns and "toi" in df.columns:
    df["shots_per60"] = df["shots"] / (df["toi"] / 60).replace(0, np.nan)
else:
    df["shots_per60"] = 0

if "ixg" in df.columns and "shots" in df.columns:
    df["ixg_per_shot"] = df["ixg"] / df["shots"].replace(0, np.nan)
else:
    df["ixg_per_shot"] = 0

if "cf" in df.columns and "toi" in df.columns:
    df["cf_per60"] = df["cf"] / (df["toi"] / 60).replace(0, np.nan)
else:
    df["cf_per60"] = 0

if "ff" in df.columns and "toi" in df.columns:
    df["ff_per60"] = df["ff"] / (df["toi"] / 60).replace(0, np.nan)
else:
    df["ff_per60"] = 0

df["aggressiveness_index"] = (
    df.get("shots_per60", 0) * 0.50 +
    df.get("ff_per60", 0) * 0.30 +
    df.get("cf_per60", 0) * 0.20
)

if "shots" in df.columns and "sf" in df.columns:
    df["individual_shot_share"] = df["shots"] / df["sf"].replace(0, np.nan)
else:
    df["individual_shot_share"] = 0

# ---- 4. FILTER CONTROLS ----
st.header("🔎 Filters")
min_gp = st.slider("Minimum Games Played", 1, 82, 10)
min_toi = st.slider("Minimum TOI (minutes)", 50, 1500, 150)
min_shots_per60 = st.slider("Minimum Shots per 60", 1.0, 20.0, 6.0)

filtered = df[
    (df.get("gp", 0) >= min_gp) &
    (df.get("toi", 0) >= min_toi) &
    (df.get("shots_per60", 0) >= min_shots_per60)
].sort_values("aggressiveness_index", ascending=False)

if filtered.empty:
    st.warning("No players passed the filters. Try lowering thresholds.")
    st.stop()

# ---- 5. DISPLAY RESULTS ----
st.header("🔥 Top SOG Players")
st.dataframe(filtered.head(20), use_container_width=True)

# ---- 6. DOWNLOAD FILTERED CSV ----
csv_output = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_output,
    file_name="top_sog_players.csv",
    mime="text/csv"
)
