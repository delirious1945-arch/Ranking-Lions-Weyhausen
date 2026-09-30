import streamlit as st
import pandas as pd
import datetime
from utils import (
    apply_custom_theme, require_admin, render_impressum_footer, 
    calculate_match_performance, get_short_name
)
from database import (
    get_matches, update_match, delete_match, 
    get_doubles_specials, update_doubles_special, delete_doubles_special,
    get_doubles_matches, update_doubles_match, delete_doubles_match,
    get_players, get_settings, get_available_seasons
)

st.set_page_config(page_title="Lions League - Verwaltung", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_admin()

st.title("⚙️ Verwaltung & Spielberichts-Bearbeitung")
st.caption("Eingetragene Einzel-Matches, Doppel-Spielberichte und Doppel-Specials bearbeiten oder Spieler detailliert analysieren & vergleichen.")

# Offizielle Gegner-Listen
STAFFEL_7_OPPONENTS = [
    "Bromer Burglöwen B", "DC Gamsen 96 B", "DC Old No.7 Sülfeld D",
    "DC Wolfsjäger C", "Erst zart dann Dart A", "Riederockets MTV Vollbüttel B",
    "TSV Rethen D", "VfB Bullseye Fallersleben B", "VfL Wolfsburg e.V. F"
]
STAFFEL_11_OPPONENTS = [
    "1.DC Didderse A", "Aller-Oker-Darter A", "Dart Kongs Triangel B",
    "FireDarter C", "HSV Isedarter B", "Mad House Fallersleben E",
    "RaZa Darts A", "VfL Wettmershagen B"
]
ALL_OPPONENTS = sorted(list(set(STAFFEL_7_OPPONENTS + STAFFEL_11_OPPONENTS)))


# ====================================================
# EINSTELLUNGEN & VERWALTUNG (HAUPTANSICHT)
# ====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "⚖️ Kategorie-Gewichtung", 
    "👤 Spieler registrieren", 
    "🔑 Passwort-Reset (Admin)",
    "👑 Rollen & Admin-Rechte"
])

with tab1:
    st.subheader("Feinjustierung der 5 Grundkategorien (0,5% Schritte)")
    current = get_settings()
    
    with st.form("settings_form"):
        c1, c2 = st.columns(2)
        with c1:
            win_w = st.slider("Siegquote (%)", 0.0, 100.0, float(current['win_weight']), step=0.5)
            avg_w = st.slider("Gesamt Average (%)", 0.0, 100.0, float(current['avg_weight']), step=0.5)
            avg9_w = st.slider("9-Dart Average (%)", 0.0, 100.0, float(current['avg9_weight']), step=0.5)
        with c2:
            avg18_w = st.slider("18-Dart Average (%)", 0.0, 100.0, float(current['avg18_weight']), step=0.5)
            scores_w = st.slider("High Scores (%)", 0.0, 100.0, float(current['scores_weight']), step=0.5)
            
        total = win_w + avg_w + avg9_w + avg18_w + scores_w
        st.markdown(f"**Summe der Gewichtungen:** `{total:.1f}%` / `100.0%`")
        
        if abs(total - 100.0) > 0.01:
            st.warning("⚠️ Die Summe der 5 Kategorien muss exakt 100,0 % ergeben!")
            submit_disabled = True
        else:
            st.success("✅ Gewichtung ist perfekt ausbalanciert (100,0 %).")
            submit_disabled = False
            
        save_settings = st.form_submit_button("💾 Gewichtung Speichern", disabled=submit_disabled, use_container_width=True)
        
        if save_settings:
            update_settings(win_w, avg_w, avg9_w, avg18_w, scores_w)
            st.success("✅ Einstellungen erfolgreich in der Datenbank gespeichert!")

with tab2:
    st.subheader("Neuen Spieler zum Team hinzufügen")
    with st.form("add_player_form", clear_on_submit=True):
        p_name = st.text_input("Vollständiger Name des Spielers")
        p_team = st.selectbox("Mannschaftszuordnung", ["A-Team", "B-Team"])
        p_role = st.selectbox("Rolle", ["player", "admin"], format_func=lambda x: "👑 Admin" if x == "admin" else "🎯 Spieler")
        p_submit = st.form_submit_button("➕ Spieler anlegen", use_container_width=True)
        
        if p_submit:
            if not p_name.strip():
                st.error("Bitte gib einen Namen ein.")
            else:
                add_player(p_name.strip(), p_team, role=p_role)
                st.success(f"✅ Spieler **{p_name.strip()}** ({p_team}, {p_role}) mit Einmal-Passwort `lions2026` angelegt!")

