import streamlit as st
import pandas as pd

st.set_page_config(page_title="NHL Advanced Stats App", layout="wide")

st.title("🏒 NHL Advanced Stats Explorer (Upload Your CSV)")

st.markdown("""
Upload any NHL skater stats CSV (MoneyPuck, NST, custom files, etc.).
""")

##############################################
# 1. CSV UPLOADER
##############################################

uploaded_file = st.file_uploader("Upload your advanced stats CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Please upload a CSV to continue.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
    st.success("CSV loaded successfully!")
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

##############################################
# 2. FILTER SIDEBAR
##############################################

# Clean column names to avoid errors
df.columns = [c.strip() for c in df.columns]

# Detect team and player columns automatically
team_col = None
player_col = None

possible_team_cols = ["team", "Team", "TEAM", "homeTeam", "awayTeam"]
possible_player_cols = ["name", "player", "Player", "skater", "Name"]

for col in df.columns:
    if col in possible_team_cols:
        team_col = col
    if col in possible_player_cols:
        player_col = col

# Sidebar Filters
if team_col:
    teams = ["All Teams"] + sorted(df[team_col].dropna().unique())
    team_choice = st.sidebar.selectbox("Select a Team", teams)

    if team_choice != "All Teams":
        df = df[df[team_col] == team_choice]

if player_col:
    players = ["All Players"] + sorted(df[player_col].dropna().unique())
    player_choice = st.sidebar.selectbox("Select a Player", players)

    if player_choice != "All Players":
        df = df[df[player_col] == player_choice]

##############################################
# 3. DISPLAY TABLE
##############################################

st.subheader("📊 Filtered Dataset")
st.dataframe(df, use_container_width=True)

##############################################
# 4. CSV DOWNLOAD BUTTON
##############################################

csv_output = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered CSV",
    data=csv_output,
    file_name="filtered_stats.csv",
    mime="text/csv"
)
