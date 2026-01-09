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

# --- MAIN DASHBOARD LAYOUT ---
if 'history' not in st.session_state:
    st.session_state.history = {'time': [], 'spread': [], 'home': [], 'away': []}

# Create 3 Columns for the Top Metrics
col1, col2, col3 = st.columns(3)

# Column 1: Current Spread (Single Stat)
metric_current = col1.empty()

# Column 2: Highest Spread (Top) + Visiting Score (Bottom)
with col2:
    metric_high = st.empty()
    metric_visit_score = st.empty() # Placeholder for Visiting Team Score

# Column 3: Lowest Spread (Top) + Home Score (Bottom)
with col3:
    metric_low = st.empty()
    metric_home_score = st.empty() # Placeholder for Home Team Score

st.divider()

# Charts below
st.subheader("Live Spread History")
spread_chart = st.empty()

st.subheader("Score Pace")
score_chart = st.empty()

# --- LIVE LOOP ---
if selected_game_name:
    if st.button("Start Tracking"):
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
                    
                    # Calculate Stats
                    current_high = max(st.session_state.history['spread'])
                    current_low = min(st.session_state.history['spread'])

                    # DataFrames for Charts
                    df_spread = pd.DataFrame({'Spread': st.session_state.history['spread']})
                    df_scores = pd.DataFrame({
                        home_team: st.session_state.history['home'],
                        away_team: st.session_state.history['away']
                    })

                    # --- RENDER TOP METRICS ---
                    
                    # 1. Current Spread
                    metric_current.metric(
                        label=f"Current Spread ({home_team} vs {away_team})", 
                        value=spread,
                        delta=f"Status: {status}"
                    )
                    
                    # 2. Highest Spread + Visiting Score
                    metric_high.metric(
                        label=f"Highest Spread (Max {home_team} Lead)",
                        value=current_high
                    )
                    metric_visit_score.metric(
                        label=f"Visiting Score ({away_team})",
                        value=away_score
                    )
                    
                    # 3. Lowest Spread + Home Score
                    metric_low.metric(
                        label=f"Lowest Spread (Max {away_team} Lead)",
                        value=current_low
                    )
                    metric_home_score.metric(
                        label=f"Home Score ({home_team})",
                        value=home_score
                    )

                    # --- RENDER CHARTS ---
                    spread_chart.line_chart(df_spread)
                    score_chart.line_chart(df_scores)

                time.sleep(3)
