import streamlit as st
import pandas as pd
from database import get_players, get_matches, get_settings, get_doubles_specials
from utils import apply_custom_theme, require_login, calculate_match_performance, get_avatar_svg, render_impressum_footer

st.set_page_config(page_title="Lions League - Teams", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_login()

st.title("🦁 Team-Kader & Mannschaftsübersicht")
st.caption("Unsere Mannschaftsaufstellung im SC Weyhausen von 1921 e.V.")

players_df = get_players()
matches_df = get_matches()
settings = get_settings()
doubles_df = get_doubles_specials()

if not matches_df.empty:
    results = []
    for _, row in matches_df.iterrows():
        perf = calculate_match_performance(row.to_dict(), settings)
        results.append({
            'player_id': row['player_id'],
            'Rating': perf['total_rating'],
            'avg_total': row['avg_total'],
            'legs_won': row['legs_won'],
            'legs_lost': row['legs_lost'],
            'is_win': 1 if perf['win_ratio'] == 100 else 0
        })
    perf_df = pd.DataFrame(results)
else:
    perf_df = pd.DataFrame()

doubles_bonus_map = {}
if not doubles_df.empty:
    for p_name, group in doubles_df.groupby('player_name'):
        doubles_bonus_map[p_name] = len(group) * 0.5

tab_a, tab_b = st.tabs(["🦁 A-Team (2. Kreisklasse Staffel 07)", "🐯 B-Team (2. Kreisklasse Staffel 11)"])

def render_team_grid(team_name, accent_color):
    team_players = players_df[players_df['team'] == team_name] if not players_df.empty else pd.DataFrame()
    if team_players.empty:
        st.info(f"Noch keine Spieler für {team_name} zugewiesen.")
        return
        
    cols = st.columns(3)
    for idx, (_, p_row) in enumerate(team_players.iterrows()):
        col = cols[idx % 3]
        p_name = p_row['name']
        p_id = p_row['id']
        
        if not perf_df.empty:
            p_m = perf_df[perf_df['player_id'] == p_id]
            matches_count = len(p_m)
            single_rating = p_m['Rating'].mean() if matches_count > 0 else 0.0
            total_rating = single_rating + doubles_bonus_map.get(p_name, 0.0)
            avg_tot = p_m['avg_total'].mean() if matches_count > 0 else 0.0
            wins = p_m['is_win'].sum()
        else:
            matches_count = 0
            total_rating = 0.0
            avg_tot = 0.0
            wins = 0
            
        av_html = get_avatar_svg(p_name, accent_color, 80)
        
        with col:
            st.markdown(f"""
            <div class="mockup-card" style="text-align: center; padding: 18px; margin-bottom: 16px;">
                {av_html}
                <h3 style="margin: 10px 0 2px 0; color: #FFFFFF; font-size: 22px;">{p_name}</h3>
                <div style="font-size: 15px; color: {accent_color}; font-weight: 700;">{team_name}</div>
                <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 12px 0;">
                <div style="display: flex; justify-content: space-around; font-size: 16px;">
                    <div>
                        <div style="color: #94A3B8; font-size: 13px;">Spiele</div>
                        <div style="font-weight: 800; font-size: 18px;">{matches_count}</div>
                    </div>
                    <div>
                        <div style="color: #94A3B8; font-size: 13px;">Punkte</div>
                        <div style="font-weight: 900; color: #00D4FF; font-size: 18px;">{total_rating:.2f}</div>
                    </div>
                    <div>
                        <div style="color: #94A3B8; font-size: 13px;">Avg.</div>
                        <div style="font-weight: 800; font-size: 18px;">{avg_tot:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab_a:
    render_team_grid("A-Team", "#00D4FF")

with tab_b:
    render_team_grid("B-Team", "#3B82F6")

render_impressum_footer()
