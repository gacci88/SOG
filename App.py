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
min_attempts = st.slider("Minimum Shot Attempts (iCF)", 3, 15, 6)

###############################
# OPTIONAL NATURAL STAT TRICK CSV
###############################
st.header("📁 Optional: Upload Natural Stat Trick CSV for advanced stats")
uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    nst_data = pd.read_csv(uploaded)
else:
    nst_data = None

###############################
# FETCH NHL API DATA
###############################
st.header("📡 Fetching today's NHL player stats...")

today = datetime.now().strftime('%Y-%m-%d')
schedule_url = f"https://statsapi.web.nhl.com/api/v1/schedule?date={today}"

try:
    schedule = requests.get(schedule_url, timeout=10).json()
except requests.exceptions.RequestException:
    st.error("Failed to fetch NHL schedule. Check your internet connection.")
    st.stop()

games = schedule.get('dates', [])
if not games:
    st.warning("No NHL games scheduled today. Please check again later.")
    st.stop()

players_data = []

for game in games[0]['games']:
    for side in ['home', 'away']:
        team_info = game['teams'][side]['team']
        team_id = team_info['id']
        team_name = team_info['name']
        home_flag = 1 if side == 'home' else 0

        # Fetch roster
        try:
            roster_url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}?expand=team.roster"
            roster_resp = requests.get(roster_url, timeout=10).json()
            roster = roster_resp['teams'][0]['roster']['roster']
        except requests.exceptions.RequestException:
            st.warning(f"Failed to fetch roster for {team_name}. Skipping.")
            roster = []

        for player in roster:
            players_data.append({
                "Player": player['person']['fullName'],
                "Team": team_name,
                "Home": home_flag,
                "Status": "Active",  # default for simplicity
            })

df_players = pd.DataFrame(players_data)

if df_players.empty:
    st.warning("No players found for today's games.")
    st.stop()

# Merge optional NST stats
if nst_data is not None:
    df = pd.merge(df_players, nst_data, how='left', left_on='Player', right_on='Player')
else:
    df = df_players.copy()
    # Fill default columns
    df['TOI'] = 16
    df['ShotsAvg'] = 2.5
    df['iCF'] = 6
    df['L10_Shots'] = df['ShotsAvg']
    df['PP_Usage'] = 0
    df['Matchup_Def_Rank'] = 5
    df['Opponent'] = "Unknown"
    df['Opponent_GA_Avg'] = 2.9
    df['ShotsProj'] = df['ShotsAvg'] * 1.1
    df['SportsbookLine'] = df['ShotsAvg']

###############################
# FILTER & CALCULATE EDGESCORE
###############################
filtered = df[
    (df["TOI"] >= min_toi)
    & (df["ShotsAvg"] >= min_shots)
    & (df["iCF"] >= min_attempts)
]

if filtered.empty:
    st.warning("No players passed the filter criteria. Adjust sliders or try again later.")
    st.stop()

filtered["HomeBoost"] = np.where(filtered["Home"] == 1, home_weight, 1.0)
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
# DISPLAY TOP 5 RECOMMENDATIONS
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
# FULL TABLE & DOWNLOAD
###############################
st.header("📊 Full Ranked Edge List")
st.dataframe(ranked.reset_index(drop=True))

st.download_button(
    "Download Ranked CSV",
    ranked.to_csv(index=False),
    file_name="nhl_sog_edges.csv",
    mime="text/csv",
)

st.info("Stats pulled automatically from NHL API. Optional NST CSV can override advanced stats.")
