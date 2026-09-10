import streamlit as st
import pandas as pd
from database import get_players, get_matches, get_settings, get_doubles_specials
from utils import apply_custom_theme, require_login, calculate_match_performance, get_avatar_svg, render_impressum_footer

st.set_page_config(page_title="Lions League - Spieler", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_login()

st.title("👤 Spielerprofil & Performance-Analyse")
st.caption("Einzelauswertung aller Lions-Darter inklusive Saison-Trendgrafik und Portraitfotos.")

players_df = get_players()
matches_df = get_matches()
settings = get_settings()
doubles_df = get_doubles_specials()

if players_df.empty:
    st.warning("⚠️ Noch keine Spieler registriert.")
    st.stop()

# Team-Filter (Nur offizielle Liga-Teams A-Team und B-Team)
selected_team = st.radio("Team wählen", ["Alle Teams", "A-Team", "B-Team"], horizontal=True)
if selected_team != "Alle Teams":
    filtered_players = players_df[players_df['team'] == selected_team]
else:
    filtered_players = players_df[players_df['team'].isin(['A-Team', 'B-Team'])]

p_names = sorted(filtered_players['name'].tolist())
selected_p_name = st.selectbox("Spieler auswählen", p_names)

player_info = players_df[players_df['name'] == selected_p_name].iloc[0]
p_id = int(player_info['id'])
p_team = player_info['team']

# Performance-Daten berechnen
if not matches_df.empty:
    matches_df['match_date_dt'] = pd.to_datetime(matches_df['match_date'])
    matches_df['match_date_str'] = matches_df['match_date_dt'].dt.strftime('%d.%m.%Y')
    
    calc_results = []
    for _, row in matches_df.iterrows():
        perf = calculate_match_performance(row.to_dict(), settings)
        calc_results.append({
            'Match_ID': row['id'],
            'player_id': row['player_id'],
            'Spieler': row['player_name'],
            'Team': row['team'],
            'Datum': row['match_date_str'],
            'Datum_DT': row['match_date_dt'],
            'Gegner': row['opponent'],
            'Rating': perf['total_rating'],
            'Gesamt Avg': row['avg_total'],
            '9D Avg': row['avg_9'],
            '18D Avg': row['avg_18'],
            'Legs_Won': row['legs_won'],
            'Legs_Lost': row['legs_lost'],
            'Is_Win': 1 if perf['win_ratio'] == 100 else 0,
            'Specials': perf['specials_count'],
            '180er': row['scores_180'],
            'High Finishes': row['high_finishes']
        })
    res_df = pd.DataFrame(calc_results)
else:
    res_df = pd.DataFrame()

p_matches = res_df[res_df['player_id'] == p_id].sort_values('Datum_DT') if not res_df.empty else pd.DataFrame()
p_doubles = doubles_df[doubles_df['player_name'] == selected_p_name] if not doubles_df.empty else pd.DataFrame()

d_bonus = len(p_doubles) * 0.5
avg_single_rating = p_matches['Rating'].mean() if not p_matches.empty else 0.0
total_pts = avg_single_rating + d_bonus

# STECKBRIEF HEADER
st.divider()
c_img, c_info = st.columns([1, 3])
with c_img:
    st.markdown(get_avatar_svg(selected_p_name, "#00D4FF", 140), unsafe_allow_html=True)
with c_info:
    team_badge = "🦁 A-Team (2. Kreisklasse Staffel 07)" if p_team == "A-Team" else "🐯 B-Team (2. Kreisklasse Staffel 11)"
    st.markdown(f"""
    <h2 style='color: #FFFFFF; margin-bottom: 4px; font-size: 32px;'>{selected_p_name}</h2>
    <h4 style='color: #00D4FF; margin-top: 0px; font-size: 22px;'>{team_badge}</h4>
    <p style='color: #CBD5E1; font-size: 19px;'>Eingetragener Darter beim SC Weyhausen von 1921 e.V.</p>
    """, unsafe_allow_html=True)

# KPI SPALTEN
st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Gesamt-Punkte", f"{total_pts:.2f} Pkt", delta=f"+{d_bonus:.1f} Doppel" if d_bonus > 0 else None)
with m2: st.metric("Gesamt-Average", f"{p_matches['Gesamt Avg'].mean():.1f}" if not p_matches.empty else "-")
with m3: st.metric("Einzel-Bilanz", f"{p_matches['Is_Win'].sum()} / {len(p_matches)}" if not p_matches.empty else "0 / 0")
with m4: st.metric("Höchstes Finish", f"{int(p_matches['High Finishes'].max())}" if (not p_matches.empty and p_matches['High Finishes'].max() > 0) else "-")
with m5: st.metric("Specials Gesamt", f"{int(p_matches['Specials'].sum() if not p_matches.empty else 0)} + {len(p_doubles)} Dbl")

# PERFORMANCE-ENTWICKLUNGSGRAFIK (TREND-CHART)
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📈 Performance-Entwicklung in der Saison")

if not p_matches.empty:
    chart_df = p_matches[['Datum', 'Rating', 'Gesamt Avg']].copy()
    chart_df = chart_df.set_index('Datum')
    
    st.markdown("##### Performance-Rating Entwicklung (Punkte je Match)")
    st.line_chart(chart_df[['Rating']], color="#00D4FF", height=280)
    
    st.markdown("##### Average-Trend (Gesamt Average je Spieltag)")
    st.line_chart(chart_df[['Gesamt Avg']], color="#60A5FA", height=280)
else:
    st.info("ℹ️ Für diesen Spieler liegen aktuell noch keine absolvierten Einzel-Matches vor.")

# MATCH-HISTORIE TABELLEN
if not p_matches.empty:
    st.markdown("#### 🎯 Einzel-Matches Historie")
    st.dataframe(
        p_matches[['Datum', 'Gegner', 'Is_Win', 'Legs_Won', 'Legs_Lost', 'Rating', 'Gesamt Avg', '9D Avg', '18D Avg', 'Specials']].rename(columns={
            'Is_Win': 'Sieg',
            'Legs_Won': 'Legs +',
            'Legs_Lost': 'Legs -',
            'Rating': 'Punkte'
        }).style.format({
            'Punkte': '{:.2f}',
            'Gesamt Avg': '{:.1f}',
            '9D Avg': '{:.1f}',
            '18D Avg': '{:.1f}'
        }),
        use_container_width=True,
        hide_index=True
    )

if not p_doubles.empty:
    st.markdown("#### 🤝 Im Doppel geworfene Specials (+0,5 Pkt Bonus)")
    st.dataframe(
        p_doubles[['match_date', 'special_type', 'partner_name', 'opponent_team', 'description']].rename(columns={
            'match_date': 'Datum',
            'special_type': 'Special Type',
            'partner_name': 'Teampartner',
            'opponent_team': 'Gegner Team',
            'description': 'Anmerkungen'
        }),
        use_container_width=True,
        hide_index=True
    )

render_impressum_footer()
