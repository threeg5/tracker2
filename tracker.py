import streamlit as st
import pandas as pd
import time
from nba_api.live.nba.endpoints import scoreboard

# --- PAGE CONFIG ---
st.set_page_config(page_title="The Rich Hits Tracker", layout="wide")
st.title("🏀 The Rich Hits: Live NBA Tracker")

# --- FUNCTIONS ---
def get_active_games():
    """Fetches active games for the dropdown."""
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        game_options = {}
        
        for game in games:
            # Status 2 = Live, 1 = Starting Soon, 3 = Final
            status = game['gameStatus']
            if status >= 1: 
                matchup = f"{game['awayTeam']['teamTricode']} @ {game['homeTeam']['teamTricode']}"
                game_options[matchup] = game['gameId']
        return game_options
    except:
        return {}

def get_game_data(game_id):
    """Fetches single snapshot of data."""
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        target = next((g for g in games if g['gameId'] == game_id), None)
        return target
    except:
        return None

# --- SIDEBAR SELECTION ---
st.sidebar.header("Game Menu")
active_games = get_active_games()

if not active_games:
    st.warning("No active games found right now.")
    selected_game_name = None
else:
    selected_game_name = st.sidebar.selectbox("Select a Game", list(active_games.keys()))
    selected_game_id = active_games[selected_game_name]

# --- MAIN DASHBOARD ---
# Initialize session state to store history (so graph doesn't erase on update)
if 'history' not in st.session_state:
    st.session_state.history = {'time': [], 'spread': [], 'home': [], 'away': []}

# Placeholders for live updates
header_metric = st.empty()
chart_col1, chart_col2 = st.columns(2)
spread_chart = chart_col1.empty()
score_chart = chart_col2.empty()

# --- LIVE LOOP ---
if selected_game_name:
    if st.button("Start Tracking (Stop with Stop Button)"):
        with st.empty():
            while True:
                data = get_game_data(selected_game_id)
                
                if data:
                    home_team = data['homeTeam']['teamTricode']
                    away_team = data['awayTeam']['teamTricode']
                    home_score = data['homeTeam']['score']
                    away_score = data['awayTeam']['score']
                    spread = home_score - away_score
                    status = data['gameStatusText']

                    # Update History
                    st.session_state.history['time'].append(len(st.session_state.history['time']))
                    st.session_state.history['spread'].append(spread)
                    st.session_state.history['home'].append(home_score)
                    st.session_state.history['away'].append(away_score)
                    
                    # Create DataFrames for Charts
                    df_spread = pd.DataFrame({
                        'Spread': st.session_state.history['spread']
                    })
                    
                    df_scores = pd.DataFrame({
                        home_team: st.session_state.history['home'],
                        away_team: st.session_state.history['away']
                    })

                    # Render Dashboard
                    header_metric.metric(
                        label=f"{away_team} vs {home_team} ({status})", 
                        value=f"Spread: {spread}",
                        delta=f"Home Lead: {spread}"
                    )
                    
                    # We use Streamlit's native charts (interactive!)
                    spread_chart.line_chart(df_spread)
                    score_chart.line_chart(df_scores)

                time.sleep(3) # Wait 3 seconds
