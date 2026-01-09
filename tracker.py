import streamlit as st
import pandas as pd
import time
from nba_api.live.nba.endpoints import scoreboard, playbyplay

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
    """Fetches single snapshot of score data."""
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        target = next((g for g in games if g['gameId'] == game_id), None)
        return target
    except:
        return None

def get_last_play_text(game_id):
    """Fetches the text description of the very last play."""
    try:
        pbp = playbyplay.PlayByPlay(game_id)
        actions = pbp.get_dict()['game']['actions']
        if actions:
            last_action = actions[-1]
            # NBA APIs sometimes split text into 'descriptionHome' or 'descriptionAway'
            # We want whichever one has text.
            desc = last_action.get('description', '')
            if not desc:
                # Try specific home/away fields if main desc is empty
                desc = last_action.get('descriptionHome') or last_action.get('descriptionAway') or "Play in progress..."
            
            # Add the clock time if available
            clock = last_action.get('clock', '')
            period = last_action.get('period', '')
            return f"(Q{period} {clock}) {desc}"
        return "Waiting for tip-off..."
    except:
        return "Loading play data..."

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

# LAYOUT UPDATE: Two Main Columns (Left for Stats, Right for Last Play)
# The ratio [3, 1] means the stats take up 75% of the width, Last Play takes 25%
main_col_left, main_col_right = st.columns([3, 1])

with main_col_left:
    # Inside the left column, we nest our 3 stat columns
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    # 1. Current Spread
    metric_current = stat_col1.empty()
    
    # 2. Highest Spread + Visiting Score
    with stat_col2:
        metric_high = st.empty()
        metric_visit_score = st.empty()

    # 3. Lowest Spread + Home Score
    with stat_col3:
        metric_low = st.empty()
        metric_home_score = st.empty()

with main_col_right:
    # This is the new "Last Play" Box on the right
    st.markdown("### ⚡ Last Play")
    last_play_box = st.empty()

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
                # 1. Get Scoreboard Data
                data = get_game_data(selected_game_id)
                
                # 2. Get Last Play Data (New!)
                play_text = get_last_play_text(selected_game_id)
                
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

                    # --- RENDER STATS (LEFT) ---
                    metric_current.metric(
                        label=f"Current ({home_team} vs {away_team})", 
                        value=spread,
                        delta=f"Status: {status}"
                    )
                    
                    metric_high.metric(
                        label=f"High Spread ({home_team} Lead)",
                        value=current_high
                    )
                    metric_visit_score.metric(
                        label=f"{away_team} Score",
                        value=away_score
                    )
                    
                    metric_low.metric(
                        label=f"Low Spread ({away_team} Lead)",
                        value=current_low
                    )
                    metric_home_score.metric(
                        label=f"{home_team} Score",
                        value=home_score
                    )

                    # --- RENDER LAST PLAY (RIGHT) ---
                    # We use a styled info box to make it pop
                    last_play_box.info(f"{play_text}")

                    # --- RENDER CHARTS ---
                    spread_chart.line_chart(df_spread)
                    score_chart.line_chart(df_scores)

                time.sleep(3)