with tab3:
    st.subheader("🔑 Einmal-Passwort für einen Spieler zurücksetzen")
    st.caption("Setzt das Passwort des Spielers auf das Standard-Einmal-Passwort 'lions2026' zurück.")
    
    players_df = get_players()
    if not players_df.empty:
        p_reset_name = st.selectbox("Spieler für Passwort-Reset wählen", players_df['name'].tolist())
        p_reset_row = players_df[players_df['name'] == p_reset_name].iloc[0]
        
        if st.button(f"🔄 Passwort für {p_reset_name} auf 'lions2026' zurücksetzen", type="secondary", use_container_width=True):
            update_player_password(int(p_reset_row['id']), "lions2026", must_change=True)
            st.success(f"Passwort für **{p_reset_name}** wurde auf `lions2026` zurückgesetzt! Er muss bei der nächsten Anmeldung ein neues Passwort festlegen.")

with tab4:
    st.subheader("👑 Rollen & Admin-Berechtigungen verwalten")
    st.caption("Hier kannst du Teammitgliedern Admin-Rechte für Match-Eingabe, DAE, Verwaltung & Einstellungen vergeben oder entziehen.")
    
    players_df = get_players()
    if not players_df.empty:
        col_r1, col_r2 = st.columns([1.5, 1.5])
        with col_r1:
            st.markdown("##### Aktuelle Admin-Übersicht")
            admins = players_df[players_df['role'] == 'admin']
            if not admins.empty:
                for _, adm in admins.iterrows():
                    st.markdown(f"👑 **{adm['name']}** ({adm['team']}) — `Admin`")
            else:
                st.info("Aktuell sind keine Spieler als Admin eingetragen.")
                
        with col_r2:
            st.markdown("##### Rolle ändern")
            selected_p_name = st.selectbox("Spieler auswählen", players_df['name'].tolist(), key="role_sel_player")
            sel_row = players_df[players_df['name'] == selected_p_name].iloc[0]
            curr_role = sel_row.get('role', 'player') or 'player'
            
            new_role = st.radio(
                f"Rolle für {selected_p_name}:",
                ["player", "admin"],
                index=1 if curr_role == "admin" else 0,
                format_func=lambda x: "👑 Admin (Vollzugriff)" if x == "admin" else "🎯 Spieler (Nur Lesezugriff)",
                key="role_radio"
            )
            
            if st.button(f"💾 Rolle für {selected_p_name} speichern", type="primary", use_container_width=True):
                update_player_role(int(sel_row['id']), new_role)
                st.success(f"✅ Rolle für **{selected_p_name}** erfolgreich auf **{new_role.upper()}** gesetzt!")
                st.rerun()



# ====================================================
# OPTIONAL: SPIELBERICHTS-BEARBEITUNG (AUSGEBLENDET)
# ====================================================
show_match_editor = st.sidebar.checkbox(
    "🛠️ Spielberichts-Editor einblenden",
    value=False,
    help="Blendet Masken zur nachträglichen Bearbeitung bereits gespeicherter Einzel- & Doppelberichte ein."
)

