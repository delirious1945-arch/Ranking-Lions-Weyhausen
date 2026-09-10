import os
import sys
import importlib
import streamlit as st
import datetime
import sqlite3

# Sicherstellen, dass das Root-Verzeichnis im Pfad liegt
_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from utils import apply_custom_theme, require_admin, render_impressum_footer
from database import get_players, add_match, add_doubles_special, add_doubles_match, get_available_seasons

import analytics.data_access
if not hasattr(analytics.data_access, 'scan_main_directory_for_spieltage'):
    importlib.reload(analytics.data_access)

from analytics.data_access import (
    save_full_analytics_match,
    scan_main_directory_for_spieltage,
    batch_import_spieltage,
    import_analyzer_csv_data,
    validate_match_legs_plausibility
)

st.set_page_config(page_title="Lions League - Eingabe", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_admin()

st.title("📝 Data Entry / Eingabemaske")
st.caption("Erfassung von Einzel-Spielberichten und Doppel-Specials durch den Admin.")

# Saison-Auswahl für neue Spielberichte
available_seasons = get_available_seasons()
col_seas1, col_seas2 = st.columns([2, 2])
with col_seas1:
    season_options = available_seasons + ["➕ Neue Saison anlegen..."]
    selected_season_choice = st.selectbox("📅 Saison für diesen Spielbericht", season_options, index=0, key="entry_season_choice")
    if selected_season_choice == "➕ Neue Saison anlegen...":
        entry_season = st.text_input("Neue Saisonbezeichnung (z. B. 2027/2028)", value="2027/2028", key="custom_season_input").strip()
    else:
        entry_season = selected_season_choice
with col_seas2:
    st.markdown(f"""
    <div style="background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.3); border-radius: 10px; padding: 10px 14px; margin-top: 18px;">
        <span style="font-size: 13px; color: #94A3B8;">Aktive Erfassungs-Saison: </span>
        <span style="font-size: 16px; font-weight: 800; color: #00D4FF;">{entry_season}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Offizielle Gegner-Listen laut Liga-Einteilung 2026 (Exklusive Lions Weyhausen A & B)
STAFFEL_7_OPPONENTS = [
    "Bromer Burglöwen B",
    "DC Gamsen 96 B",
    "DC Old No.7 Sülfeld D",
    "DC Wolfsjäger C",
    "Erst zart dann Dart A",
    "Riederockets MTV Vollbüttel B",
    "TSV Rethen D",
    "VfB Bullseye Fallersleben B",
    "VfL Wolfsburg e.V. F"
]

STAFFEL_11_OPPONENTS = [
    "1.DC Didderse A",
    "Aller-Oker-Darter A",
    "Dart Kongs Triangel B",
    "FireDarter C",
    "HSV Isedarter B",
    "Mad House Fallersleben E",
    "RaZa Darts A",
    "VfL Wettmershagen B"
]

tab_single, tab_analytics, tab_csv_import, tab_double_match, tab_double_special = st.tabs([
    "🎯 Einzel-Schnellbericht", 
    "🚀 Detailliertes Match (DAE)", 
    "📥 CSV-Import (DAE & Liga)",
    "👥 Doppel-Spielbericht", 
    "🤝 Doppel-Special (Bonus)"
])

# ----------------------------------------------------
# TAB 1: EINZEL-SPIELBERICHT
# ----------------------------------------------------
with tab_single:
    players_df = get_players()
    if not players_df.empty:
        players_df = players_df[players_df['team'].isin(['A-Team', 'B-Team'])].copy()
    if players_df.empty:
        st.warning("⚠️ Bitte registriere zuerst Spieler unter 'Einstellungen'.")
        st.stop()

    players_df['team_prefix'] = players_df['team'].apply(lambda x: "🦁 " if x == "A-Team" else "🐯 ")
    players_df['display_name'] = players_df['team_prefix'] + players_df['name'] + " (" + players_df['team'] + ")"

    # DYNAMISCHES MATCHMAKING: Spieler-Auswahl AUSSERHALB des Formulars, damit Streamlit bei Änderung sofort neu lädt!
    st.subheader("1. Spieler & Spielauswahl")
    col_p_sel, col_t_info = st.columns([2, 1])
    with col_p_sel:
        selected_player_disp = st.selectbox(
            "Spieler auswählen",
            players_df['display_name'].tolist(),
            key="active_match_player_select"
        )
    
    selected_player_row = players_df[players_df['display_name'] == selected_player_disp].iloc[0]
    player_id = int(selected_player_row['id'])
    player_name = selected_player_row['name']
    player_team = selected_player_row['team']
    
    # Exakte Gegner-Zuordnung je nach Mannschaft des ausgewählten Spielers!
    if player_team == "A-Team":
        opponents_list = STAFFEL_7_OPPONENTS
        staffel_label = "2. Kreisklasse Staffel 07 (A-Team)"
    else:
        opponents_list = STAFFEL_11_OPPONENTS
        staffel_label = "2. Kreisklasse Staffel 11 (B-Team)"

    with col_t_info:
        st.markdown(f"""
        <div style="background: rgba(0,212,255,0.1); border: 1px solid #00D4FF; border-radius: 12px; padding: 10px; text-align: center; margin-top: 10px;">
            <div style="font-size: 13px; color: #00D4FF; font-weight: 700;">ZUTREFFENDE STAFFEL</div>
            <div style="font-size: 16px; font-weight: 800; color: #FFFFFF;">{staffel_label}</div>
        </div>
        """, unsafe_allow_html=True)

    is_two_singles = st.checkbox("✌️ Der Spieler hat heute 2 Einzel absolviert (2. Einzel freischalten)", value=False)

    st.divider()

    with st.form("entry_form_single"):
        st.subheader("2. Spielberichtsdaten eintragen")
        
        c1, c2 = st.columns(2)
        with c1:
            match_date = st.date_input("Spieldatum", datetime.date.today(), key="m1_date")
        with c2:
            opponent = st.selectbox(f"Gegnerische Mannschaft ({staffel_label})", opponents_list, key="m1_opp")
            
        st.markdown("#### Leg-Ergebnis (Best of 5)")
        lc1, lc2 = st.columns(2)
        with lc1:
            legs_won = st.number_input("Gewonnene Legs", min_value=0, max_value=3, value=3, key="m1_lw")
        with lc2:
            legs_lost = st.number_input("Verlorene Legs", min_value=0, max_value=3, value=1, key="m1_ll")
            
        st.markdown("#### Average-Werte")
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            avg_total = st.number_input("Gesamt Average", min_value=0.0, max_value=150.0, value=48.5, step=0.1, key="m1_avg_t")
        with ac2:
            avg_9 = st.number_input("Durchschnitts-Average 9 Darts", min_value=0.0, max_value=150.0, value=52.0, step=0.1, key="m1_avg_9")
        with ac3:
            avg_18 = st.number_input("Durchschnitts-Average 18 Darts", min_value=0.0, max_value=150.0, value=50.0, step=0.1, key="m1_avg_18")
            
        st.markdown("#### High Scores")
        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1: s_80 = st.number_input("80+ Scores", min_value=0, value=4, key="m1_s80")
        with hc2: s_100 = st.number_input("100+ Scores", min_value=0, value=2, key="m1_s100")
        with hc3: s_140 = st.number_input("140+ Scores", min_value=0, value=1, key="m1_s140")
        with hc4: s_180 = st.number_input("180er", min_value=0, value=0, key="m1_s180")
            
        st.markdown("#### Highlights & Specials")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            high_finishes = st.number_input("Höchstes Finish (z.B. 120)", min_value=0, max_value=170, value=0, key="m1_hf")
        with sc2:
            short_legs = st.number_input("Short Legs (≤18 Darts)", min_value=0, value=0, key="m1_sl")
        with sc3:
            specials_count = st.number_input("Specials Anz. (Bonus +3 Pkt)", min_value=0, value=0, key="m1_sp")
            
        # Optionales 2. Einzel
        match_data_2 = None
        if is_two_singles:
            st.divider()
            st.subheader(f"Spielbericht #2 für {player_name}")
            c2_1, c2_2 = st.columns(2)
            with c2_1:
                match_date_2 = st.date_input("Spieldatum (Einzel 2)", datetime.date.today(), key="m2_date")
            with c2_2:
                opponent_2 = st.selectbox(f"Gegnerische Mannschaft (Einzel 2)", opponents_list, key="m2_opp")
                
            st.markdown("#### Leg-Ergebnis (Einzel 2)")
            lc2_1, lc2_2 = st.columns(2)
            with lc2_1: legs_won_2 = st.number_input("Gewonnene Legs (E2)", min_value=0, max_value=3, value=3, key="m2_lw")
            with lc2_2: legs_lost_2 = st.number_input("Verlorene Legs (E2)", min_value=0, max_value=3, value=0, key="m2_ll")
                
            st.markdown("#### Average-Werte (Einzel 2)")
            ac2_1, ac2_2, ac2_3 = st.columns(3)
            with ac2_1: avg_t2 = st.number_input("Gesamt Avg (E2)", min_value=0.0, max_value=150.0, value=50.0, step=0.1, key="m2_avg_t")
            with ac2_2: avg_9_2 = st.number_input("9-Dart Avg (E2)", min_value=0.0, max_value=150.0, value=54.0, step=0.1, key="m2_avg_9")
            with ac2_3: avg_18_2 = st.number_input("18-Dart Avg (E2)", min_value=0.0, max_value=150.0, value=51.5, step=0.1, key="m2_avg_18")
                
            st.markdown("#### High Scores (Einzel 2)")
            hc2_1, hc2_2, hc2_3, hc2_4 = st.columns(4)
            with hc2_1: s80_2 = st.number_input("80+ (E2)", min_value=0, value=3, key="m2_s80")
            with hc2_2: s100_2 = st.number_input("100+ (E2)", min_value=0, value=3, key="m2_s100")
            with hc2_3: s140_2 = st.number_input("140+ (E2)", min_value=0, value=1, key="m2_s140")
            with hc2_4: s180_2 = st.number_input("180er (E2)", min_value=0, value=0, key="m2_s180")
                
            st.markdown("#### Highlights & Specials (Einzel 2)")
            sc2_1, sc2_2, sc2_3 = st.columns(3)
            with sc2_1: hf_2 = st.number_input("High Finish (E2)", min_value=0, max_value=170, value=0, key="m2_hf")
            with sc2_2: sl_2 = st.number_input("Short Legs (E2)", min_value=0, value=0, key="m2_sl")
            with sc2_3: sp_2 = st.number_input("Specials Anz. (E2)", min_value=0, value=0, key="m2_sp")
                
            match_data_2 = {
                'player_id': player_id,
                'match_date': match_date_2.strftime('%Y-%m-%d'),
                'opponent': opponent_2,
                'legs_won': legs_won_2,
                'legs_lost': legs_lost_2,
                'avg_total': avg_t2,
                'avg_9': avg_9_2,
                'avg_18': avg_18_2,
                'scores_80': s80_2,
                'scores_100': s100_2,
                'scores_140': s140_2,
                'scores_180': s180_2,
                'high_finishes': hf_2,
                'short_legs': sl_2,
                'specials_count': sp_2,
                'season': entry_season
            }

        submitted = st.form_submit_button("🚀 Spielbericht(e) Speichern", use_container_width=True)
        
        if submitted:
            m1_data = {
                'player_id': player_id,
                'match_date': match_date.strftime('%Y-%m-%d'),
                'opponent': opponent,
                'legs_won': legs_won,
                'legs_lost': legs_lost,
                'avg_total': avg_total,
                'avg_9': avg_9,
                'avg_18': avg_18,
                'scores_80': s_80,
                'scores_100': s_100,
                'scores_140': s_140,
                'scores_180': s_180,
                'high_finishes': high_finishes,
                'short_legs': short_legs,
                'specials_count': specials_count,
                'season': entry_season
            }
            val_m1 = validate_match_legs_plausibility(legs_won, legs_lost, best_of=5)
            if not val_m1['is_valid']:
                st.warning(val_m1['warning'])
                
            add_match(m1_data)
            if is_two_singles and match_data_2:
                val_m2 = validate_match_legs_plausibility(legs_won_2, legs_lost_2, best_of=5)
                if not val_m2['is_valid']:
                    st.warning(val_m2['warning'])
                add_match(match_data_2)
                st.success(f"✅ Beide Einzel-Spielberichte für {player_name} wurden erfolgreich gespeichert!")
            else:
                st.success(f"✅ Einzel-Spielbericht für {player_name} ({opponent}) erfolgreich gespeichert!")

# ----------------------------------------------------
# TAB 2: DETAILLIERTES MATCH (ANALYTICS ENGINE)
# ----------------------------------------------------
with tab_analytics:
    st.subheader("🚀 Detailliertes Match erfassen (Legs & Aufnahmen)")
    st.markdown("""
    <div style="background: rgba(0,212,255,0.08); border: 1px solid #00D4FF; border-radius: 12px; padding: 12px 18px; margin-bottom: 18px;">
        <b style="color: #00D4FF; font-size: 15px;">💡 Keine doppelte Dateneingabe:</b><br>
        <span style="color: #CBD5E1; font-size: 14px;">
            Wenn du hier die Visits pro Leg erfasst, berechnet die Engine <b>alle Ligawerte (Average, 9-Dart-Avg, 18-Dart-Avg, 80+, 100+, 140+, 180er, High Finish) automatisch</b> 
            und trägt das Spiel auf Wunsch direkt in die offizielle Lions-Rangliste ein!
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. SPIEL- & KOPFDATEN (2K DARTS METADATEN)
    col_m_p1, col_m_p2, col_m_set = st.columns([1.5, 1.5, 1])
    with col_m_p1:
        p_names = players_df['name'].tolist()
        an_p1_name = st.selectbox("Spieler A (Lions Weyhausen)", p_names, key="an_p1_select")
        an_p1_id = int(players_df[players_df['name'] == an_p1_name].iloc[0]['id'])
        
    with col_m_p2:
        opp_type = st.radio("Gegner-Typ", ["Aus Lions Kader", "Freier Gegnername"], horizontal=True, key="an_opp_type")
        if opp_type == "Aus Lions Kader":
            p2_options = [p for p in p_names if p != an_p1_name]
            an_p2_name = st.selectbox("Spieler B", p2_options, key="an_p2_select")
            an_p2_id = int(players_df[players_df['name'] == an_p2_name].iloc[0]['id'])
        else:
            an_p2_name = st.text_input("Gegnername (z. B. Gastspieler / Ligagegner)", value="Gastspieler", key="an_guest_name").strip()
            an_p2_id = 0
            
    with col_m_set:
        an_date = st.date_input("Spieldatum", datetime.date.today(), key="an_match_date")
        an_location = st.selectbox("Spielort", ["Heim", "Auswärts"], key="an_loc_select")
        
    # Zusätzliche 2K Darts Spieldaten (Dauer, Start, Ende, Board, Spielnummer)
    with st.expander("⏱️ 2K Darts Spieldaten (Dauer, Startzeit, Endzeit & Board)", expanded=True):
        c_tim1, c_tim2, c_tim3, c_tim4, c_tim5 = st.columns(5)
        with c_tim1:
            an_duration = st.number_input("Dauer (Minuten)", min_value=1, max_value=240, value=14, step=1, key="an_duration")
        with c_tim2:
            an_start_time = st.text_input("Spielstart (Uhrzeit)", value="20:49", key="an_start_time", placeholder="z.B. 20:49")
        with c_tim3:
            an_end_time = st.text_input("Spielende (Uhrzeit)", value="21:04", key="an_end_time", placeholder="z.B. 21:04")
        with c_tim4:
            an_board = st.number_input("Board-Nr.", min_value=1, max_value=32, value=1, step=1, key="an_board")
        with c_tim5:
            an_match_nr = st.number_input("Spielnummer", min_value=1, max_value=100, value=7, step=1, key="an_match_nr")

    st.markdown("#### 🎯 2K Darts Leg-Erfassung (Beide Spieler)")
    st.caption("Erfasse beide Spieler Aufnahme für Aufnahme, um den gegnerischen Druck und die Match-Dynamik exakt zu analysieren.")
    num_legs = st.number_input("Anzahl gespielter Legs", min_value=1, max_value=15, value=3, step=1, key="an_num_legs")
    
    legs_input_data = []
    
    def parse_visits_str(v_string, player_id):
        if not v_string or not v_string.strip():
            return []
        parts = v_string.replace(';', ',').replace('\n', ',').replace(' ', ',').split(',')
        visits = []
        cur_rest = 501
        for p in parts:
            clean = p.strip()
            if clean.isdigit():
                sc = int(clean)
                cur_rest = max(cur_rest - sc, 0)
                visits.append({
                    'score': sc,
                    'rest_score': cur_rest,
                    'player_id': player_id
                })
        return visits

    for l_num in range(1, int(num_legs) + 1):
        with st.expander(f"🎯 Leg {l_num}", expanded=(l_num <= 3)):
            col_l_starter, col_l_winner, col_l_brk = st.columns([1.5, 1.5, 1])
            with col_l_starter:
                l_starter_name = st.selectbox(f"Startrecht Leg {l_num}", [an_p1_name, an_p2_name], key=f"an_l_{l_num}_starter")
                l_starter_id = an_p1_id if l_starter_name == an_p1_name else an_p2_id
            with col_l_winner:
                l_winner_name = st.selectbox(f"Gewinner Leg {l_num}", [an_p1_name, an_p2_name], key=f"an_l_{l_num}_winner")
                l_winner_id = an_p1_id if l_winner_name == an_p1_name else an_p2_id
            with col_l_brk:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                l_is_break = st.checkbox(f"Break? (Anwurf abgenommen)", value=(l_starter_id != l_winner_id), key=f"an_l_{l_num}_brk")
                
            # Darts & Checkouts Eingabezeile für BEIDE Spieler
            c_d_a, c_co_a, c_d_b, c_co_b = st.columns(4)
            with c_d_a:
                l_darts_a = st.number_input(f"Darts ({an_p1_name})", min_value=9, max_value=60, value=29 if l_num==1 else (36 if l_num==2 else 30), step=1, key=f"an_darts_a_{l_num}")
            with c_co_a:
                l_co_a = st.number_input(f"Checkout ({an_p1_name})", min_value=0, max_value=170, value=20 if l_num==1 else (2 if l_num==2 else 9), step=1, key=f"an_co_a_{l_num}")
            with c_d_b:
                l_darts_b = st.number_input(f"Darts ({an_p2_name})", min_value=0, max_value=60, value=27 if l_num==1 else 33, step=1, key=f"an_darts_b_{l_num}")
            with c_co_b:
                l_co_b = st.number_input(f"Checkout ({an_p2_name})", min_value=0, max_value=170, value=0, step=1, key=f"an_co_b_{l_num}")
                
            col_in_a, col_in_b = st.columns(2)
            with col_in_a:
                v_str_a = st.text_area(
                    f"Aufnahmen {an_p1_name} (kommagetrennt aus 2K Scoreboard)",
                    key=f"an_v_a_{l_num}",
                    value="45, 38, 40, 100, 83, 59, 27, 49, 40, 20" if l_num==1 else ("60, 140, 60, 38, 43, 60, 28, 70, 0, 0, 0, 2" if l_num==2 else "24, 40, 28, 95, 95, 30, 140, 31, 9, 9"),
                    height=70,
                    placeholder="45, 38, 40, 100, 83, 59, 27, 49, 40, 20"
                )
            with col_in_b:
                v_str_b = st.text_area(
                    f"Aufnahmen {an_p2_name} (kommagetrennt aus 2K Scoreboard)",
                    key=f"an_v_b_{l_num}",
                    value="54, 30, 121, 60, 45, 26, 18, 11, 54" if l_num==1 else ("25, 41, 24, 50, 75, 10, 77, 9, 56, 41, 57" if l_num==2 else "11, 63, 26, 31, 8, 45, 26, 38, 75"),
                    height=70,
                    placeholder="54, 30, 121, 60, 45, 26, 18, 11, 54"
                )
                
            parsed_a = parse_visits_str(v_str_a, an_p1_id)
            parsed_b = parse_visits_str(v_str_b, an_p2_id)
            
            # Gegenseitige Restscores für präzise Druckanalyse verknüpfen
            for i, va in enumerate(parsed_a):
                opp_idx = i if l_starter_id == an_p1_id else (i - 1)
                if 0 <= opp_idx < len(parsed_b):
                    va['opponent_rest'] = parsed_b[opp_idx]['rest_score']
                else:
                    va['opponent_rest'] = 501
                    
            for i, vb in enumerate(parsed_b):
                opp_idx = (i - 1) if l_starter_id == an_p1_id else i
                if 0 <= opp_idx < len(parsed_a):
                    vb['opponent_rest'] = parsed_a[opp_idx]['rest_score']
                else:
                    vb['opponent_rest'] = 501
            
            # Live-Berechnung des Leg-Averages nach 2K Darts Formel
            if parsed_a:
                pts_a = sum(v['score'] for v in parsed_a)
                if l_darts_a > 0:
                    leg_avg_a = (pts_a / l_darts_a) * 3
                else:
                    leg_avg_a = pts_a / len(parsed_a)
                last_rest_a = parsed_a[-1]['rest_score']
                st.markdown(f"""
                <div style="background: rgba(0,212,255,0.06); border: 1px solid rgba(0,212,255,0.3); border-radius: 8px; padding: 6px 12px; margin-top: 4px; font-size: 13px;">
                    🦁 <b>{an_p1_name}:</b> {len(parsed_a)} Aufnahmen • {l_darts_a} Darts • <b>Leg-Average: Ø {leg_avg_a:.1f}</b> • Rest: <b>{last_rest_a}</b> {'(🏁 Leg-Finish mit ' + str(l_co_a) + ')' if last_rest_a == 0 or l_co_a > 0 else ''}
                </div>
                """, unsafe_allow_html=True)
                
            if parsed_b:
                pts_b = sum(v['score'] for v in parsed_b)
                if l_darts_b > 0:
                    leg_avg_b = (pts_b / l_darts_b) * 3
                else:
                    leg_avg_b = pts_b / len(parsed_b)
                last_rest_b = parsed_b[-1]['rest_score']
                st.caption(f"🎯 **{an_p2_name}:** {len(parsed_b)} Aufnahmen • {l_darts_b} Darts • Leg-Average: Ø {leg_avg_b:.1f} • Rest: {last_rest_b}")
                
            legs_input_data.append({
                'leg_num': l_num,
                'starter_player_id': l_starter_id,
                'winner_player_id': l_winner_id,
                'darts_thrown_a': l_darts_a,
                'darts_thrown_b': l_darts_b,
                'checkout_a': l_co_a,
                'checkout_b': l_co_b,
                'is_break': l_is_break,
                'visits_a': parsed_a,
                'visits_b': parsed_b
            })
            
    st.markdown("<br>", unsafe_allow_html=True)
    col_sub_check, col_sub_btn = st.columns([2, 1.5])
    with col_sub_check:
        sync_to_league = st.checkbox("✅ Automatisch in die offizielle Lions League Rangliste ('matches') übernehmen", value=True, key="an_sync_league")
        st.caption("Berechnet automatisch Averages, 80+, 100+, 140+, 180er und High Finish.")
        
    with col_sub_btn:
        save_an_match = st.button("🚀 Detailliertes Match speichern", type="primary", use_container_width=True)
        
    if save_an_match:
        total_v_a = sum(len(l['visits_a']) for l in legs_input_data)
        if total_v_a == 0:
            st.error("⚠️ Bitte trage mindestens für ein Leg Aufnahmen für Spieler A ein.")
        else:
            wins_a = sum(1 for l in legs_input_data if l['winner_player_id'] == an_p1_id)
            wins_b = len(legs_input_data) - wins_a
            match_winner_id = an_p1_id if wins_a > wins_b else an_p2_id
            
            match_meta = {
                'player_a_id': an_p1_id,
                'player_b_id': an_p2_id,
                'player_a_name': an_p1_name,
                'player_b_name': an_p2_name,
                'match_date': an_date.strftime('%Y-%m-%d'),
                'event_name': 'Lions League',
                'round_name': 'Liga-Spiel',
                'best_of_legs': int(num_legs),
                'location': an_location,
                'winner_id': match_winner_id,
                'season': entry_season,
                'duration_min': int(an_duration),
                'start_time': str(an_start_time).strip(),
                'end_time': str(an_end_time).strip(),
                'board_nr': int(an_board),
                'match_nr': int(an_match_nr),
                'round_nr': 1
            }
            
            new_id = save_full_analytics_match(match_meta, legs_input_data, auto_sync_league=sync_to_league)
            if sync_to_league:
                st.success(f"🎉 Match #{new_id} ({an_p1_name} vs. {an_p2_name}) erfolgreich in der Analytics Engine gespeichert UND automatisch in die offizielle Lions-Rangliste übernommen! (Keine Doppeleingabe nötig)")
            else:
                st.success(f"🎉 Match #{new_id} erfolgreich in der Analytics Engine gespeichert!")

# ----------------------------------------------------
# ----------------------------------------------------
# TAB 3: CSV-IMPORT (AUS DART MATCH IMAGE ANALYZER)
# ----------------------------------------------------
with tab_csv_import:
    st.subheader("📥 Intelligenter CSV-Spieltags-Import (DAE & Lions League)")
    st.caption("Wähle einfach den Hauptordner aus – das System durchsucht alle Unterordner, identifiziert automatisch NEUE Daten und importiert sie ohne Duplikate!")
    
    # Standard-Pfad zum Archiv-Ordner des Analyzers
    default_archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Dart_Match_Image_Analyzer", "output", "spieltage"))
    if not os.path.exists(default_archive_dir):
        default_archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Dart_Match_Image_Analyzer", "output"))

    st.markdown("""
    <div style="background: rgba(0,212,255,0.06); border: 1px solid rgba(0,212,255,0.3); border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
        <b style="color: #00D4FF; font-size: 14px;">⚡ Automatische Neu-Erkennung & Deduplizierung:</b><br>
        <span style="color: #CBD5E1; font-size: 13px;">
            Das System gleicht gefundene Spieltage mit der Datenbank ab und erkennt eigenständig, welche Matches <b>neu</b> sind.
            Bestehende Matches werden bei Bedarf sauber aktualisiert – es entstehen <b>keine doppelten Einträge</b>!
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    col_dir_path, col_btn_scan = st.columns([3.2, 1])
    with col_dir_path:
        main_scan_dir = st.text_input(
            "📁 Pfad zum Hauptordner (durchsucht alle Unterordner)",
            value=default_archive_dir if os.path.exists(default_archive_dir) else "",
            key="txt_main_scan_dir"
        )
    with col_btn_scan:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_trigger_scan = st.button("🔍 Hauptordner scannen", type="primary", use_container_width=True, key="btn_trigger_scan")
        
    # Scan-Ergebnisse im Session-State speichern, damit sie beim Interagieren erhalten bleiben
    if btn_trigger_scan or "scanned_spieltage_list" not in st.session_state:
        if main_scan_dir and os.path.exists(main_scan_dir):
            with st.spinner("Scanne Hauptordner und gleiche Matches mit der Datenbank ab..."):
                st.session_state["scanned_spieltage_list"] = scan_main_directory_for_spieltage(main_scan_dir, season=entry_season)
        else:
            st.session_state["scanned_spieltage_list"] = []

    scanned_items = st.session_state.get("scanned_spieltage_list", [])
    
    if not os.path.exists(main_scan_dir):
        st.error(f"❌ Ordnerpfad existiert nicht: {main_scan_dir}")
    elif not scanned_items:
        st.info("ℹ️ Keine Spieltags-Dateien in diesem Hauptordner gefunden. Exportiere zuerst einen Spieltag im Dart Match Image Analyzer!")
    else:
        new_items_count = sum(1 for x in scanned_items if x['is_new_candidate'])
        exists_items_count = len(scanned_items) - new_items_count
        total_m_count = sum(x['total_matches'] for x in scanned_items)
        
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("🟢 Neue Spieltage", f"{new_items_count}", help="Noch nicht in der Datenbank erfasst")
        c_k2.metric("⚪ Bereits vorhanden", f"{exists_items_count}", help="Bereits in der Datenbank synchronisiert")
        c_k3.metric("🎯 Gefundene Matches", f"{total_m_count}", help="Gesamtzahl gefundener Spiele")
        
        st.markdown("##### 📋 Gefundene Spieltage:")
        
        # Tabelle zur Auswahl mit automatischer Vorauswahl für NEUE Spieltage
        selected_indices = []
        for idx, item in enumerate(scanned_items):
            is_new = item['is_new_candidate']
            col_chk, col_sp_info, col_match_cnt, col_badge = st.columns([0.4, 3, 1, 1.3])
            
            with col_chk:
                # Neue Spieltage standardmäßig angehakt, vorhandene abgewählt
                is_selected = st.checkbox(
                    "", 
                    value=is_new, 
                    key=f"chk_sp_{idx}_{item['slug']}",
                    label_visibility="collapsed"
                )
                if is_selected:
                    selected_indices.append(idx)
                    
            with col_sp_info:
                st.markdown(f"**{item['sp_display']}** ({item['date_str']}): `{item['team_display']}` vs. `{item['opp_display']}`")
                st.caption(f"📁 `{os.path.basename(item['dir_path'])}` • Stand: {item['mtime_str']}")
                
            with col_match_cnt:
                st.markdown(f"🎯 **{item['total_matches']} Matches**")
                
            with col_badge:
                if item['status'] == "NEW":
                    st.markdown(f"<span style='color: #10B981; font-weight: bold; font-size: 13px;'>🟢 NEU</span><br><span style='font-size: 11px; color: #94A3B8;'>{item['status_desc']}</span>", unsafe_allow_html=True)
                elif item['status'] == "PARTIAL":
                    st.markdown(f"<span style='color: #F59E0B; font-weight: bold; font-size: 13px;'>🟡 TEILWEISE NEU</span><br><span style='font-size: 11px; color: #94A3B8;'>{item['status_desc']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #64748B; font-weight: bold; font-size: 13px;'>⚪ VORHANDEN</span><br><span style='font-size: 11px; color: #94A3B8;'>{item['status_desc']}</span>", unsafe_allow_html=True)
            st.divider()
            
        sync_league_csv = st.checkbox(
            "✅ Automatisch in die offizielle Lions League Rangliste ('matches' & 'doubles_matches') synchronisieren", 
            value=True, 
            key="chk_sync_batch_league"
        )
        
        btn_label = f"🚀 Alle ausgewählten Spieltage importieren ({len(selected_indices)} von {len(scanned_items)})"
        if st.button(btn_label, type="primary", use_container_width=True, key="btn_run_batch_import", disabled=(len(selected_indices) == 0)):
            items_to_import = [scanned_items[i] for i in selected_indices]
            with st.spinner(f"Importiere {len(items_to_import)} Spieltage..."):
                batch_res = batch_import_spieltage(items_to_import, season=entry_season, sync_league=sync_league_csv)
                
                st.success(f"🎉 Batch-Import abgeschlossen! {batch_res['imported_spieltage']} Spieltag(e) verarbeitet: **{batch_res['total_created']} Spiele neu angelegt**, **{batch_res['total_updated']} Spiele aktualisiert/ersetzt**.")
                st.balloons()
                
                # Scan-Ergebnisse nach Import aktualisieren
                st.session_state["scanned_spieltage_list"] = scan_main_directory_for_spieltage(main_scan_dir, season=entry_season)
                
                if batch_res.get('results'):
                    with st.expander("📋 Details des Batch-Imports anzeigen", expanded=True):
                        res_df = pd.DataFrame(batch_res['results'])
                        st.dataframe(res_df, use_container_width=True, hide_index=True)
                        
    # Optionaler Manueller Upload für einzelne CSV-Dateien
    with st.expander("📤 Alternative: Einzelne CSV-Dateien manuell hochladen (Drag & Drop)", expanded=False):
        uploaded_csv_files = st.file_uploader(
            "Dateien aus einem Spieltag auswählen (matches.csv, legs.csv, visits.csv, statistics.csv)",
            type=["csv"],
            accept_multiple_files=True,
            key="uploader_manual_csv"
        )
        if uploaded_csv_files:
            dfs = {}
            for f in uploaded_csv_files:
                try: dfs[f.name.lower()] = pd.read_csv(f, sep=";", encoding="utf-8-sig")
                except Exception:
                    f.seek(0)
                    dfs[f.name.lower()] = pd.read_csv(f, sep=",", encoding="utf-8-sig")
            if any("matches" in k for k in dfs):
                m_df = next(v for k, v in dfs.items() if "matches" in k)
                st.success(f"✅ {len(uploaded_csv_files)} Datei(en) geladen mit **{len(m_df)} Matches**.")
                if st.button("📥 Diese manuellen CSVs importieren", key="btn_import_manual_upload"):
                    with st.spinner("Importiere Matches..."):
                        man_res = import_analyzer_csv_data(dfs, season=entry_season, sync_league=True)
                        if man_res.get('success'):
                            st.success(f"🎉 {man_res['message']}")
                        else:
                            st.error(f"❌ Fehler: {man_res.get('message')}")

# ----------------------------------------------------

# ----------------------------------------------------
# TAB 4: DOPPEL-SPIELBERICHT
# ----------------------------------------------------
with tab_double_match:
    st.subheader("1. Spieler & Spielauswahl (Doppel)")
    col_dm_p1, col_dm_p2, col_dm_info = st.columns([1.5, 1.5, 1])
    
    with col_dm_p1:
        dm_p1_disp = st.selectbox("Spieler 1", players_df['display_name'].tolist(), key="dm_p1_sel")
    with col_dm_p2:
        dm_p2_disp = st.selectbox("Spieler 2", players_df['display_name'].tolist(), key="dm_p2_sel")
        
    dm_p1_row = players_df[players_df['display_name'] == dm_p1_disp].iloc[0]
    dm_p2_row = players_df[players_df['display_name'] == dm_p2_disp].iloc[0]
    dm_p1_id = int(dm_p1_row['id'])
    dm_p2_id = int(dm_p2_row['id'])
    
    dm_team = dm_p1_row['team']
    dm_opponents_list = STAFFEL_7_OPPONENTS if dm_team == "A-Team" else STAFFEL_11_OPPONENTS
    dm_staffel_label = "2. Kreisklasse Staffel 07 (A-Team)" if dm_team == "A-Team" else "2. Kreisklasse Staffel 11 (B-Team)"
    
    with col_dm_info:
        st.markdown(f"""
        <div style="background: rgba(0,212,255,0.1); border: 1px solid #00D4FF; border-radius: 12px; padding: 10px; text-align: center; margin-top: 10px;">
            <div style="font-size: 13px; color: #00D4FF; font-weight: 700;">ZUTREFFENDE STAFFEL</div>
            <div style="font-size: 16px; font-weight: 800; color: #FFFFFF;">{dm_staffel_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    with st.form("entry_form_double_match"):
        st.subheader("2. Doppel-Spielberichtsdaten eintragen")
        
        c1, c2 = st.columns(2)
        with c1:
            dm_date = st.date_input("Spieldatum", datetime.date.today(), key="dm_date")
        with c2:
            dm_opp = st.selectbox(f"Gegnerische Mannschaft", dm_opponents_list, key="dm_opp")
            
        st.markdown("#### Leg-Ergebnis (Best of 5)")
        lc1, lc2 = st.columns(2)
        with lc1: dm_lw = st.number_input("Gewonnene Legs", min_value=0, max_value=3, value=3, key="dm_lw")
        with lc2: dm_ll = st.number_input("Verlorene Legs", min_value=0, max_value=3, value=1, key="dm_ll")
            
        st.markdown("#### Average-Werte")
        ac1, ac2, ac3 = st.columns(3)
        with ac1: dm_avg_t = st.number_input("Gesamt Average", min_value=0.0, max_value=150.0, value=45.0, step=0.1, key="dm_avg_t")
        with ac2: dm_avg_9 = st.number_input("Durchschnitts-Average 9 Darts", min_value=0.0, max_value=150.0, value=48.0, step=0.1, key="dm_avg_9")
        with ac3: dm_avg_18 = st.number_input("Durchschnitts-Average 18 Darts", min_value=0.0, max_value=150.0, value=46.0, step=0.1, key="dm_avg_18")
            
        st.markdown("#### High Scores")
        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1: dm_s80 = st.number_input("80+ Scores", min_value=0, value=3, key="dm_s80")
        with hc2: dm_s100 = st.number_input("100+ Scores", min_value=0, value=1, key="dm_s100")
        with hc3: dm_s140 = st.number_input("140+ Scores", min_value=0, value=0, key="dm_s140")
        with hc4: dm_s180 = st.number_input("180er", min_value=0, value=0, key="dm_s180")
            
        st.markdown("#### Highlights & Specials")
        sc1, sc2, sc3 = st.columns(3)
        with sc1: dm_hf = st.number_input("Höchstes Finish (z.B. 120)", min_value=0, max_value=170, value=0, key="dm_hf")
        with sc2: dm_sl = st.number_input("Short Legs (≤18 Darts)", min_value=0, value=0, key="dm_sl")
        with sc3: dm_sp = st.number_input("Specials Anz.", min_value=0, value=0, key="dm_sp")
        
        submitted_dm = st.form_submit_button("🚀 Doppel-Spielbericht Speichern", use_container_width=True)
        if submitted_dm:
            if dm_p1_id == dm_p2_id:
                st.error("⚠️ Bitte wähle zwei verschiedene Spieler für das Doppel aus.")
            else:
                from database import add_doubles_match
                dm_data = {
                    'player1_id': dm_p1_id,
                    'player2_id': dm_p2_id,
                    'match_date': dm_date.strftime('%Y-%m-%d'),
                    'opponent': dm_opp,
                    'legs_won': dm_lw,
                    'legs_lost': dm_ll,
                    'avg_total': dm_avg_t,
                    'avg_9': dm_avg_9,
                    'avg_18': dm_avg_18,
                    'scores_80': dm_s80,
                    'scores_100': dm_s100,
                    'scores_140': dm_s140,
                    'scores_180': dm_s180,
                    'high_finishes': dm_hf,
                    'short_legs': dm_sl,
                    'specials_count': dm_sp,
                    'season': entry_season
                }
                add_doubles_match(dm_data)
                st.success(f"✅ Doppel-Spielbericht für {dm_p1_row['name']} & {dm_p2_row['name']} ({entry_season}) gespeichert!")

# ----------------------------------------------------
# TAB 3: DOPPEL-SPECIALS ERFASSEN
# ----------------------------------------------------
with tab_double_special:
    st.subheader("🤝 Doppel-Special erfassen")
    st.info("💡 **Bonus-Regel:** Jedes im Doppel geworfene Special bringt dem Spieler **+0,5 Punkte extra** im Gesamt-Ranking.")
    
    st.markdown("#### 1. Spieler-Auswahl (Doppel)")
    col_ds_p1, col_ds_info = st.columns([2, 1])
    with col_ds_p1:
        p_list = sorted(players_df['name'].tolist())
        spec_player = st.selectbox("Wer hat das Special geworfen?", p_list, key="ds_p_select")
        
    ds_player_row = players_df[players_df['name'] == spec_player].iloc[0]
    ds_player_team = ds_player_row['team']
    ds_opponents = STAFFEL_7_OPPONENTS if ds_player_team == "A-Team" else STAFFEL_11_OPPONENTS
    ds_staffel_label = "2. Kreisklasse Staffel 07" if ds_player_team == "A-Team" else "2. Kreisklasse Staffel 11"
    
    with col_ds_info:
        st.markdown(f"""
        <div style="background: rgba(0,212,255,0.1); border: 1px solid #00D4FF; border-radius: 12px; padding: 10px; text-align: center; margin-top: 10px;">
            <div style="font-size: 13px; color: #00D4FF; font-weight: 700;">ZUTREFFENDE STAFFEL</div>
            <div style="font-size: 16px; font-weight: 800; color: #FFFFFF;">{ds_staffel_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    with st.form("doubles_special_form", clear_on_submit=True):
        partner_list = ["-- Bitte Partner wählen --"] + [p for p in p_list if p != spec_player]
        spec_partner = st.selectbox("Teampartner im Doppel", partner_list, key="ds_partner")
            
        col_date, col_opp = st.columns(2)
        with col_date:
            spec_date = st.date_input("Spieldatum", datetime.date.today(), key="ds_date")
        with col_opp:
            spec_opp = st.selectbox(f"Gegnerische Mannschaft ({ds_staffel_label})", ds_opponents, key="ds_opp")
            
        col_type, col_desc = st.columns(2)
        with col_type:
            SPECIAL_TYPES = [
                "180er High Score 🎯",
                "High Finish (101 - 170) 🏁",
                "Short Game (≤ 18 Darts) 🏹",
                "Bullfinish (≥ 121) 🎯",
                "High Score (141 - 171) 💥"
            ]
            spec_type = st.selectbox("Geworfenes Special", SPECIAL_TYPES, key="ds_type")
        with col_desc:
            spec_desc = st.text_input("Details / Anmerkung (optional)", placeholder="z.B. 140er Checkout in Leg 3", key="ds_desc")
            
        ds_submitted = st.form_submit_button("➕ Doppel-Special speichern (+0,5 Pkt)", use_container_width=True)
        
        if ds_submitted:
            if spec_partner == "-- Bitte Partner wählen --":
                st.error("Bitte wähle den Teampartner aus.")
            else:
                p_id = int(ds_player_row['id'])
                add_doubles_special(
                    player_id=p_id,
                    partner_name=spec_partner,
                    opponent_team=spec_opp,
                    match_date=spec_date.strftime('%Y-%m-%d'),
                    special_type=spec_type,
                    description=spec_desc.strip(),
                    season=entry_season
                )
                st.success(f"✅ Doppel-Special für **{spec_player}** (+0,5 Pkt, {entry_season}) erfolgreich gespeichert!")

render_impressum_footer()
