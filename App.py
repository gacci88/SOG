import pandas as pd
from io import StringIO, BytesIO

# ---- 1. FILE UPLOAD ----
# This will prompt you to upload: 
# "Player Season Totals - Natural Stat Trick.csv"
from google.colab import files  # If not in Colab, remove this line
uploaded = files.upload()

filename = list(uploaded.keys())[0]
df = pd.read_csv(BytesIO(uploaded[filename]))

# ---- 2. BASIC CLEANUP ----
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

# Natural Stat Trick often uses weird symbols & spaces
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

# Shots per 60
df["shots_per60"] = df["shots"] / (df["toi"] / 60)

# Individual expected goals per shot (finishing quality)
df["ixg_per_shot"] = df["ixg"] / df["shots"].replace(0, pd.NA)

# Corsi contribution rate
df["cf_per60"] = df["cf"] / (df["toi"] / 60)

# Fenwick contribution rate
df["ff_per60"] = df["ff"] / (df["toi"] / 60)

# Shooting aggressiveness index (custom metric)
df["aggressiveness_index"] = (
    df["shots_per60"] * 0.50 +
    df["ff_per60"] * 0.30 +
    df["cf_per60"] * 0.20
)

# Usage indicator
df["individual_shot_share"] = df["shots"] / df["sf"]

# ---- 4. FILTER FOR REAL SOG PROP TARGETS ----
filtered = df[
    (df["gp"] >= 10) &
    (df["toi"] >= 150) &
    (df["shots_per60"] >= 6.0)
].sort_values("aggressiveness_index", ascending=False)

filtered.head(20)