if show_match_editor:
    st.divider()
    st.markdown("### 🛠️ Nachträgliche Spielberichts-Bearbeitung")
    tab_singles, tab_analytics_edit, tab_doubles_match, tab_doubles = st.tabs([
        "🎯 Einzel-Spielbericht", 
        "🚀 Analytics-Matches",
        "👥 Doppel-Spielbericht", 
        "🤝 Doppel-Special"
    ])
    
    with tab_singles:
        matches_df = get_matches()
        players_df = get_players()
    
        if matches_df.empty:
            st.info("Keine Einzel-Spielberichte in der Datenbank vorhanden.")
        else:
            st.subheader("1. Einzel-Match auswählen")
            matches_df['match_date_str'] = pd.to_datetime(matches_df['match_date']).dt.strftime('%d.%m.%Y')
            matches_df['display_label'] = matches_df.apply(
                lambda r: f"ID #{r['id']} | {r['match_date_str']} | {r['player_name']} ({r['team']}) vs {r['opponent']} [{r['legs_won']}:{r['legs_lost']}]",
                axis=1
            )
            
            selected_match_label = st.selectbox("Wähle ein Einzel-Match zum Bearbeiten", matches_df['display_label'].tolist(), key="sel_match_to_edit")
            selected_match = matches_df[matches_df['display_label'] == selected_match_label].iloc[0]
            match_id = int(selected_match['id'])
            
            st.divider()
            st.subheader(f"2. Daten für Spielbericht #{match_id} anpassen")
            
            # Formular mit vorausgefüllten Daten des ausgewählten Matches
            with st.form(f"edit_match_form_{match_id}"):
                c1, c2 = st.columns(2)
                with c1:
                    p_names = sorted(players_df['name'].tolist())
                    curr_p_idx = p_names.index(selected_match['player_name']) if selected_match['player_name'] in p_names else 0
                    edit_player_name = st.selectbox("Spieler", p_names, index=curr_p_idx, key=f"e_p_{match_id}")
                    
                    try:
                        init_date = datetime.datetime.strptime(selected_match['match_date'], '%Y-%m-%d').date()
                    except:
                        init_date = datetime.date.today()
                    edit_date = st.date_input("Spieldatum", init_date, key=f"e_d_{match_id}")
                    
                with c2:
                    # Gegner pre-select
                    selected_p_team = players_df[players_df['name'] == edit_player_name].iloc[0]['team'] if not players_df.empty else "A-Team"
                    opp_list = STAFFEL_7_OPPONENTS if selected_p_team == "A-Team" else STAFFEL_11_OPPONENTS
                    curr_opp_idx = opp_list.index(selected_match['opponent']) if selected_match['opponent'] in opp_list else 0
                    edit_opponent = st.selectbox("Gegnerische Mannschaft", opp_list, index=curr_opp_idx, key=f"e_o_{match_id}")
                    
                st.markdown("#### Leg-Ergebnis (Best of 5)")
                lc1, lc2 = st.columns(2)
                with lc1:
                    edit_legs_won = st.number_input("Gewonnene Legs", min_value=0, max_value=3, value=int(selected_match['legs_won']), key=f"e_lw_{match_id}")
                with lc2:
                    edit_legs_lost = st.number_input("Verlorene Legs", min_value=0, max_value=3, value=int(selected_match['legs_lost']), key=f"e_ll_{match_id}")
                    
                st.markdown("#### Average-Werte")
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    edit_avg_total = st.number_input("Gesamt Average", min_value=0.0, max_value=150.0, value=float(selected_match['avg_total']), step=0.1, key=f"e_at_{match_id}")
                with ac2:
                    edit_avg_9 = st.number_input("Durchschnitts-Average 9 Darts", min_value=0.0, max_value=150.0, value=float(selected_match['avg_9']), step=0.1, key=f"e_a9_{match_id}")
                with ac3:
                    edit_avg_18 = st.number_input("Durchschnitts-Average 18 Darts", min_value=0.0, max_value=150.0, value=float(selected_match['avg_18']), step=0.1, key=f"e_a18_{match_id}")
                    
                st.markdown("#### High Scores")
                hc1, hc2, hc3, hc4 = st.columns(4)
                with hc1: edit_s80 = st.number_input("80+ Scores", min_value=0, value=int(selected_match['scores_80']), key=f"e_s80_{match_id}")
                with hc2: edit_s100 = st.number_input("100+ Scores", min_value=0, value=int(selected_match['scores_100']), key=f"e_s100_{match_id}")
                with hc3: edit_s140 = st.number_input("140+ Scores", min_value=0, value=int(selected_match['scores_140']), key=f"e_s140_{match_id}")
                with hc4: edit_s180 = st.number_input("180er", min_value=0, value=int(selected_match['scores_180']), key=f"e_s180_{match_id}")
                    
                st.markdown("#### Highlights & Specials")
                sc1, sc2, sc3 = st.columns(3)
                with sc1: edit_hf = st.number_input("Höchstes Finish", min_value=0, max_value=170, value=int(selected_match['high_finishes']), key=f"e_hf_{match_id}")
                with sc2: edit_sl = st.number_input("Short Legs (≤18 Darts)", min_value=0, value=int(selected_match['short_legs']), key=f"e_sl_{match_id}")
                with sc3: edit_sp = st.number_input("Specials Anz. (Bonus +3 Pkt)", min_value=0, value=int(selected_match['specials_count']), key=f"e_sp_{match_id}")
                    
                col_save, col_del = st.columns([2, 1])
                with col_save:
                    submit_update = st.form_submit_button("💾 Änderungen am Spielbericht speichern (Überschreiben)", use_container_width=True)
                    
                if submit_update:
                    p_id = int(players_df[players_df['name'] == edit_player_name].iloc[0]['id'])
                    updated_data = {
                        'player_id': p_id,
                        'match_date': edit_date.strftime('%Y-%m-%d'),
                        'opponent': edit_opponent,
                        'legs_won': edit_legs_won,
                        'legs_lost': edit_legs_lost,
                        'avg_total': edit_avg_total,
                        'avg_9': edit_avg_9,
                        'avg_18': edit_avg_18,
                        'scores_80': edit_s80,
                        'scores_100': edit_s100,
                        'scores_140': edit_s140,
                        'scores_180': edit_s180,
                        'high_finishes': edit_hf,
                        'short_legs': edit_sl,
                        'specials_count': edit_sp
                    }
                    update_match(match_id, updated_data)
                    st.success(f"✅ Spielbericht #{match_id} für {edit_player_name} wurde erfolgreich aktualisiert und überspeichert!")
                    st.rerun()
    
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🗑️ Spielbericht #{match_id} komplett löschen", type="secondary"):
                delete_match(match_id)
                st.success(f"Match #{match_id} wurde gelöscht.")
                st.rerun()
    
    # ----------------------------------------------------
    # TAB 2: ANALYTICS-MATCHES BEARBEITEN & VERWALTEN
    # ----------------------------------------------------
    with tab_analytics_edit:
        st.subheader("🚀 Detaillierte Analytics-Matches (Legs & Visits) verwalten")
        st.caption("Hier kannst du alle mit Aufnahmen erfassten Matches anpassen, korrigieren oder löschen. Änderungen werden automatisch in die Liga synchronisiert.")
        
        from analytics.data_access import (
            get_all_analytics_matches, get_analytics_match_details, 
            update_analytics_match, delete_analytics_match
        )
        
        an_df = get_all_analytics_matches()
        
        if an_df.empty:
            st.info("Noch keine detaillierten Analytics-Matches in der Datenbank vorhanden.")
        else:
            an_df['match_date_str'] = pd.to_datetime(an_df['match_date']).dt.strftime('%d.%m.%Y')
            an_df['display_label'] = an_df.apply(
                lambda r: f"ID #{r['id']} | {r['match_date_str']} | {r['player_a_name']} vs {r['player_b_name']} ({r.get('duration_min', 0)} Min) [{r['season']}]",
                axis=1
            )
            
            sel_an_label = st.selectbox("Wähle ein Analytics-Match zum Bearbeiten / Löschen", an_df['display_label'].tolist(), key="sel_an_match_to_edit")
            sel_an_row = an_df[an_df['display_label'] == sel_an_label].iloc[0]
            an_match_id = int(sel_an_row['id'])
            
            match_details = get_analytics_match_details(an_match_id)
            
            if match_details:
                st.divider()
                st.markdown(f"#### 📝 Daten für Match #{an_match_id} bearbeiten ({match_details['player_a_name']} vs. {match_details['player_b_name']})")
                
                with st.form(f"form_edit_an_{an_match_id}"):
                    c_m1, c_m2, c_m3 = st.columns(3)
                    with c_m1:
                        try:
                            init_an_d = datetime.datetime.strptime(match_details['match_date'], '%Y-%m-%d').date()
                        except:
                            init_an_d = datetime.date.today()
                        edit_an_date = st.date_input("Spieldatum", init_an_d, key=f"e_an_d_{an_match_id}")
                    with c_m2:
                        edit_an_dur = st.number_input("Dauer (Minuten)", min_value=1, max_value=240, value=int(match_details.get('duration_min', 14) or 14), key=f"e_an_dur_{an_match_id}")
                    with c_m3:
                        edit_an_loc = st.selectbox("Spielort", ["Heim", "Auswärts"], index=0 if match_details.get('location') == 'Heim' else 1, key=f"e_an_loc_{an_match_id}")
                        
                    c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                    with c_t1:
                        edit_an_start = st.text_input("Spielstart", value=str(match_details.get('start_time', '20:49') or '20:49'), key=f"e_an_st_{an_match_id}")
                    with c_t2:
                        edit_an_end = st.text_input("Spielende", value=str(match_details.get('end_time', '21:04') or '21:04'), key=f"e_an_et_{an_match_id}")
                    with c_t3:
                        edit_an_board = st.number_input("Board-Nr.", min_value=1, max_value=32, value=int(match_details.get('board_nr', 1) or 1), key=f"e_an_bd_{an_match_id}")
                    with c_t4:
                        edit_an_mnr = st.number_input("Spielnummer", min_value=1, max_value=100, value=int(match_details.get('match_nr', 7) or 7), key=f"e_an_mn_{an_match_id}")
                        
                    st.markdown("##### Legs & Aufnahmen bearbeiten")
                    legs_edit_list = []
                    
                    for idx, leg in enumerate(match_details.get('legs', []), 1):
                        with st.expander(f"Leg {idx} (Starter: ID {leg.get('starter_player_id')})", expanded=(idx <= 2)):
                            cl_d1, cl_d2, cl_d3 = st.columns(3)
                            with cl_d1:
                                leg_darts_a = st.number_input(
                                    f"Darts geworfen ({match_details['player_a_name']})",
                                    min_value=9, max_value=60,
                                    value=int(leg.get('darts_thrown_a', 29) or 29),
                                    key=f"e_leg_da_{an_match_id}_{idx}"
                                )
                            with cl_d2:
                                leg_co_a = st.number_input(
                                    f"Checkout ({match_details['player_a_name']})",
                                    min_value=0, max_value=170,
                                    value=int(leg.get('checkout_a', 0) or 0),
                                    key=f"e_leg_coa_{an_match_id}_{idx}"
                                )
                            with cl_d3:
                                leg_brk = st.checkbox(
                                    "Break?",
                                    value=bool(leg.get('is_break', False)),
                                    key=f"e_leg_brk_{an_match_id}_{idx}"
                                )
                                
                            # Vorhandene Visits als String formatieren
                            v_a_scores = [str(v['score']) for v in leg.get('visits_a', [])]
                            v_b_scores = [str(v['score']) for v in leg.get('visits_b', [])]
                            v_a_str_init = ", ".join(v_a_scores)
                            v_b_str_init = ", ".join(v_b_scores)
                            
                            col_eva, col_evb = st.columns(2)
                            with col_eva:
                                e_va_str = st.text_area(
                                    f"Aufnahmen {match_details['player_a_name']}",
                                    value=v_a_str_init,
                                    key=f"e_va_str_{an_match_id}_{idx}",
                                    height=68
                                )
                            with col_evb:
                                e_vb_str = st.text_area(
                                    f"Aufnahmen {match_details['player_b_name']}",
                                    value=v_b_str_init,
                                    key=f"e_vb_str_{an_match_id}_{idx}",
                                    height=68
                                )
                                
                            def parse_v_str(v_str, p_id):
                                if not v_str or not v_str.strip(): return []
                                parts = v_str.replace(';', ',').replace('\n', ',').replace(' ', ',').split(',')
                                res = []
                                cur_rest = 501
                                for p in parts:
                                    cl = p.strip()
                                    if cl.isdigit():
                                        sc = int(cl)
                                        cur_rest = max(cur_rest - sc, 0)
                                        res.append({'score': sc, 'rest_score': cur_rest, 'player_id': p_id})
                                return res
                                
                            parsed_a = parse_v_str(e_va_str, match_details['player_a_id'])
                            parsed_b = parse_v_str(e_vb_str, match_details['player_b_id'])
                            
                            legs_edit_list.append({
                                'leg_num': idx,
                                'starter_player_id': leg.get('starter_player_id', match_details['player_a_id']),
                                'winner_player_id': leg.get('winner_player_id', match_details['player_a_id']),
                                'darts_thrown_a': leg_darts_a,
                                'darts_thrown_b': int(leg.get('darts_thrown_b', 0) or 0),
                                'checkout_a': leg_co_a,
                                'checkout_b': int(leg.get('checkout_b', 0) or 0),
                                'is_break': leg_brk,
                                'visits_a': parsed_a,
                                'visits_b': parsed_b
                            })
                            
                    st.markdown("<br>", unsafe_allow_html=True)
                    an_sub_save = st.form_submit_button("💾 Änderungen am Analytics-Match speichern & synchronisieren", type="primary", use_container_width=True)
                    
                    if an_sub_save:
                        updated_meta = {
                            'player_a_id': match_details['player_a_id'],
                            'player_b_id': match_details['player_b_id'],
                            'player_a_name': match_details['player_a_name'],
                            'player_b_name': match_details['player_b_name'],
                            'match_date': edit_an_date.strftime('%Y-%m-%d'),
                            'event_name': match_details.get('event_name', 'Lions League'),
                            'round_name': match_details.get('round_name', 'Liga-Spiel'),
                            'best_of_legs': match_details.get('best_of_legs', len(legs_edit_list)),
                            'location': edit_an_loc,
                            'winner_id': match_details.get('winner_id'),
                            'season': match_details.get('season', '2026/2027'),
                            'duration_min': int(edit_an_dur),
                            'start_time': str(edit_an_start).strip(),
                            'end_time': str(edit_an_end).strip(),
                            'board_nr': int(edit_an_board),
                            'match_nr': int(edit_an_mnr),
                            'round_nr': 1
                        }
                        update_analytics_match(an_match_id, updated_meta, legs_edit_list, auto_sync_league=True)
                        st.success(f"✅ Analytics-Match #{an_match_id} wurde erfolgreich aktualisiert!")
                        st.rerun()
                        
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🗑️ Analytics-Match #{an_match_id} komplett löschen (inkl. Legs, Visits & Liga-Spielbericht)", type="secondary"):
                    delete_analytics_match(an_match_id, delete_linked_league_match=True)
                    st.success(f"Match #{an_match_id} wurde erfolgreich gelöscht.")
                    st.rerun()
    
    # ----------------------------------------------------
    # TAB 3: DOPPEL-MATCHES BEARBEITEN & ÜBERSPEICHERN
    # ----------------------------------------------------
    with tab_doubles_match:
        dm_df = get_doubles_matches()
        players_df = get_players()
        
        if dm_df.empty:
            st.info("Keine Doppel-Spielberichte in der Datenbank vorhanden.")
        else:
            st.subheader("1. Doppel-Match auswählen")
            dm_df['match_date_str'] = pd.to_datetime(dm_df['match_date']).dt.strftime('%d.%m.%Y')
            dm_df['display_label'] = dm_df.apply(
                lambda r: f"ID #{r['id']} | {r['match_date_str']} | {r['p1_name']} & {r['p2_name']} vs {r['opponent']} [{r['legs_won']}:{r['legs_lost']}]",
                axis=1
            )
            
            selected_dm_label = st.selectbox("Wähle ein Doppel-Match zum Bearbeiten", dm_df['display_label'].tolist(), key="sel_dm_to_edit")
            selected_dm = dm_df[dm_df['display_label'] == selected_dm_label].iloc[0]
            dm_id = int(selected_dm['id'])
            
            st.divider()
            st.subheader(f"2. Daten für Doppel-Spielbericht #{dm_id} anpassen")
            
            with st.form(f"edit_dm_form_{dm_id}"):
                p_names = sorted(players_df['name'].tolist())
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    curr_p1_idx = p_names.index(selected_dm['p1_name']) if selected_dm['p1_name'] in p_names else 0
                    edit_dm_p1 = st.selectbox("Spieler 1", p_names, index=curr_p1_idx, key=f"edm_p1_{dm_id}")
                with col_p2:
                    curr_p2_idx = p_names.index(selected_dm['p2_name']) if selected_dm['p2_name'] in p_names else 0
                    edit_dm_p2 = st.selectbox("Spieler 2", p_names, index=curr_p2_idx, key=f"edm_p2_{dm_id}")
                
                c1, c2 = st.columns(2)
                with c1:
                    try:
                        init_dm_date = datetime.datetime.strptime(selected_dm['match_date'], '%Y-%m-%d').date()
                    except:
                        init_dm_date = datetime.date.today()
                    edit_dm_date = st.date_input("Spieldatum", init_dm_date, key=f"edm_d_{dm_id}")
                with c2:
                    selected_dm_team = players_df[players_df['name'] == edit_dm_p1].iloc[0]['team'] if not players_df.empty else "A-Team"
                    dm_opp_list = STAFFEL_7_OPPONENTS if selected_dm_team == "A-Team" else STAFFEL_11_OPPONENTS
                    curr_dm_opp_idx = dm_opp_list.index(selected_dm['opponent']) if selected_dm['opponent'] in dm_opp_list else 0
                    edit_dm_opp = st.selectbox("Gegnerische Mannschaft", dm_opp_list, index=curr_dm_opp_idx, key=f"edm_o_{dm_id}")
                
                st.markdown("#### Leg-Ergebnis (Best of 5)")
                lc1, lc2 = st.columns(2)
                with lc1: edit_dm_lw = st.number_input("Gewonnene Legs", min_value=0, max_value=3, value=int(selected_dm['legs_won']), key=f"edm_lw_{dm_id}")
                with lc2: edit_dm_ll = st.number_input("Verlorene Legs", min_value=0, max_value=3, value=int(selected_dm['legs_lost']), key=f"edm_ll_{dm_id}")
                
                st.markdown("#### Average-Werte")
                ac1, ac2, ac3 = st.columns(3)
                with ac1: edit_dm_avg_t = st.number_input("Gesamt Average", min_value=0.0, max_value=150.0, value=float(selected_dm['avg_total']), step=0.1, key=f"edm_at_{dm_id}")
                with ac2: edit_dm_avg_9 = st.number_input("Durchschnitts-Average 9 Darts", min_value=0.0, max_value=150.0, value=float(selected_dm['avg_9']), step=0.1, key=f"edm_a9_{dm_id}")
                with ac3: edit_dm_avg_18 = st.number_input("Durchschnitts-Average 18 Darts", min_value=0.0, max_value=150.0, value=float(selected_dm['avg_18']), step=0.1, key=f"edm_a18_{dm_id}")
                
                st.markdown("#### High Scores")
                hc1, hc2, hc3, hc4 = st.columns(4)
                with hc1: edit_dm_s80 = st.number_input("80+ Scores", min_value=0, value=int(selected_dm['scores_80']), key=f"edm_s80_{dm_id}")
                with hc2: edit_dm_s100 = st.number_input("100+ Scores", min_value=0, value=int(selected_dm['scores_100']), key=f"edm_s100_{dm_id}")
                with hc3: edit_dm_s140 = st.number_input("140+ Scores", min_value=0, value=int(selected_dm['scores_140']), key=f"edm_s140_{dm_id}")
                with hc4: edit_dm_s180 = st.number_input("180er", min_value=0, value=int(selected_dm['scores_180']), key=f"edm_s180_{dm_id}")
                
                st.markdown("#### Highlights & Specials")
                sc1, sc2, sc3 = st.columns(3)
                with sc1: edit_dm_hf = st.number_input("Höchstes Finish", min_value=0, max_value=170, value=int(selected_dm['high_finishes']), key=f"edm_hf_{dm_id}")
                with sc2: edit_dm_sl = st.number_input("Short Legs (≤18 Darts)", min_value=0, value=int(selected_dm['short_legs']), key=f"edm_sl_{dm_id}")
                with sc3: edit_dm_sp = st.number_input("Specials Anz.", min_value=0, value=int(selected_dm['specials_count']), key=f"edm_sp_{dm_id}")
                
                submit_dm_update = st.form_submit_button("💾 Änderungen am Doppel-Spielbericht speichern (Überschreiben)", use_container_width=True)
                
                if submit_dm_update:
                    p1_id = int(players_df[players_df['name'] == edit_dm_p1].iloc[0]['id'])
                    p2_id = int(players_df[players_df['name'] == edit_dm_p2].iloc[0]['id'])
                    if p1_id == p2_id:
                        st.error("⚠️ Bitte wähle zwei verschiedene Spieler aus.")
                    else:
                        updated_dm = {
                            'player1_id': p1_id,
                            'player2_id': p2_id,
                            'match_date': edit_dm_date.strftime('%Y-%m-%d'),
                            'opponent': edit_dm_opp,
                            'legs_won': edit_dm_lw,
                            'legs_lost': edit_dm_ll,
                            'avg_total': edit_dm_avg_t,
                            'avg_9': edit_dm_avg_9,
                            'avg_18': edit_dm_avg_18,
                            'scores_80': edit_dm_s80,
                            'scores_100': edit_dm_s100,
                            'scores_140': edit_dm_s140,
                            'scores_180': edit_dm_s180,
                            'high_finishes': edit_dm_hf,
                            'short_legs': edit_dm_sl,
                            'specials_count': edit_dm_sp
                        }
                        update_doubles_match(dm_id, updated_dm)
                        st.success(f"✅ Doppel-Spielbericht #{dm_id} für {edit_dm_p1} & {edit_dm_p2} wurde aktualisiert!")
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🗑️ Doppel-Spielbericht #{dm_id} komplett löschen", type="secondary"):
                delete_doubles_match(dm_id)
                st.success(f"Doppel-Spielbericht #{dm_id} wurde gelöscht.")
                st.rerun()
    
    # ----------------------------------------------------
    # TAB 3: DOPPEL-SPECIALS BEARBEITEN & ÜBERSPEICHERN
    # ----------------------------------------------------
    with tab_doubles:
        doubles_df = get_doubles_specials()
        players_df = get_players()
        
        if doubles_df.empty:
            st.info("Keine Doppel-Specials in der Datenbank vorhanden.")
        else:
            st.subheader("1. Doppel-Special auswählen")
            doubles_df['date_str'] = pd.to_datetime(doubles_df['match_date']).dt.strftime('%d.%m.%Y')
            doubles_df['display_label'] = doubles_df.apply(
                lambda r: f"ID #{r['id']} | {r['date_str']} | {r['player_name']} & {r['partner_name']} vs {r['opponent_team']} [{r['special_type']}]",
                axis=1
            )
            
            selected_ds_label = st.selectbox("Wähle ein Doppel-Special zum Bearbeiten", doubles_df['display_label'].tolist(), key="sel_ds_to_edit")
            selected_ds = doubles_df[doubles_df['display_label'] == selected_ds_label].iloc[0]
            ds_id = int(selected_ds['id'])
            
            st.divider()
            st.subheader(f"2. Daten für Doppel-Special #{ds_id} anpassen")
            
            with st.form(f"edit_ds_form_{ds_id}"):
                col_p1, col_partner = st.columns(2)
                with col_p1:
                    p_list = sorted(players_df['name'].tolist())
                    curr_ds_p_idx = p_list.index(selected_ds['player_name']) if selected_ds['player_name'] in p_list else 0
                    edit_ds_player = st.selectbox("Wer hat das Special geworfen?", p_list, index=curr_ds_p_idx, key=f"e_ds_p_{ds_id}")
                with col_partner:
                    partner_list = [p for p in p_list if p != edit_ds_player]
                    curr_ds_part_idx = partner_list.index(selected_ds['partner_name']) if selected_ds['partner_name'] in partner_list else 0
                    edit_ds_partner = st.selectbox("Teampartner im Doppel", partner_list, index=curr_ds_part_idx, key=f"e_ds_part_{ds_id}")
                    
                col_date, col_opp = st.columns(2)
                with col_date:
                    try:
                        init_ds_date = datetime.datetime.strptime(selected_ds['match_date'], '%Y-%m-%d').date()
                    except:
                        init_ds_date = datetime.date.today()
                    edit_ds_date = st.date_input("Spieldatum", init_ds_date, key=f"e_ds_d_{ds_id}")
                with col_opp:
                    selected_ds_p_team = players_df[players_df['name'] == edit_ds_player].iloc[0]['team'] if not players_df.empty else "A-Team"
                    ds_opps = STAFFEL_7_OPPONENTS if selected_ds_p_team == "A-Team" else STAFFEL_11_OPPONENTS
                    curr_ds_opp_idx = ds_opps.index(selected_ds['opponent_team']) if selected_ds['opponent_team'] in ds_opps else 0
                    edit_ds_opp = st.selectbox("Gegnerische Mannschaft", ds_opps, index=curr_ds_opp_idx, key=f"e_ds_opp_{ds_id}")
                    
                col_type, col_desc = st.columns(2)
                with col_type:
                    SPECIAL_TYPES = [
                        "180er High Score 🎯",
                        "High Finish (101 - 170) 🏁",
                        "Short Game (≤ 18 Darts) 🏹",
                        "Bullfinish (≥ 121) 🎯",
                        "High Score (141 - 171) 💥"
                    ]
                    curr_type_idx = SPECIAL_TYPES.index(selected_ds['special_type']) if selected_ds['special_type'] in SPECIAL_TYPES else 0
                    edit_ds_type = st.selectbox("Geworfenes Special", SPECIAL_TYPES, index=curr_type_idx, key=f"e_ds_t_{ds_id}")
                with col_desc:
                    edit_ds_desc = st.text_input("Details / Anmerkung (optional)", value=str(selected_ds['description'] if selected_ds['description'] else ""), key=f"e_ds_desc_{ds_id}")
                    
                submit_ds_update = st.form_submit_button("💾 Änderungen am Doppel-Special speichern (Überschreiben)", use_container_width=True)
                
                if submit_ds_update:
                    p_id = int(players_df[players_df['name'] == edit_ds_player].iloc[0]['id'])
                    update_doubles_special(
                        ds_id,
                        player_id=p_id,
                        partner_name=edit_ds_partner,
                        opponent_team=edit_ds_opp,
                        match_date=edit_ds_date.strftime('%Y-%m-%d'),
                        special_type=edit_ds_type,
                        description=edit_ds_desc.strip()
                    )
                    st.success(f"✅ Doppel-Special #{ds_id} für {edit_ds_player} wurde aktualisiert!")
                    st.rerun()
    
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(f"🗑️ Doppel-Special #{ds_id} komplett löschen", type="secondary"):
                delete_doubles_special(ds_id)
                st.success(f"Doppel-Special #{ds_id} wurde gelöscht.")
                st.rerun()
    
    # ----------------------------------------------------
    # TAB 4: SPIELER-VERGLEICH & ANALYSE
    # ----------------------------------------------------
    

render_impressum_footer()
