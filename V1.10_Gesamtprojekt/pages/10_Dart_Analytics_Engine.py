import textwrap
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils import apply_custom_theme, require_login, render_impressum_footer, get_avatar_svg, get_short_name
from database import get_players, get_available_seasons
from analytics.config import get_sample_size_rating
from analytics.data_access import get_player_leg_visits, get_all_analytics_matches, get_analytics_match_details
from analytics.basic_metrics import (
    calculate_visit_statistics, calculate_first_n_averages,
    calculate_score_distribution, calculate_darts_per_leg
)
from analytics.phase_engine import (
    analyze_start_performance, calculate_performance_curve,
    calculate_leg_phases, calculate_skill_radar_metrics
)
from analytics.ai_scouting import (
    generate_ai_player_profile, generate_ai_h2h_scouting
)

st.set_page_config(
    page_title="Lions League - DAE (Dart Analytics Engine)",
    page_icon="assets/logo.png",
    layout="wide"
)

apply_custom_theme()
require_login()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.markdown("""
<div style="background: rgba(8, 20, 48, 0.85); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 16px; padding: 14px 24px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,212,255,0.15);">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="color: #FFFFFF; font-size: 26px; font-weight: 800; margin: 0; text-shadow: 0 0 10px rgba(0,212,255,0.5);">
                🎯 DART ANALYTICS ENGINE (DAE)
            </h1>
            <p style="color: #00D4FF; font-size: 14px; margin: 2px 0 0 0; font-weight: 600;">
                Deterministische Steel-Dart Leistungsdiagnostik • Einzelanalyse & Head-to-Head Spieler-Vergleich
            </p>
        </div>
        <div style="background: rgba(0,212,255,0.1); border: 1px solid #00D4FF; border-radius: 8px; padding: 6px 14px; color: #00D4FF; font-weight: 700; font-size: 13px;">
            📊 PERFORMANCE ANALYTICS
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

players_df = get_players()
if not players_df.empty:
    players_df = players_df[players_df['team'].isin(['A-Team', 'B-Team'])].copy()
available_seasons = get_available_seasons()

if players_df.empty:
    st.warning("Keine Spieler in der Datenbank registriert.")
    st.stop()

player_options = sorted(players_df['name'].tolist())

def render_html(html_str: str):
    """Rendert sauberes HTML ohne Markdown-Einrueckungs-Fehler (Code-Block-Vermeidung)."""
    clean_lines = [line.strip() for line in html_str.split('\n') if line.strip()]
    st.markdown(''.join(clean_lines), unsafe_allow_html=True)

def compute_player_analytics(player_id: int, player_name: str, legs_visits: list) -> dict:
    """Berechnet alle DAE-Metriken konsistent für einen Spieler."""
    all_scores = [v['score'] for leg in legs_visits for v in leg]
    legs_plain_scores = [[v['score'] for v in leg] for leg in legs_visits]
    
    visit_stats = calculate_visit_statistics(all_scores)
    first_n = calculate_first_n_averages(legs_plain_scores)
    dist_data = calculate_score_distribution(all_scores)
    
    won_legs_darts = [
        leg[-1]['darts_thrown'] if (leg[-1].get('darts_thrown') and leg[-1]['darts_thrown'] > 0) else (len(leg) * 3)
        for leg in legs_visits if leg and leg[-1]['winner_player_id'] == player_id
    ]
    darts_per_leg = round(float(np.mean(won_legs_darts)), 1) if won_legs_darts else 0.0
    
    all_darts = [
        leg[-1]['darts_thrown'] if (leg[-1].get('darts_thrown') and leg[-1]['darts_thrown'] > 0) else (len(leg) * 3)
        for leg in legs_visits if leg
    ]
    if sum(all_darts) > 0 and all_scores:
        visit_stats['match_average'] = round(float((sum(all_scores) / sum(all_darts)) * 3), 1)
        
    start_data = analyze_start_performance(legs_visits)
    curve_data = calculate_performance_curve(legs_visits)
    phases = calculate_leg_phases(legs_visits)
    sample_rating = get_sample_size_rating(len(legs_visits))
    
    radar_metrics = calculate_skill_radar_metrics(
        start_index=start_data['start_index'],
        mid_avg=phases['mid_game']['average'],
        match_avg=visit_stats['match_average'],
        vol_std=visit_stats['volatility_std'],
        darts_per_leg=darts_per_leg,
        threshold_dict=dist_data['thresholds']
    )
    
    vol_std = visit_stats['volatility_std']
    match_avg = visit_stats['match_average']
    korridor_min = max(0, round(match_avg - vol_std))
    korridor_max = min(180, round(match_avg + vol_std))
    
    if vol_std < 20: konstanz_label, konstanz_color = "Sehr stabil", "#34D399"
    elif vol_std < 28: konstanz_label, konstanz_color = "Solide", "#38BDF8"
    elif vol_std < 35: konstanz_label, konstanz_color = "Ausgeglichen", "#FBBF24"
    else: konstanz_label, konstanz_color = "Volatil", "#F87171"
    
    return {
        'all_scores': all_scores,
        'visit_stats': visit_stats,
        'first_n': first_n,
        'dist_data': dist_data,
        'darts_per_leg': darts_per_leg,
        'start_data': start_data,
        'curve_data': curve_data,
        'phases': phases,
        'sample_rating': sample_rating,
        'radar_metrics': radar_metrics,
        'vol_std': vol_std,
        'korridor_min': korridor_min,
        'korridor_max': korridor_max,
        'konstanz_label': konstanz_label,
        'konstanz_color': konstanz_color,
        'legs_visits': legs_visits
    }

# ----------------------------------------------------
# MAIN TABS: EINZELSPIELER VS. SPIELER-VERGLEICH
# ----------------------------------------------------
tab_single, tab_compare = st.tabs([
    "👤 Einzelspieler-Analyse", 
    "⚔️ Spieler-Vergleich (Head-to-Head)"
])

# ====================================================
# TAB 1: EINZELSPIELER-ANALYSE
# ====================================================
with tab_single:
    col_f1, col_f2 = st.columns([2.5, 1.5])
    with col_f1:
        selected_player_name = st.selectbox("👤 Spieler auswählen", player_options, index=0, key="single_player_sel")
        selected_player_row = players_df[players_df['name'] == selected_player_name].iloc[0]
        selected_player_id = int(selected_player_row['id'])
        selected_player_team = selected_player_row['team']

    with col_f2:
        season_choice = st.selectbox("📅 Saison", ["Alle Saisons"] + available_seasons, index=1 if available_seasons else 0, key="single_season_sel")
        filter_season = None if season_choice == "Alle Saisons" else season_choice

    legs_visits = get_player_leg_visits(selected_player_id, season=filter_season)

    if not legs_visits:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"🎯 Für **{selected_player_name}** ({selected_player_team}) liegen in der Saison **{season_choice}** noch keine detaillierten Visit-Aufnahmen vor.")
        st.markdown("""
        <div class="mockup-card" style="margin-top: 15px;">
            <h3 style="color: #00D4FF; font-size: 18px; margin-top: 0;">💡 Wie werden Visit-Daten erfasst?</h3>
            <p style="color: #CBD5E1; font-size: 15px;">
                Detaillierte Spieldaten mit jeder einzelnen 3-Dart-Aufnahme können unter <b>„Eingabe“ ➔ Tab „🎯 Detailliertes Match“</b> erfasst werden.
                Dabei berechnet das System automatisch alle Ligakennzahlen (Averages, 80+, 100+, 180er) für die reguläre Tabelle mit – <b>ohne doppelte Eingabe!</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Beispiel-Spieldaten für diesen Spieler generieren (Demo-Test)", type="primary", key="btn_demo_single"):
            from analytics.data_access import save_full_analytics_match
            demo_legs = [
                {
                    'starter_player_id': selected_player_id,
                    'winner_player_id': selected_player_id,
                    'visits_a': [{'score': 140, 'rest_score': 361}, {'score': 100, 'rest_score': 261}, {'score': 85, 'rest_score': 176}, {'score': 100, 'rest_score': 76}, {'score': 76, 'rest_score': 0}],
                    'visits_b': [{'score': 60, 'rest_score': 441}, {'score': 60, 'rest_score': 381}, {'score': 80, 'rest_score': 301}, {'score': 60, 'rest_score': 241}]
                },
                {
                    'starter_player_id': 9999,
                    'winner_player_id': selected_player_id,
                    'visits_a': [{'score': 100, 'rest_score': 401}, {'score': 140, 'rest_score': 261}, {'score': 95, 'rest_score': 166}, {'score': 60, 'rest_score': 106}, {'score': 70, 'rest_score': 36}, {'score': 36, 'rest_score': 0}],
                    'visits_b': [{'score': 100, 'rest_score': 401}, {'score': 60, 'rest_score': 341}, {'score': 60, 'rest_score': 281}, {'score': 81, 'rest_score': 200}, {'score': 60, 'rest_score': 140}]
                }
            ]
            meta = {
                'player_a_id': selected_player_id, 'player_b_id': 0,
                'player_a_name': selected_player_name, 'player_b_name': 'Trainingspartner (Demo)',
                'match_date': '2026-09-01', 'season': filter_season if filter_season else '2026/2027',
                'winner_id': selected_player_id
            }
            save_full_analytics_match(meta, demo_legs, auto_sync_league=False)
            st.success("✅ Beispiel-Aufnahmen erfolgreich gespeichert! Lade Daten neu...")
            st.rerun()
    else:
        ana = compute_player_analytics(selected_player_id, selected_player_name, legs_visits)
        v_stats = ana['visit_stats']
        first_n = ana['first_n']
        dist_data = ana['dist_data']
        darts_per_leg = ana['darts_per_leg']
        start_data = ana['start_data']
        curve_data = ana['curve_data']
        phases = ana['phases']
        sample_rating = ana['sample_rating']
        radar_metrics = ana['radar_metrics']
        
        # Stichproben-Statusleiste
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px 18px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <span style="color: #94A3B8; font-size: 14px;">Datenbasis: <b style="color: #FFFFFF;">{len(legs_visits)} Legs</b> ({v_stats['total_visits']} Aufnahmen / ~{v_stats['total_visits'] * 3} Darts)</span>
                <span style="color: #94A3B8; font-size: 14px;">Team: <b style="color: #00D4FF;">{selected_player_team}</b></span>
            </div>
            <div style="background: {sample_rating['color']}22; border: 1px solid {sample_rating['color']}; border-radius: 6px; padding: 4px 12px; color: {sample_rating['color']}; font-weight: 700; font-size: 12px;">
                {sample_rating['badge']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 1. Haupt-KPIs
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(f"""
            <div class="kpi-box" title="3-Dart-Punktedurchschnitt aller gespielten Aufnahmen">
                <div class="kpi-tag">MATCH AVERAGE ℹ️</div>
                <div class="kpi-main" style="color: #00D4FF;">Ø {v_stats['match_average']:.1f}</div>
                <div class="kpi-sub">Gesamtschnitt aller Visits</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="kpi-box" title="Durchschnitt der ersten 3 Aufnahmen (Darts 1–9) pro Leg">
                <div class="kpi-tag">FIRST 9 AVERAGE ℹ️</div>
                <div class="kpi-main" style="color: #38BDF8;">Ø {first_n['first_9_avg']:.1f}</div>
                <div class="kpi-sub">Visits 1 bis 3 (Startphase)</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="kpi-box" title="Durchschnitt der ersten 6 Aufnahmen (Darts 1–18) pro Leg">
                <div class="kpi-tag">FIRST 18 AVERAGE ℹ️</div>
                <div class="kpi-main" style="color: #818CF8;">Ø {first_n['first_18_avg']:.1f}</div>
                <div class="kpi-sub">Visits 1 bis 6 (Scoring-Phase)</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="kpi-box" title="Durchschnittlich benötigte Pfeile in allen gewonnenen Legs">
                <div class="kpi-tag">DARTS PER LEG ℹ️</div>
                <div class="kpi-main" style="color: #34D399;">{darts_per_leg:.1f}</div>
                <div class="kpi-sub">Ø bei gewonnenen Legs</div>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div class="kpi-box" title="Streuung / Standardabweichung der Scores um den Schnitt. Zeigt Wurfkonstanz.">
                <div class="kpi-tag">KONSTANZ / STREUUNG ℹ️</div>
                <div class="kpi-main" style="color: {ana['konstanz_color']};">±{ana['vol_std']:.1f} <span style="font-size: 13px; font-weight: 600;">({ana['konstanz_label']})</span></div>
                <div class="kpi-sub">Korridor: {ana['korridor_min']}–{ana['korridor_max']} Pkt</div>
            </div>
            """, unsafe_allow_html=True)
        with c6:
            s_color = "#34D399" if start_data['start_index'] >= 75 else ("#38BDF8" if start_data['start_index'] >= 50 else ("#FBBF24" if start_data['start_index'] >= 35 else "#F87171"))
            st.markdown(f"""
            <div class="kpi-box" title="Leg-Auftaktstärke (0-100) basierend auf First 9 Darts, Highscores und Fehlwurf-Dämpfung">
                <div class="kpi-tag">START INDEX ℹ️</div>
                <div class="kpi-main" style="color: {s_color};">{start_data['start_index']:.0f}<span style="font-size: 14px; color: #94A3B8;">/100</span></div>
                <div class="kpi-sub">Leg-Auftaktstärke (Amateur-Index)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        with st.expander("📖 DAE-Lexikon: Was bedeuten alle Kennzahlen & Felder genau?", expanded=False):
            st.markdown(r"""
            Hier findest du alle Kennzahlen der **Dart Analytics Engine (DAE)** verständlich auf den Punkt erklärt:
            - **MATCH AVERAGE:** Der klassische 3-Dart-Punktedurchschnitt über das gesamte Spiel hinweg.
            - **FIRST 9 / 18 AVERAGE:** 3-Dart-Schnitt der ersten 3 (Visits 1–3) bzw. ersten 6 Aufnahmen (Visits 1–6).
            - **DARTS PER LEG:** Die durchschnittliche Anzahl geworfener Pfeile in den gewonnenen Legs.
            - **KONSTANZ / STREUUNG:** Misst die Schwankungsbreite der Aufnahmen. Eine niedrige Streuung bedeutet hohe Wiederholgenauigkeit.
            - **START INDEX (0–100):** Bewertet die Auftaktstärke in den ersten 3 Aufnahmen auf Kreisklasse-/Amateurniveau.
            - **SKILL-RADAR:** Normiertes 6-Dimensionen-Fähigkeitenprofil (Start, Mid-Game, Power, Highscores, Konstanz, Finish).
            """)

        st.markdown("<br>", unsafe_allow_html=True)

        # 1. Leg-Phasen Analyse
        st.subheader("📊 1. Leg-Phasen Analyse", help="Unterteilt das Leg in Opening (Visits 1–3), Mid Game (Visits 4–6) und Finish-Bereich (Rest ≤ 170).")
        st.caption(f"Leistungsentwicklung im Verlauf der Legs. Einstufung: **{phases['phase_trend']}**")
        ph_col1, ph_col2, ph_col3 = st.columns(3)
        with ph_col1:
            st.markdown(f"""
            <div class="mockup-card" style="border-left: 4px solid #38BDF8;">
                <div class="card-title"><span style="color: #38BDF8;">🏹 OPENING (Visits 1–3)</span><span style="font-size: 12px; color: #94A3B8;">Startphase</span></div>
                <div style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 8px 0;">Ø {phases['opening']['average']:.1f}</div>
                <div style="color: #94A3B8; font-size: 13px; line-height: 1.8;">
                    • Streuung: <b>±{phases['opening']['volatility_std']:.1f}</b> Pkt<br>
                    • 100+ Rate: <b style="color: #38BDF8;">{phases['opening']['rate_100_pct']:.1f}%</b><br>
                    • 140+ Rate: <b style="color: #818CF8;">{phases['opening']['rate_140_pct']:.1f}%</b><br>
                    • 180er Rate: <b style="color: #F43F5E;">{phases['opening']['rate_180_pct']:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ph_col2:
            st.markdown(f"""
            <div class="mockup-card" style="border-left: 4px solid #818CF8;">
                <div class="card-title"><span style="color: #818CF8;">⚔️ MID GAME (Visits 4–6)</span><span style="font-size: 12px; color: #94A3B8;">Mittelspiel</span></div>
                <div style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 8px 0;">Ø {phases['mid_game']['average']:.1f}</div>
                <div style="color: #94A3B8; font-size: 13px; line-height: 1.8;">
                    • Streuung: <b>±{phases['mid_game']['volatility_std']:.1f}</b> Pkt<br>
                    • 100+ Rate: <b style="color: #38BDF8;">{phases['mid_game']['rate_100_pct']:.1f}%</b><br>
                    • 140+ Rate: <b style="color: #818CF8;">{phases['mid_game']['rate_140_pct']:.1f}%</b><br>
                    • 180er Rate: <b style="color: #F43F5E;">{phases['mid_game']['rate_180_pct']:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ph_col3:
            st.markdown(f"""
            <div class="mockup-card" style="border-left: 4px solid #34D399;">
                <div class="card-title"><span style="color: #34D399;">🏁 FINISH (Rest ≤ 170)</span><span style="font-size: 12px; color: #94A3B8;">Entscheidungsphase</span></div>
                <div style="font-size: 28px; font-weight: 800; color: #FFFFFF; margin: 8px 0;">Ø {phases['finish']['average']:.1f}</div>
                <div style="color: #94A3B8; font-size: 13px; line-height: 1.8;">
                    • Streuung: <b>±{phases['finish']['volatility_std']:.1f}</b> Pkt<br>
                    • 100+ Rate: <b style="color: #38BDF8;">{phases['finish']['rate_100_pct']:.1f}%</b><br>
                    • 140+ Rate: <b style="color: #818CF8;">{phases['finish']['rate_140_pct']:.1f}%</b><br>
                    • 180er Rate: <b style="color: #F43F5E;">{phases['finish']['rate_180_pct']:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Skill-Radar
        st.subheader("🕸️ 2. Skill-Radar & Spielerprofil (Spinnendiagramm)", help="Visualisiert die 6 Kernkompetenzen auf einer normierten Skala von 0–100 Punkten.")
        st.caption(f"Gesamt-Rating: **{radar_metrics['overall_skill']:.0f} / 100 ({radar_metrics['overall_label']})** • Basiert auf {len(legs_visits)} erfassten Legs")
        col_radar_chart, col_radar_details = st.columns([1.3, 1.0])
        with col_radar_chart:
            r_values = [d['value'] for d in radar_metrics['dimensions']]
            theta_labels = [d['dim'] for d in radar_metrics['dimensions']]
            r_values_closed = r_values + [r_values[0]]
            theta_labels_closed = theta_labels + [theta_labels[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=r_values_closed, theta=theta_labels_closed, fill='toself',
                fillcolor='rgba(0, 212, 255, 0.22)', line=dict(color='#00D4FF', width=3),
                marker=dict(size=7, color='#38BDF8', symbol='circle'), name=selected_player_name,
                hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f} / 100<extra></extra>"
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor='rgba(15, 23, 42, 0.65)',
                    radialaxis=dict(visible=True, range=[0, 100], tickvals=[20, 40, 60, 80, 100], tickfont=dict(color='#64748B', size=10), gridcolor='rgba(255, 255, 255, 0.1)'),
                    angularaxis=dict(tickfont=dict(color='#E2E8F0', size=12), gridcolor='rgba(255, 255, 255, 0.1)', linecolor='rgba(0, 212, 255, 0.3)')
                ),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=45, r=45, t=30, b=30), showlegend=False, height=380
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with col_radar_details:
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 12px; padding: 14px 18px; margin-top: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #FFFFFF;">FÄHIGKEITEN-PROFIL</span>
                    <span style="background: rgba(0,212,255,0.15); color: #00D4FF; border: 1px solid #00D4FF; padding: 2px 10px; border-radius: 6px; font-weight: 800; font-size: 13px;">
                        Ø {radar_metrics['overall_skill']:.0f} / 100
                    </span>
                </div>
            """, unsafe_allow_html=True)
            for dim in radar_metrics['dimensions']:
                v = dim['value']
                b_color = "#34D399" if v >= 75 else ("#38BDF8" if v >= 55 else ("#FBBF24" if v >= 40 else "#F87171"))
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 2px 0;">
                    <div><span style="color: #F1F5F9; font-weight: 600; font-size: 13px;">{dim['dim']}</span><span style="color: #64748B; font-size: 11px; display: block;">{dim['desc']}</span></div>
                    <div style="text-align: right;"><span style="color: {b_color}; font-weight: 800; font-size: 14px;">{v:.0f}<span style="font-size: 11px; color: #94A3B8;">/100</span></span><span style="display: block; font-size: 10px; color: {b_color}; font-weight: 700;">{dim['label']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # KI-Leistungsdiagnostik & Scouting-Bericht (Einzelspieler)
        ai_p = generate_ai_player_profile(ana, selected_player_name)
        render_html(f"""
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 14px; padding: 18px 22px; margin-top: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">{ai_p['archetype_icon']}</span>
                    <div>
                        <div style="color: #00D4FF; font-size: 11px; font-weight: 800; letter-spacing: 1px;">KI-LEISTUNGSDIAGNOSTIK & SCOUTING-PROFIL</div>
                        <div style="color: #FFFFFF; font-size: 18px; font-weight: 800;">{ai_p['archetype']}</div>
                    </div>
                </div>
                <div style="background: rgba(0, 212, 255, 0.12); border: 1px solid #00D4FF; border-radius: 8px; padding: 4px 12px; color: #00D4FF; font-weight: 700; font-size: 12px;">
                    🎯 DAE KI-Rating: {ai_p['total_score']:.0f}/100
                </div>
            </div>
            <p style="color: #CBD5E1; font-size: 13px; line-height: 1.6; margin-bottom: 16px;">
                {ai_p['archetype_desc']}
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
                <div style="background: rgba(52, 211, 153, 0.08); border-left: 3px solid #34D399; padding: 10px 14px; border-radius: 6px;">
                    <div style="color: #34D399; font-weight: 700; font-size: 12px; margin-bottom: 4px;">🌟 TOP-STÄRKEN</div>
                    <div style="color: #F1F5F9; font-size: 12px; line-height: 1.6;">
                        • <b>{ai_p['strengths'][0][0]}</b> ({ai_p['strengths'][0][2]})<br>
                        • <b>{ai_p['strengths'][1][0]}</b> ({ai_p['strengths'][1][2]})
                    </div>
                </div>
                <div style="background: rgba(248, 113, 113, 0.08); border-left: 3px solid #F87171; padding: 10px 14px; border-radius: 6px;">
                    <div style="color: #F87171; font-weight: 700; font-size: 12px; margin-bottom: 4px;">⚠️ KRITISCHE HANDLUNGSFELDER</div>
                    <div style="color: #F1F5F9; font-size: 12px; line-height: 1.6;">
                        • <b>{ai_p['weaknesses'][0][0]}</b> ({ai_p['weaknesses'][0][2]})<br>
                        • <b>{ai_p['weaknesses'][1][0]}</b> ({ai_p['weaknesses'][1][2]})
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
                <div style="background: rgba(129, 140, 248, 0.08); border-left: 3px solid #818CF8; padding: 10px 14px; border-radius: 6px;">
                    <div style="color: #818CF8; font-weight: 700; font-size: 12px; margin-bottom: 4px;">🎯 TRAININGS-SCHWERPUNKT</div>
                    <div style="color: #FFFFFF; font-weight: 600; font-size: 13px; margin-bottom: 2px;">{ai_p['training_title']}</div>
                    <div style="color: #94A3B8; font-size: 12px; line-height: 1.5;">{ai_p['training_text']}</div>
                </div>
                <div style="background: rgba(251, 191, 36, 0.08); border-left: 3px solid #FBBF24; padding: 10px 14px; border-radius: 6px;">
                    <div style="color: #FBBF24; font-weight: 700; font-size: 12px; margin-bottom: 4px;">🛡️ GEGNER-SCOUTING-TIPP</div>
                    <div style="color: #CBD5E1; font-size: 12px; line-height: 1.5;">{ai_p['scout_tip']}</div>
                </div>
            </div>

            <!-- 3-Card Dashboard-Grid: Psychologische & Verhaltens-Diagnostik -->
            <div style="margin-top: 6px;">
                <div style="color: #38BDF8; font-size: 11px; font-weight: 800; letter-spacing: 1px; margin-bottom: 10px;">
                    🧠 PSYCHOLOGISCHE LEISTUNGSDIAGNOSTIK & VERHALTEN
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                    <!-- Karte 1: Bounce-Back -->
                    <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(56, 189, 248, 0.25); border-top: 3px solid #38BDF8; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #38BDF8; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">🔄 BOUNCE-BACK</span>
                                <span style="background: {ai_p['badge_bounce_color']}22; color: {ai_p['badge_bounce_color']}; border: 1px solid {ai_p['badge_bounce_color']}; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">
                                    {ai_p['badge_bounce']}
                                </span>
                            </div>
                            <div style="color: #CBD5E1; font-size: 12px; line-height: 1.55;">
                                {ai_p['text_bounce']}
                            </div>
                        </div>
                        <div style="margin-top: 10px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; color: #64748B;">
                            Folgescore nach ≤45: <b style="color: #FFFFFF;">Ø {ai_p['behavior_metrics']['bounce_back_avg']:.1f}</b> ({ai_p['behavior_metrics']['bounce_back_delta']:+.1f})
                        </div>
                    </div>

                    <!-- Karte 2: Gegnerdruck -->
                    <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(244, 63, 94, 0.25); border-top: 3px solid #F43F5E; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #F43F5E; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">🔥 GEGNERDRUCK</span>
                                <span style="background: {ai_p['badge_pressure_color']}22; color: {ai_p['badge_pressure_color']}; border: 1px solid {ai_p['badge_pressure_color']}; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">
                                    {ai_p['badge_pressure']}
                                </span>
                            </div>
                            <div style="color: #CBD5E1; font-size: 12px; line-height: 1.55;">
                                {ai_p['text_pressure']}
                            </div>
                        </div>
                        <div style="margin-top: 10px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; color: #64748B;">
                            Bei Gegner Rest ≤170: <b style="color: #FFFFFF;">Ø {ai_p['behavior_metrics']['pressure_avg']:.1f}</b> ({ai_p['behavior_metrics']['pressure_delta']:+.1f})
                        </div>
                    </div>

                    <!-- Karte 3: Fokus & Ausdauer -->
                    <div style="background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(168, 85, 247, 0.25); border-top: 3px solid #A855F7; border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="color: #A855F7; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">⏱️ FOKUS & AUSDAUER</span>
                                <span style="background: {ai_p['badge_focus_color']}22; color: {ai_p['badge_focus_color']}; border: 1px solid {ai_p['badge_focus_color']}; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">
                                    {ai_p['badge_focus']}
                                </span>
                            </div>
                            <div style="color: #CBD5E1; font-size: 12px; line-height: 1.55;">
                                {ai_p['text_focus']}
                            </div>
                        </div>
                        <div style="margin-top: 10px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; color: #64748B;">
                            Visits 1–3: <b style="color: #FFFFFF;">Ø {ai_p['behavior_metrics']['focus_early']:.1f}</b> → Spät: <b style="color: #FFFFFF;">Ø {ai_p['behavior_metrics']['focus_late']:.1f}</b>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Performance-Kurve
        st.subheader("📈 3. Performance-Kurve pro Aufnahme (Visit 1 bis N)", help="Zeigt die Score-Entwicklung und Streuung Wurf für Wurf von Visit 1 bis zum Match-Ende.")
        st.caption("Wie entwickelt sich die Scoring-Power eines Spielers Aufnahme für Aufnahme innerhalb des Legs?")
        if curve_data:
            curve_df = pd.DataFrame(curve_data)
            col_chart, col_table = st.columns([2.2, 1.8])
            with col_chart:
                fig_single = go.Figure()
                fig_single.add_trace(go.Scatter(
                    x=curve_df['visit_label'], y=curve_df['average'],
                    mode='lines+markers', name='Average',
                    line=dict(color='#00D4FF', width=2.5),
                    marker=dict(size=6)
                ))
                fig_single.add_trace(go.Scatter(
                    x=curve_df['visit_label'], y=curve_df['median'],
                    mode='lines+markers', name='Median',
                    line=dict(color='#818CF8', width=2, dash='dot'),
                    marker=dict(size=5)
                ))
                fig_single.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)',
                    margin=dict(l=30, r=20, t=20, b=30),
                    xaxis=dict(
                        categoryorder='array',
                        categoryarray=curve_df['visit_label'].tolist(),
                        gridcolor='rgba(255,255,255,0.08)',
                        tickfont=dict(color='#94A3B8')
                    ),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.08)', tickfont=dict(color='#94A3B8')),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#FFFFFF"))
                )
                st.plotly_chart(fig_single, use_container_width=True)
            with col_table:
                disp_curve = curve_df[['visit_label', 'sample_count', 'average', 'volatility_std', 'rate_100_pct']].rename(
                    columns={'visit_label': 'Aufnahme', 'sample_count': 'Anz. Visits', 'average': 'Ø Score', 'volatility_std': 'Streuung', 'rate_100_pct': '100+ Rate'}
                )
                disp_curve['100+ Rate'] = disp_curve['100+ Rate'].apply(lambda x: f"{x:.1f}%")
                disp_curve['Ø Score'] = disp_curve['Ø Score'].apply(lambda x: f"{x:.1f}")
                st.dataframe(disp_curve, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Score-Verteilung
        st.subheader("🎯 4. Score-Verteilung & Raten pro 100 Visits", help="Einteilung aller geworfenen Aufnahmen in Klassen sowie Highscore-Raten hochgerechnet auf 100 Aufnahmen.")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("##### Aufnahmen nach Score-Kategorien (Buckets)")
            b_dict = dist_data['buckets']
            b_df = pd.DataFrame([{'Kategorie': k, 'Anzahl': v['count'], 'Anteil': f"{v['pct']:.1f}%", 'Rate pro 100': v['rate_per_100']} for k, v in b_dict.items()])
            st.bar_chart(b_df.set_index('Kategorie')['Rate pro 100'], color="#00D4FF")
        with col_d2:
            st.markdown("##### Schwellenwert-Raten (pro 100 Aufnahmen)")
            t_dict = dist_data['thresholds']
            t_df = pd.DataFrame([{'Schwellenwert': k, 'Anzahl': v['count'], 'Anteil (%)': f"{v['pct']:.1f}%", 'Rate / 100 Visits': f"{v['rate_per_100']:.1f}"} for k, v in t_dict.items()])
            st.dataframe(t_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Match- & Leg-Protokoll
        st.subheader("📋 5. Match- & Leg-Protokoll (2K Darts Spielberichte)", help="Detaillierte Spielberichte mit Anwurf, Legs, Checkouts, Spieldauer und Wurfverläufen.")
        st.caption("Alle erfassten Matches dieses Spielers inklusive Spieldauer, Start/Endzeit, Board und Darts pro Leg.")
        player_matches = get_all_analytics_matches(player_id=selected_player_id, player_name=selected_player_name, season=filter_season)
        if player_matches.empty:
            st.info(f"Keine Matchberichte für {selected_player_name} in der Saison {season_choice} vorhanden.")
        else:
            for _, m_row in player_matches.iterrows():
                mid = int(m_row['id'])
                m_nr = int(m_row.get('match_nr', 0) or 0)
                m_nr_disp = f"#{m_nr}" if m_nr > 0 else f"ID {mid}"
                p_a = str(m_row['player_a_name'])
                p_b = str(m_row['player_b_name'])
                m_dt_str = pd.to_datetime(m_row['match_date']).strftime('%d.%m.%Y')
                dauer_str = f"{m_row.get('duration_min', 14)} Min" if m_row.get('duration_min') else "k.A."
                time_str = f"({m_row.get('start_time', '')} – {m_row.get('end_time', '')})" if m_row.get('start_time') else ""
                board_str = f"Board {m_row.get('board_nr', 1)}"
                mdet = get_analytics_match_details(mid)
                legs_list = mdet.get('legs', []) if mdet else []
                w_a = sum(1 for l in legs_list if (l.get('winner_player_id') == mdet.get('player_a_id') and l.get('winner_player_id', 0) > 0) or (int(l.get('checkout_a', 0) or 0) > 0))
                w_b = len(legs_list) - w_a if legs_list else 0
                expander_title = f"🎯 Spiel {m_nr_disp} | {m_dt_str} | {p_a} vs. {p_b} | Ergebnis: {w_a}:{w_b} | ⏱️ {dauer_str} {time_str} | {board_str}"
                with st.expander(expander_title, expanded=False):
                    if not legs_list:
                        st.warning("Keine Leg-Daten für dieses Match vorhanden.")
                        continue
                    leg_rows = []
                    for l in legs_list:
                        l_num = l.get('leg_num', 1)
                        d_a = int(l.get('darts_thrown_a', 0) or 0)
                        d_b = int(l.get('darts_thrown_b', 0) or 0)
                        co_a = int(l.get('checkout_a', 0) or 0)
                        co_b = int(l.get('checkout_b', 0) or 0)
                        v_a_cnt = len(l.get('visits_a', []))
                        v_b_cnt = len(l.get('visits_b', []))
                        act_d_a = d_a if d_a > 0 else (v_a_cnt * 3)
                        act_d_b = d_b if d_b > 0 else (v_b_cnt * 3)
                        l_pts_a = sum(v['score'] for v in l.get('visits_a', []))
                        l_pts_b = sum(v['score'] for v in l.get('visits_b', []))
                        l_avg_a = round((l_pts_a / act_d_a) * 3, 1) if act_d_a > 0 else 0.0
                        l_avg_b = round((l_pts_b / act_d_b) * 3, 1) if act_d_b > 0 else 0.0
                        starter_pid = l.get('starter_player_id', 0)
                        winner_pid = l.get('winner_player_id', 0)
                        starter_name = p_a if (starter_pid == mdet.get('player_a_id') or starter_pid == 0) else p_b
                        winner_name = p_a if (winner_pid == mdet.get('player_a_id') or (co_a > 0)) else p_b
                        is_brk = bool(l.get('is_break', False))
                        brk_str = "✅ Break" if is_brk else "-"
                        leg_rows.append({
                            'Leg': f"Leg {l_num}",
                            'Anwurf': f"🎯 {get_short_name(starter_name)}",
                            'Gewinner': f"🏆 {get_short_name(winner_name)}",
                            f'Darts ({get_short_name(p_a)})': d_a if d_a > 0 else "-",
                            f'Ø Avg ({get_short_name(p_a)})': f"Ø {l_avg_a:.1f}",
                            f'Finish ({get_short_name(p_a)})': co_a if co_a > 0 else "-",
                            f'Darts ({get_short_name(p_b)})': d_b if d_b > 0 else "-",
                            f'Ø Avg ({get_short_name(p_b)})': f"Ø {l_avg_b:.1f}",
                            f'Finish ({get_short_name(p_b)})': co_b if co_b > 0 else "-",
                            'Break': brk_str
                        })
                    st.dataframe(pd.DataFrame(leg_rows), use_container_width=True, hide_index=True)


# ====================================================
# TAB 2: HEAD-TO-HEAD SPIELER-VERGLEICH
# ====================================================
with tab_compare:
    col_c1, col_c2, col_c3 = st.columns([2, 2, 1.5])
    with col_c1:
        cmp_a_name = st.selectbox("🔵 Spieler A auswählen", player_options, index=0, key="cmp_sel_a")
        cmp_a_row = players_df[players_df['name'] == cmp_a_name].iloc[0]
        cmp_a_id = int(cmp_a_row['id'])
        cmp_a_team = cmp_a_row['team']
        
    with col_c2:
        default_b_idx = 1 if len(player_options) > 1 else 0
        cmp_b_name = st.selectbox("🟠 Spieler B auswählen", player_options, index=default_b_idx, key="cmp_sel_b")
        cmp_b_row = players_df[players_df['name'] == cmp_b_name].iloc[0]
        cmp_b_id = int(cmp_b_row['id'])
        cmp_b_team = cmp_b_row['team']
        
    with col_c3:
        cmp_season_sel = st.selectbox("📅 Saison", ["Alle Saisons"] + available_seasons, index=1 if available_seasons else 0, key="cmp_season_sel")
        cmp_filter_season = None if cmp_season_sel == "Alle Saisons" else cmp_season_sel

    if cmp_a_name == cmp_b_name:
        st.warning("⚠️ Bitte wähle zwei verschiedene Spieler für den Vergleich aus.")
    else:
        legs_a = get_player_leg_visits(cmp_a_id, season=cmp_filter_season)
        legs_b = get_player_leg_visits(cmp_b_id, season=cmp_filter_season)
        
        if not legs_a:
            st.info(f"🎯 Für **{cmp_a_name}** ({cmp_a_team}) liegen in der Saison **{cmp_season_sel}** noch keine Leg-Aufnahmen vor.")
        elif not legs_b:
            st.info(f"🎯 Für **{cmp_b_name}** ({cmp_b_team}) liegen in der Saison **{cmp_season_sel}** noch keine Leg-Aufnahmen vor.")
        else:
            # Beide Spieler haben Daten -> Vergleich berechnen!
            ana_a = compute_player_analytics(cmp_a_id, cmp_a_name, legs_a)
            ana_b = compute_player_analytics(cmp_b_id, cmp_b_name, legs_b)
            
            skill_a = ana_a['radar_metrics']['overall_skill']
            skill_b = ana_b['radar_metrics']['overall_skill']
            
            # 1. Matchup-Banner
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(245, 158, 11, 0.12)); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 16px 24px; margin-bottom: 22px; display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: left;">
                    <span style="font-size: 20px; font-weight: 800; color: #00D4FF;">🔵 {cmp_a_name}</span><br>
                    <span style="color: #94A3B8; font-size: 13px;">Team: <b style="color: #FFFFFF;">{cmp_a_team}</b> • {len(legs_a)} Legs ({ana_a['visit_stats']['total_visits']} Visits)</span><br>
                    <span style="display: inline-block; margin-top: 4px; background: rgba(0,212,255,0.2); border: 1px solid #00D4FF; border-radius: 6px; padding: 2px 10px; font-weight: 800; color: #00D4FF; font-size: 13px;">Skill: {skill_a:.0f}/100 ({ana_a['radar_metrics']['overall_label']})</span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 26px; font-weight: 900; color: #FFFFFF; letter-spacing: 2px;">⚔️ VS ⚔️</span><br>
                    <span style="color: #F1F5F9; font-size: 12px; font-weight: 600;">HEAD-TO-HEAD DUELL</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 20px; font-weight: 800; color: #F59E0B;">🟠 {cmp_b_name}</span><br>
                    <span style="color: #94A3B8; font-size: 13px;">Team: <b style="color: #FFFFFF;">{cmp_b_team}</b> • {len(legs_b)} Legs ({ana_b['visit_stats']['total_visits']} Visits)</span><br>
                    <span style="display: inline-block; margin-top: 4px; background: rgba(245,158,11,0.2); border: 1px solid #F59E0B; border-radius: 6px; padding: 2px 10px; font-weight: 800; color: #F59E0B; font-size: 13px;">Skill: {skill_b:.0f}/100 ({ana_b['radar_metrics']['overall_label']})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Top-KPI Vergleich (6 Spalten)
            def get_kpi_winner(val_a, val_b, lower_better=False):
                if val_a == val_b:
                    return "Gleichstand", "#94A3B8"
                if lower_better:
                    winner = cmp_a_name if val_a < val_b else cmp_b_name
                    diff = abs(val_a - val_b)
                    return f"👑 {get_short_name(winner)} (-{diff:.1f})", ("#00D4FF" if val_a < val_b else "#F59E0B")
                else:
                    winner = cmp_a_name if val_a > val_b else cmp_b_name
                    diff = abs(val_a - val_b)
                    return f"👑 {get_short_name(winner)} (+{diff:.1f})", ("#00D4FF" if val_a > val_b else "#F59E0B")

            k_col1, k_col2, k_col3, k_col4, k_col5, k_col6 = st.columns(6)
            
            # KPI 1: Match Avg
            w_msg, w_col = get_kpi_winner(ana_a['visit_stats']['match_average'], ana_b['visit_stats']['match_average'])
            with k_col1:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">MATCH AVERAGE</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">{ana_a['visit_stats']['match_average']:.1f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">{ana_b['visit_stats']['match_average']:.1f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # KPI 2: First 9
            w_msg, w_col = get_kpi_winner(ana_a['first_n']['first_9_avg'], ana_b['first_n']['first_9_avg'])
            with k_col2:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">FIRST 9 AVERAGE</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">{ana_a['first_n']['first_9_avg']:.1f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">{ana_b['first_n']['first_9_avg']:.1f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # KPI 3: First 18
            w_msg, w_col = get_kpi_winner(ana_a['first_n']['first_18_avg'], ana_b['first_n']['first_18_avg'])
            with k_col3:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">FIRST 18 AVERAGE</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">{ana_a['first_n']['first_18_avg']:.1f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">{ana_b['first_n']['first_18_avg']:.1f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # KPI 4: Darts per Leg
            w_msg, w_col = get_kpi_winner(ana_a['darts_per_leg'], ana_b['darts_per_leg'], lower_better=True)
            with k_col4:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">DARTS PER LEG</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">{ana_a['darts_per_leg']:.1f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">{ana_b['darts_per_leg']:.1f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # KPI 5: Konstanz
            w_msg, w_col = get_kpi_winner(ana_a['vol_std'], ana_b['vol_std'], lower_better=True)
            with k_col5:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">WURFKONSTANZ (±σ)</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">±{ana_a['vol_std']:.1f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">±{ana_b['vol_std']:.1f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # KPI 6: Start Index
            w_msg, w_col = get_kpi_winner(ana_a['start_data']['start_index'], ana_b['start_data']['start_index'])
            with k_col6:
                st.markdown(f"""
                <div class="kpi-box">
                    <div class="kpi-tag">START INDEX</div>
                    <div style="font-size: 20px; font-weight: 800; margin: 6px 0;">
                        <span style="color: #00D4FF;">{ana_a['start_data']['start_index']:.0f}</span>
                        <span style="color: #64748B; font-size: 14px;"> vs </span>
                        <span style="color: #F59E0B;">{ana_b['start_data']['start_index']:.0f}</span>
                    </div>
                    <div class="kpi-sub" style="color: {w_col}; font-weight: 700;">{w_msg}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 3. Doppel-Skill-Radar (Überlagertes Spinnendiagramm)
            st.subheader("🕸️ 1. Doppel-Skill-Radar (Fähigkeiten-Vergleich)", help="Überlagerung aller 6 Dimensionen beider Spieler in einem gemeinsamen Spinnendiagramm.")
            r_col_chart, r_col_table = st.columns([1.3, 1.0])
            
            with r_col_chart:
                r_a = [d['value'] for d in ana_a['radar_metrics']['dimensions']]
                r_b = [d['value'] for d in ana_b['radar_metrics']['dimensions']]
                labels = [d['dim'] for d in ana_a['radar_metrics']['dimensions']]
                
                r_a_closed = r_a + [r_a[0]]
                r_b_closed = r_b + [r_b[0]]
                labels_closed = labels + [labels[0]]
                
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Scatterpolar(
                    r=r_a_closed, theta=labels_closed, fill='toself',
                    fillcolor='rgba(0, 212, 255, 0.20)', line=dict(color='#00D4FF', width=3),
                    marker=dict(size=6, color='#00D4FF'), name=cmp_a_name,
                    hovertemplate=f"<b>{cmp_a_name}</b><br>%{{theta}}: %{{r:.1f}} / 100<extra></extra>"
                ))
                fig_cmp.add_trace(go.Scatterpolar(
                    r=r_b_closed, theta=labels_closed, fill='toself',
                    fillcolor='rgba(245, 158, 11, 0.20)', line=dict(color='#F59E0B', width=3),
                    marker=dict(size=6, color='#F59E0B'), name=cmp_b_name,
                    hovertemplate=f"<b>{cmp_b_name}</b><br>%{{theta}}: %{{r:.1f}} / 100<extra></extra>"
                ))
                fig_cmp.update_layout(
                    polar=dict(
                        bgcolor='rgba(15, 23, 42, 0.65)',
                        radialaxis=dict(visible=True, range=[0, 100], tickvals=[20, 40, 60, 80, 100], tickfont=dict(color='#64748B', size=10), gridcolor='rgba(255, 255, 255, 0.1)'),
                        angularaxis=dict(tickfont=dict(color='#E2E8F0', size=12), gridcolor='rgba(255, 255, 255, 0.1)', linecolor='rgba(255, 255, 255, 0.2)')
                    ),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=45, r=45, t=30, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="#FFFFFF", size=13)),
                    height=400
                )
                st.plotly_chart(fig_cmp, use_container_width=True, config={'displayModeBar': False})

            with r_col_table:
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; padding: 14px 18px; margin-top: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
                        <span style="font-size: 14px; font-weight: 700; color: #FFFFFF;">DIREKTER DIMENSIONEN-VERGLEICH</span>
                        <span style="font-size: 12px; color: #94A3B8;">0 bis 100 Punkte</span>
                    </div>
                """, unsafe_allow_html=True)
                for da, db in zip(ana_a['radar_metrics']['dimensions'], ana_b['radar_metrics']['dimensions']):
                    va = da['value']
                    vb = db['value']
                    if va > vb:
                        v_str = f"<b style='color: #00D4FF;'>👑 {get_short_name(cmp_a_name)} (+{va-vb:.1f})</b>"
                    elif vb > va:
                        v_str = f"<b style='color: #F59E0B;'>👑 {get_short_name(cmp_b_name)} (+{vb-va:.1f})</b>"
                    else:
                        v_str = "<span style='color: #94A3B8;'>Gleichstand</span>"
                    st.markdown(f"""
                    <div style="margin-bottom: 9px; padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.04);">
                        <div style="display: flex; justify-content: space-between; font-size: 13px;">
                            <span style="color: #F1F5F9; font-weight: 600;">{da['dim']}</span>
                            <span>
                                <b style="color: #00D4FF;">{va:.0f}</b> <span style="color: #64748B;">:</span> <b style="color: #F59E0B;">{vb:.0f}</b>
                            </span>
                        </div>
                        <div style="font-size: 11px; text-align: right; margin-top: 1px;">{v_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # KI-Duell-Prognose & Head-to-Head Scouting
            ai_h2h = generate_ai_h2h_scouting(ana_a, ana_b, cmp_a_name, cmp_b_name)
            p_a_prob = ai_h2h['win_prob_a']
            p_b_prob = ai_h2h['win_prob_b']
            
            render_html(f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 14px; padding: 18px 22px; margin-top: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 14px;">
                    <div>
                        <div style="color: #00D4FF; font-size: 11px; font-weight: 800; letter-spacing: 1px;">KI-MATCHUP-PROGNOSE & TAKTIK-SCOUTING</div>
                        <div style="color: #FFFFFF; font-size: 18px; font-weight: 800;">{ai_h2h['matchup_title']}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 12px; color: #94A3B8;">Gesamt-Skill</span>
                        <div style="font-weight: 800; font-size: 15px;">
                            <span style="color: #00D4FF;">{ai_h2h['score_a']:.0f}</span>
                            <span style="color: #64748B;"> vs </span>
                            <span style="color: #F59E0B;">{ai_h2h['score_b']:.0f}</span>
                        </div>
                    </div>
                </div>
                
                <p style="color: #CBD5E1; font-size: 13px; line-height: 1.6; margin-bottom: 16px;">
                    {ai_h2h['tactical_summary']}
                </p>

                <!-- Siegwahrscheinlichkeits-Balken -->
                <div style="margin-bottom: 18px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; margin-bottom: 6px;">
                        <span style="color: #00D4FF;">{get_short_name(cmp_a_name)}: {p_a_prob:.1f}% Siegchance</span>
                        <span style="color: #F59E0B;">{p_b_prob:.1f}% Siegchance: {get_short_name(cmp_b_name)}</span>
                    </div>
                    <div style="height: 10px; border-radius: 5px; background: #F59E0B; overflow: hidden; display: flex;">
                        <div style="width: {p_a_prob}%; background: #00D4FF; height: 100%;"></div>
                    </div>
                </div>

                <!-- Phasen-Vorteile & Schluessel zum Sieg -->
                <div style="display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 14px; margin-bottom: 16px;">
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 14px;">
                        <div style="color: #38BDF8; font-weight: 700; font-size: 12px; margin-bottom: 6px;">⚖️ PHASEN-SCHLÜSSEL IM DIREKTEN VERGLEICH</div>
                        <div style="font-size: 12px; line-height: 1.7; color: #E2E8F0;">
                            • <b>Opening (Start 1–3):</b> {ai_h2h['phase_opening']}<br>
                            • <b>Mid-Game (Visits 4–6):</b> {ai_h2h['phase_mid']}<br>
                            • <b>Finish (Rest ≤ 170):</b> {ai_h2h['phase_finish']}
                        </div>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 14px;">
                        <div style="color: #FBBF24; font-weight: 700; font-size: 12px; margin-bottom: 6px;">🔑 SCHLÜSSEL ZUM MATCH-SIEG</div>
                        <div style="font-size: 12px; line-height: 1.6; color: #E2E8F0;">
                            • <b style="color: #00D4FF;">{get_short_name(cmp_a_name)}:</b> {ai_h2h['key_a']}<br>
                            • <b style="color: #F59E0B;">{get_short_name(cmp_b_name)}:</b> {ai_h2h['key_b']}
                        </div>
                    </div>
                </div>

                <!-- Duell-Psychologie: 2-Spalten Head-to-Head Vergleich -->
                <div style="background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 14px 16px;">
                    <div style="color: #38BDF8; font-size: 11px; font-weight: 800; letter-spacing: 1px; margin-bottom: 12px;">
                        🧠 DUELL-PSYCHOLOGIE: DIREKTE VERHALTENS-GEGENÜBERSTELLUNG
                    </div>
                    
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <!-- Zeile 1: Bounce-Back -->
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 10px 14px;">
                            <div style="color: #38BDF8; font-weight: 700; font-size: 11px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                                <span>🔄 REAKTION AUF FEHLWÜRFE (BOUNCE-BACK)</span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px; line-height: 1.5;">
                                <div style="border-left: 2px solid #00D4FF; padding-left: 8px;">
                                    <div style="color: #00D4FF; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_a_name)} ({ai_h2h['stat_bb_a']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_bb_a']}</div>
                                </div>
                                <div style="border-left: 2px solid #F59E0B; padding-left: 8px;">
                                    <div style="color: #F59E0B; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_b_name)} ({ai_h2h['stat_bb_b']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_bb_b']}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Zeile 2: Nervenstärke -->
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(244, 63, 94, 0.15); border-radius: 8px; padding: 10px 14px;">
                            <div style="color: #F43F5E; font-weight: 700; font-size: 11px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                                <span>🔥 NERVENSTÄRKE BEI GEGNER-CHECKOUT (REST ≤ 170)</span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px; line-height: 1.5;">
                                <div style="border-left: 2px solid #00D4FF; padding-left: 8px;">
                                    <div style="color: #00D4FF; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_a_name)} ({ai_h2h['stat_pr_a']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_pr_a']}</div>
                                </div>
                                <div style="border-left: 2px solid #F59E0B; padding-left: 8px;">
                                    <div style="color: #F59E0B; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_b_name)} ({ai_h2h['stat_pr_b']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_pr_b']}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Zeile 3: Fokus in langen Legs -->
                        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(168, 85, 247, 0.15); border-radius: 8px; padding: 10px 14px;">
                            <div style="color: #A855F7; font-weight: 700; font-size: 11px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                                <span>⏱️ FOKUS & AUSDAUER IM WEITEREN LEG-VERLAUF (VISIT 7+)</span>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px; line-height: 1.5;">
                                <div style="border-left: 2px solid #00D4FF; padding-left: 8px;">
                                    <div style="color: #00D4FF; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_a_name)} ({ai_h2h['stat_fc_a']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_fc_a']}</div>
                                </div>
                                <div style="border-left: 2px solid #F59E0B; padding-left: 8px;">
                                    <div style="color: #F59E0B; font-weight: 700; font-size: 11px; margin-bottom: 2px;">{get_short_name(cmp_b_name)} ({ai_h2h['stat_fc_b']})</div>
                                    <div style="color: #E2E8F0;">{ai_h2h['txt_fc_b']}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """)

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. Leg-Phasen Duell (Opening vs. Mid vs. Finish)
            st.subheader("📊 2. Leg-Phasen Duell", help="Wer dominiert die Startphase, wer das Mittelspiel und wer den Finishbereich?")
            ph_d1, ph_d2, ph_d3 = st.columns(3)
            
            with ph_d1:
                op_a = ana_a['phases']['opening']['average']
                op_b = ana_b['phases']['opening']['average']
                win_op = "👑 " + (cmp_a_name if op_a > op_b else cmp_b_name)
                w_c = "#00D4FF" if op_a > op_b else "#F59E0B"
                st.markdown(f"""
                <div class="mockup-card" style="border-left: 4px solid #38BDF8;">
                    <div class="card-title"><span style="color: #38BDF8;">🏹 OPENING (Visits 1–3)</span><span style="font-size: 12px; color: {w_c}; font-weight: 700;">{win_op}</span></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 10px 0;">
                        <div><span style="font-size: 13px; color: #00D4FF; font-weight: 700;">{get_short_name(cmp_a_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {op_a:.1f}</b></div>
                        <div><span style="font-size: 13px; color: #F59E0B; font-weight: 700;">{get_short_name(cmp_b_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {op_b:.1f}</b></div>
                    </div>
                    <div style="color: #94A3B8; font-size: 12px; line-height: 1.8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">
                        • Streuung: <b style="color: #00D4FF;">±{ana_a['phases']['opening']['volatility_std']:.1f}</b> vs <b style="color: #F59E0B;">±{ana_b['phases']['opening']['volatility_std']:.1f}</b><br>
                        • 100+ Rate: <b style="color: #00D4FF;">{ana_a['phases']['opening']['rate_100_pct']:.1f}%</b> vs <b style="color: #F59E0B;">{ana_b['phases']['opening']['rate_100_pct']:.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with ph_d2:
                mid_a = ana_a['phases']['mid_game']['average']
                mid_b = ana_b['phases']['mid_game']['average']
                win_mid = "👑 " + (cmp_a_name if mid_a > mid_b else cmp_b_name)
                w_c = "#00D4FF" if mid_a > mid_b else "#F59E0B"
                st.markdown(f"""
                <div class="mockup-card" style="border-left: 4px solid #818CF8;">
                    <div class="card-title"><span style="color: #818CF8;">⚔️ MID GAME (Visits 4–6)</span><span style="font-size: 12px; color: {w_c}; font-weight: 700;">{win_mid}</span></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 10px 0;">
                        <div><span style="font-size: 13px; color: #00D4FF; font-weight: 700;">{get_short_name(cmp_a_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {mid_a:.1f}</b></div>
                        <div><span style="font-size: 13px; color: #F59E0B; font-weight: 700;">{get_short_name(cmp_b_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {mid_b:.1f}</b></div>
                    </div>
                    <div style="color: #94A3B8; font-size: 12px; line-height: 1.8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">
                        • Streuung: <b style="color: #00D4FF;">±{ana_a['phases']['mid_game']['volatility_std']:.1f}</b> vs <b style="color: #F59E0B;">±{ana_b['phases']['mid_game']['volatility_std']:.1f}</b><br>
                        • 100+ Rate: <b style="color: #00D4FF;">{ana_a['phases']['mid_game']['rate_100_pct']:.1f}%</b> vs <b style="color: #F59E0B;">{ana_b['phases']['mid_game']['rate_100_pct']:.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with ph_d3:
                fin_a = ana_a['phases']['finish']['average']
                fin_b = ana_b['phases']['finish']['average']
                win_fin = "👑 " + (cmp_a_name if fin_a > fin_b else cmp_b_name)
                w_c = "#00D4FF" if fin_a > fin_b else "#F59E0B"
                st.markdown(f"""
                <div class="mockup-card" style="border-left: 4px solid #34D399;">
                    <div class="card-title"><span style="color: #34D399;">🏁 FINISH (Rest ≤ 170)</span><span style="font-size: 12px; color: {w_c}; font-weight: 700;">{win_fin}</span></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 10px 0;">
                        <div><span style="font-size: 13px; color: #00D4FF; font-weight: 700;">{get_short_name(cmp_a_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {fin_a:.1f}</b></div>
                        <div><span style="font-size: 13px; color: #F59E0B; font-weight: 700;">{get_short_name(cmp_b_name)}:</span> <b style="font-size: 24px; color: #FFFFFF;">Ø {fin_b:.1f}</b></div>
                    </div>
                    <div style="color: #94A3B8; font-size: 12px; line-height: 1.8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">
                        • Streuung: <b style="color: #00D4FF;">±{ana_a['phases']['finish']['volatility_std']:.1f}</b> vs <b style="color: #F59E0B;">±{ana_b['phases']['finish']['volatility_std']:.1f}</b><br>
                        • 100+ Rate: <b style="color: #00D4FF;">{ana_a['phases']['finish']['rate_100_pct']:.1f}%</b> vs <b style="color: #F59E0B;">{ana_b['phases']['finish']['rate_100_pct']:.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 5. Gemeinsame Performance-Kurve
            st.subheader("📈 3. Gemeinsame Performance-Kurve (Visit 1 bis N)", help="Direkter Vergleich der Scoring-Power Wurf für Wurf im Leg-Verlauf.")
            curve_a = ana_a['curve_data']
            curve_b = ana_b['curve_data']
            
            all_visits_keys = sorted(list(set([c['visit_order'] for c in curve_a] + [c['visit_order'] for c in curve_b])))
            if all_visits_keys:
                dict_a = {c['visit_order']: c['average'] for c in curve_a}
                dict_b = {c['visit_order']: c['average'] for c in curve_b}
                
                chart_h2h_df = pd.DataFrame({
                    'Aufnahme': [f"Visit {k}" for k in all_visits_keys],
                    f"{cmp_a_name}": [dict_a.get(k, np.nan) for k in all_visits_keys],
                    f"{cmp_b_name}": [dict_b.get(k, np.nan) for k in all_visits_keys]
                }).set_index('Aufnahme')
                
                col_c_chart, col_c_table = st.columns([2.2, 1.8])
                with col_c_chart:
                    x_labels = [f"Visit {k}" for k in all_visits_keys]
                    y_a = [dict_a.get(k, None) for k in all_visits_keys]
                    y_b = [dict_b.get(k, None) for k in all_visits_keys]
                    fig_h2h = go.Figure()
                    fig_h2h.add_trace(go.Scatter(
                        x=x_labels, y=y_a,
                        mode='lines+markers', name=cmp_a_name,
                        line=dict(color='#00D4FF', width=2.5),
                        marker=dict(size=6)
                    ))
                    fig_h2h.add_trace(go.Scatter(
                        x=x_labels, y=y_b,
                        mode='lines+markers', name=cmp_b_name,
                        line=dict(color='#F59E0B', width=2.5),
                        marker=dict(size=6)
                    ))
                    fig_h2h.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,23,42,0.6)',
                        margin=dict(l=30, r=20, t=20, b=30),
                        xaxis=dict(
                            categoryorder='array',
                            categoryarray=x_labels,
                            gridcolor='rgba(255,255,255,0.08)',
                            tickfont=dict(color='#94A3B8')
                        ),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.08)', tickfont=dict(color='#94A3B8')),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#FFFFFF"))
                    )
                    st.plotly_chart(fig_h2h, use_container_width=True)
                with col_c_table:
                    comp_curve_rows = []
                    for k in all_visits_keys:
                        av_a = dict_a.get(k, None)
                        av_b = dict_b.get(k, None)
                        if av_a is not None and av_b is not None:
                            v_w = f"👑 {get_short_name(cmp_a_name)}" if av_a > av_b else (f"👑 {get_short_name(cmp_b_name)}" if av_b > av_a else "Gleich")
                        else:
                            v_w = "-"
                        comp_curve_rows.append({
                            'Aufnahme': f"Visit {k}",
                            f'Ø {get_short_name(cmp_a_name)}': f"{av_a:.1f}" if av_a is not None else "-",
                            f'Ø {get_short_name(cmp_b_name)}': f"{av_b:.1f}" if av_b is not None else "-",
                            'Vorteil': v_w
                        })
                    st.dataframe(pd.DataFrame(comp_curve_rows), use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 6. Score-Verteilung & Highscore-Raten
            st.subheader("🎯 4. Highscore-Raten im Vergleich (pro 100 Visits)", help="Wie viele 60+, 80+, 100+, 140+ und 180er wirft jeder Spieler auf 100 Aufnahmen?")
            t_a = ana_a['dist_data']['thresholds']
            t_b = ana_b['dist_data']['thresholds']
            
            rates_rows = []
            for th_key in ['60+', '80+', '100+', '140+', '180']:
                ra = t_a.get(th_key, {}).get('rate_per_100', 0.0)
                rb = t_b.get(th_key, {}).get('rate_per_100', 0.0)
                cnt_a = t_a.get(th_key, {}).get('count', 0)
                cnt_b = t_b.get(th_key, {}).get('count', 0)
                if ra > rb:
                    w = f"👑 {get_short_name(cmp_a_name)} (+{ra-rb:.1f})"
                elif rb > ra:
                    w = f"👑 {get_short_name(cmp_b_name)} (+{rb-ra:.1f})"
                else:
                    w = "Gleichstand"
                rates_rows.append({
                    'Schwellenwert': th_key,
                    f'{get_short_name(cmp_a_name)} (Anzahl)': f"{cnt_a}x ({ra:.1f}/100)",
                    f'{get_short_name(cmp_b_name)} (Anzahl)': f"{cnt_b}x ({rb:.1f}/100)",
                    'Besserer Wert': w
                })
            st.dataframe(pd.DataFrame(rates_rows), use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 7. Direkte Duelle (Match-Historie)
            st.subheader("📋 5. Direkte Duelle & Match-Historie (Head-to-Head)", help="Alle Ligaspiele, in denen diese beiden Spieler direkt gegeneinander angetreten sind.")
            all_m = get_all_analytics_matches(season=cmp_filter_season)
            direct_matches = all_m[
                ((all_m['player_a_name'].str.contains(cmp_a_name, case=False)) & (all_m['player_b_name'].str.contains(cmp_b_name, case=False))) |
                ((all_m['player_a_name'].str.contains(cmp_b_name, case=False)) & (all_m['player_b_name'].str.contains(cmp_a_name, case=False)))
            ]
            
            if direct_matches.empty:
                st.info(f"ℹ️ In der Saison **{cmp_season_sel}** liegt bisher kein direktes Einzelmatch zwischen **{cmp_a_name}** und **{cmp_b_name}** vor.")
            else:
                for _, dm_row in direct_matches.iterrows():
                    dmid = int(dm_row['id'])
                    dm_nr = int(dm_row.get('match_nr', 0) or 0)
                    dm_disp = f"#{dm_nr}" if dm_nr > 0 else f"ID {dmid}"
                    dm_pa = str(dm_row['player_a_name'])
                    dm_pb = str(dm_row['player_b_name'])
                    dm_dt = pd.to_datetime(dm_row['match_date']).strftime('%d.%m.%Y')
                    dmdet = get_analytics_match_details(dmid)
                    dlegs = dmdet.get('legs', []) if dmdet else []
                    dw_a = sum(1 for l in dlegs if (l.get('winner_player_id') == dmdet.get('player_a_id') and l.get('winner_player_id', 0) > 0) or (int(l.get('checkout_a', 0) or 0) > 0))
                    dw_b = len(dlegs) - dw_a if dlegs else 0
                    with st.expander(f"🎯 Direktes Match {dm_disp} | {dm_dt} | {dm_pa} vs {dm_pb} (Ergebnis: {dw_a}:{dw_b})", expanded=True):
                        st.write(f"Matchdetails ID {dmid}: {len(dlegs)} Legs gespielt.")

render_impressum_footer()
