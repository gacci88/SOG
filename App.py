import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

###############################
# CONFIG
###############################
API_URL = "https://api-web.nhle.com/v1/"  # Public NHL stats API

###############################
# VISUAL STYLE A — Clean, white, card-based
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
st.write("Automated nightly SOG analysis — matchup edges, player statuses, trends, and projections.")

###############################
# CSV TEMPLATE GENERATOR
###############################
template_df = pd.DataFrame({
    "Player": [],
    "Team": [],
    "TOI": [],
    "ShotsAvg": [],
    "iCF": [],
    "L10_Shots": [],
    "PP_Usage": [],
    "Matchup_Def_Rank": [],
    "Home": [],
    "Status": [],  # Active, Injured, Scratched
    "Opponent": [],
    "Opponent_GA_Avg": [],
    "ShotsProj": [],
    "SportsbookLine": [],
})

st.download_button(
    "📄 Download CSV Template",
    template_df.to_csv(index=False),
    file_name="nhl_sog_template.csv",
    mime="text/csv",
)

###############################
# FILE UPLOAD
###############################
st.header("📁 Upload tonight's player data (CSV)")
uploaded = st.file_uploader("Upload CSV with player stats (shots, attempts, TOI, L10, etc.)")

###############################
# FILTERS — interactive sliders
###############################
st.header("🔎 Filters & Weight Controls")
home_weight = st.slider("Home Ice Advantage Weight", 1.0, 3.0, 2.0)
min_toi = st.slider("Minimum TOI (minutes)", 12, 25, 16)
min_shots = st.slider("Minimum Avg Shots", 1.0, 6.0, 2.5)
min_attempts = st.slider("Minimum Shot Attempts (iCF)", 3, 15, 6)

###############################
# PROCESSING
###############################
if uploaded:
    df = pd.read_csv(uploaded)

    # Auto-fill missing advanced fields
    required_cols = ["Opponent", "Opponent_GA_Avg", "ShotsProj", "SportsbookLine"]
    for col in required_cols:
        if col not in df.columns:
            if col == "Opponent_GA_Avg":
                df[col] = 2.9
            elif col == "ShotsProj":
                df[col] = df["ShotsAvg"] * 1.1
            elif col == "SportsbookLine":
                df[col] = round(df["ShotsAvg"], 1)
            else:
                df[col] = "Unknown"

    # Filter out inactive players
    df = df[df["Status"].str.lower() == "active"]

    # Basic filters
    filtered = df[
        (df["TOI"] >= min_toi)
        & (df["ShotsAvg"] >= min_shots)
        & (df["iCF"] >= min_attempts)
    ]

    # Add home-ice multiplier
    filtered["HomeBoost"] = np.where(filtered["Home"] == 1, home_weight, 1.0)

    # Calculate EdgeScore including goalie matchup and sportsbook edge
    filtered["GoalieMatchupScore"] = 1 / (filtered["Opponent_GA_Avg"] + 1) * 10
    filtered["SportsbookEdge"] = filtered["ShotsProj"] - filtered["SportsbookLine"]

    filtered["EdgeScore"] = (
        filtered["ShotsAvg"] * 0.35
        + filtered["iCF"] * 0.25
        + filtered["L10_Shots"] * 0.15
        + filtered["PP_Usage"] * 0.10
        + filtered["Matchup_Def_Rank"] * 0.15
    ) * filtered["HomeBoost"] + filtered["GoalieMatchupScore"] + filtered["SportsbookEdge"]

    ranked = filtered.sort_values("EdgeScore", ascending=False)

    ###############################
    # RECOMMENDED PLAYS
    ###############################
    st.header("🔥 Recommended SOG Plays (Top 5)")
    top5 = ranked.head(5)
    for _, row in top5.iterrows():
        st.metric(
            label=f"{row['Player']} — {row['Team']}",
            value=f"Edge Score: {row['EdgeScore']:.2f}",
            delta=f"L10 avg {row['L10_Shots']} shots",
        )

    ###############################
    # FULL TABLE
    ###############################
    st.header("📊 Full Ranked Edge List")
    st.dataframe(ranked.reset_index(drop=True))

    ###############################
    # DOWNLOAD OUTPUT
    ###############################
    st.download_button(
        "Download Ranked CSV",
        ranked.to_csv(index=False),
        file_name="nhl_sog_edges.csv",
        mime="text/csv",
    )

st.info("Upload your nightly CSV above to begin analysis. Only active players are considered.")
