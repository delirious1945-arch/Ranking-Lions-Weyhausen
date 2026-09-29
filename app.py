import streamlit as st
import pandas as pd
import datetime
from database import (
    init_db, get_matches, get_settings, get_players, 
    update_player_password, get_doubles_specials, get_doubles_matches,
    get_top_26er_players
)
try:
    from database import get_available_seasons
except ImportError:
    def get_available_seasons():
        return ["2026/2027"]
from utils import (
    calculate_match_performance, 
    apply_custom_theme, 
    init_session_auth, 
    check_login, 
    render_sidebar_auth,
    get_avatar_svg,
    get_base64_image,
    validate_password_strength
)

init_session_auth()
is_auth = st.session_state.get('authenticated', False)
st.set_page_config(
    page_title="Lions League - SC Weyhausen", 
    layout="wide", 
    page_icon="assets/logo.png",
    initial_sidebar_state="expanded" if is_auth else "collapsed"
)
init_db()
apply_custom_theme()

# ----------------------------------------------------
# 1. NEUTRALE LANDINGPAGE (OHNE SEITENLEISTE / PRIVACY-DATENSCHUTZ)
# ----------------------------------------------------
if not st.session_state.get('authenticated', False):
    st.markdown("""
    <style>
    /* 1. Header & Sidebar komplett neutralisieren */
    [data-testid="stHeader"],
    header,
    [data-testid="stSidebar"], 
    [data-testid="stSidebarNav"], 
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapseButton"],
    footer,
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
        width: 0 !important;
    }
    
    /* 2. Vertikal harmonisch zentrieren & großzügige 2-Spalten-Breite */
    .block-container, [data-testid="block-container"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        margin-top: 4.5vh !important;
        max-width: 1040px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* 3. Formular: Große, elegante Karte in der rechten Spalte */
    [data-testid="stForm"] {
        background: rgba(10, 20, 42, 0.88) !important;
        border: 1.5px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 20px !important;
        padding: 26px 36px 22px 36px !important;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.65), 0 0 32px rgba(0, 212, 255, 0.18) !important;
        backdrop-filter: blur(16px) !important;
    }
    [data-testid="stForm"] label {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stForm"] .stTextInput input {
        font-size: 16px !important;
        padding: 10px 16px !important;
        height: 48px !important;
    }
    [data-testid="stForm"] .stTextInput {
        margin-bottom: 4px !important;
    }
    [data-testid="stForm"] div[data-testid="stVerticalBlock"] > div {
        gap: 0.4rem !important;
    }
    [data-testid="stForm"] button[kind="primary"],
    [data-testid="stForm"] button[kind="secondary"],
    [data-testid="stForm"] button {
        height: 50px !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        margin-top: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    logo_b64 = get_base64_image("assets/logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 250px; max-width: 95%; height: auto; object-fit: contain; display: inline-block; filter: drop-shadow(0 0 28px rgba(0, 212, 255, 0.45)) drop-shadow(0 8px 20px rgba(0, 0, 0, 0.7));">' if logo_b64 else '<div style="width: 190px; height: 190px; border-radius: 12px; background: #00D4FF;"></div>'
    
    col_left, col_right = st.columns([1.0, 1.2], gap="large")
    
    with col_left:
        st.markdown(f"""
        <div style='text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding-top: 4px;'>
            <div style="display: block; margin: 0 auto 10px auto;">
                {logo_html}
            </div>
            <h1 style='color: #FFFFFF; font-size: 32px; font-weight: 800; letter-spacing: 2px; margin: 4px 0 2px 0; text-shadow: 0 0 26px rgba(0,212,255,0.6);'>
                LIONS LEAGUE
            </h1>
            <p style='color: #00D4FF; font-size: 14px; font-weight: 700; margin: 0 0 4px 0; letter-spacing: 0.8px; text-transform: uppercase; line-height: 1.3;'>
                SC WEYHAUSEN VON 1921 E.V.<br>SPARTE DARTSPORT
            </p>
            <p style='color: #94A3B8; font-size: 12.5px; margin: 2px 0 0 0;'>
                Geschlossenes Mitgliederportal
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_right:
        # Erstanmeldung: Passwortänderung mit strengen Regeln
        if st.session_state.get('pending_pw_change'):
            with st.form("first_login_pw_form"):
                st.markdown("<h4 style='color: #00D4FF; font-size: 17px; margin: 0 0 10px 0;'>🔑 Erstanmeldung: Neues Passwort festlegen</h4>", unsafe_allow_html=True)
                st.info("""
                **Passwort-Regularien:**
                - Mindestens **10 Zeichen** lang
                - Mindestens **eine Zahl** (0–9)
                - Mindestens **ein Sonderzeichen** (z.B. `!`, `?`, `@`, `#`, `$`, `%`, `-`, `_`)
                """)
                
                new_pw = st.text_input("Neues persönliches Passwort", type="password")
                new_pw_confirm = st.text_input("Passwort wiederholen", type="password")
                submit_pw = st.form_submit_button("💾 Passwort speichern & Anmelden", use_container_width=True)
                
                if submit_pw:
                    is_valid, err_msg = validate_password_strength(new_pw)
                    if not is_valid:
                        st.error(f"⚠️ {err_msg}")
                    elif new_pw.strip() != new_pw_confirm.strip():
                        st.error("⚠️ Die beiden Passwörter stimmen nicht überein.")
                    else:
                        p_id = st.session_state['pending_player_id']
                        update_player_password(p_id, new_pw.strip())
                        st.session_state['authenticated'] = True
                        st.session_state['role'] = st.session_state['pending_role']
                        st.session_state['user_name'] = st.session_state['pending_user_name']
                        st.session_state['player_id'] = p_id
                        st.session_state['pending_pw_change'] = False
                        st.success("Passwort erfolgreich gespeichert!")
                        st.rerun()
        else:
            with st.form("login_form"):
                st.markdown("<div style='color: #00D4FF; font-size: 21px; font-weight: 700; margin: 0 0 16px 0; text-align: center; letter-spacing: 0.5px;'>🔒 Mitglieder Login</div>", unsafe_allow_html=True)
                
                # DATENSCHUTZ: Keine Namensliste sichtbar! Manuelle Texteingabe.
                user_input = st.text_input("Benutzername / Name", placeholder="Vor- und Nachname (oder Admin)")
                pass_input = st.text_input("Passwort / PIN", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("🚀 Anmelden", use_container_width=True)
                
                if submit_login:
                    if not user_input.strip():
                        st.error("Bitte gib deinen Benutzernamen / Namen ein.")
                    else:
                        user_info = check_login(user_input.strip(), pass_input)
                        
                        if user_info:
                            if user_info.get('must_change_pw') and user_info.get('player_id'):
                                st.session_state['pending_pw_change'] = True
                                st.session_state['pending_player_id'] = user_info['player_id']
                                st.session_state['pending_role'] = user_info['role']
                                st.session_state['pending_user_name'] = user_info['name']
                                st.rerun()
                            else:
                                st.session_state['authenticated'] = True
                                st.session_state['role'] = user_info['role']
                                st.session_state['user_name'] = user_info['name']
                                st.session_state['player_id'] = user_info.get('player_id')
                                st.rerun()
                        else:
                            st.error("Ungültiger Name oder Passwort. Bei Erstanmeldung nutze bitte dein Vorname/Name und das Einmal-Passwort 'lions2026'.")
    
    st.markdown("""
    <div style='text-align: center; margin-top: 14px; color: #64748B; font-size: 11.5px; line-height: 1.4;'>
        © 2026 Sportclub Weyhausen von 1921 e.V. • Sparte Darts • Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ----------------------------------------------------
# 2. HAUPT-DASHBOARD (1:1 MOCKUP DESIGN)
# ----------------------------------------------------
render_sidebar_auth()

logo_b64 = get_base64_image("assets/logo.png")
available_seasons = get_available_seasons()

# Top Header Bar mit Saison-Auswahl & Versionsanzeige
col_head_title, col_head_season = st.columns([3.5, 1.1])
with col_head_title:
    st.markdown(f"""<div style="background: rgba(13, 22, 41, 0.72); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 12px 22px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35); backdrop-filter: blur(14px); margin-bottom: 18px; height: 62px;">
<div style="display: flex; align-items: center; gap: 12px;">
<img src="data:image/png;base64,{logo_b64}" width="38" height="38" style="border-radius: 6px; object-fit: contain;" />
<span style="font-weight: 700; font-size: 17px; color: #F8FAFC; letter-spacing: 0.5px;">LIONS LEAGUE • SC WEYHAUSEN</span>
</div>
<div style="display: flex; align-items: center; gap: 8px;">
<span style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); color: #94A3B8; font-weight: 600; font-size: 11.5px; padding: 3px 10px; border-radius: 6px; letter-spacing: 0.5px;">
v1.10
</span>
</div>
</div>""", unsafe_allow_html=True)

with col_head_season:
    selected_season = st.selectbox("📅 Saison wählen", available_seasons, index=0, key="global_season_selector")

try:
    matches_df = get_matches(season=selected_season)
except TypeError:
    matches_df = get_matches()

settings = get_settings()

try:
    doubles_df = get_doubles_specials(season=selected_season)
except TypeError:
    doubles_df = get_doubles_specials()

try:
    doubles_matches_df = get_doubles_matches(season=selected_season)
except TypeError:
    doubles_matches_df = get_doubles_matches()

if matches_df.empty and doubles_df.empty and doubles_matches_df.empty:
    st.info("🎯 Noch keine Spieldaten vorhanden. Der Spartenleiter kann unter 'Eingabe' neue Einzel-Matches oder Doppel-Specials erfassen.")
else:
    if not matches_df.empty:
        matches_df['match_date_dt'] = pd.to_datetime(matches_df['match_date'])
        matches_df['match_date_str'] = matches_df['match_date_dt'].dt.strftime('%d.%m.%Y')
        
        results = []
        for _, row in matches_df.iterrows():
            perf = calculate_match_performance(row.to_dict(), settings)
            results.append({
                'Match_ID': row['id'],
                'Datum': row['match_date_str'],
                'Datum_DT': row['match_date_dt'],
                'Spieler': row['player_name'],
                'Team': row['team'],
                'Gegner': row['opponent'],
                'Base_Rating': perf.get('base_rating', perf['total_rating'] - perf['specials_bonus']),
                'Rating': perf['total_rating'],
                'Sieg': '✅' if perf['win_ratio'] == 100 else '❌',
                'Is_Win': 1 if perf['win_ratio'] == 100 else 0,
                'Legs_Won': row['legs_won'],
                'Legs_Lost': row['legs_lost'],
                'Gesamt Avg': row['avg_total'],
                '9D Avg': row['avg_9'],
                '18D Avg': row['avg_18'],
                'Scores_Count': row['scores_80'] + row['scores_100'] + row['scores_140'] + row['scores_180'],
                'Scores/Leg': perf['score_ratio'],
                'Specials': perf['specials_count'],
                '180er': row['scores_180'],
                'High Finishes': row['high_finishes'],
                'Short Legs': row['short_legs']
            })
        res_df = pd.DataFrame(results)
    else:
        res_df = pd.DataFrame()
    
    def get_short_name(full_name):
        p = full_name.split()
        return f"{p[0]} {p[1][0]}." if len(p) > 1 else full_name

    doubles_bonus_map = {}
    if not doubles_df.empty:
        for p_name, group in doubles_df.groupby('player_name'):
            doubles_bonus_map[p_name] = len(group) * 0.5

    # ----------------------------------------------------
    # 3-SPALTEN GRID
    # ----------------------------------------------------
    col1, col2, col3 = st.columns([1.1, 1.1, 1.1])
    
    # ====================================================
    # SPALTE 1: TEAM BATTLE + 3 KPI CARDS
    # ====================================================
    with col1:
        team_a_df = res_df[res_df['Team'] == 'A-Team'] if not res_df.empty else pd.DataFrame()
        team_b_df = res_df[res_df['Team'] == 'B-Team'] if not res_df.empty else pd.DataFrame()
        
        avg_a = team_a_df['Gesamt Avg'].mean() if not team_a_df.empty else 0.0
        avg_b = team_b_df['Gesamt Avg'].mean() if not team_b_df.empty else 0.0
        
        avg9_a = team_a_df['9D Avg'].mean() if not team_a_df.empty else 0.0
        avg9_b = team_b_df['9D Avg'].mean() if not team_b_df.empty else 0.0
        
        avg18_a = team_a_df['18D Avg'].mean() if not team_a_df.empty else 0.0
        avg18_b = team_b_df['18D Avg'].mean() if not team_b_df.empty else 0.0
        
        hf_a = team_a_df['High Finishes'].max() if not team_a_df.empty else 0
        hf_b = team_b_df['High Finishes'].max() if not team_b_df.empty else 0
        
        sp_single_a = team_a_df['Specials'].sum() if not team_a_df.empty else 0
        sp_single_b = team_b_df['Specials'].sum() if not team_b_df.empty else 0
        
        sp_double_a = len(doubles_df[doubles_df['team'] == 'A-Team']) if not doubles_df.empty else 0
        sp_double_b = len(doubles_df[doubles_df['team'] == 'B-Team']) if not doubles_df.empty else 0
        
        sp_a = sp_single_a + sp_double_a
        sp_b = sp_single_b + sp_double_b
        
        wins_a = team_a_df['Is_Win'].sum() if not team_a_df.empty else 0
        wins_b = team_b_df['Is_Win'].sum() if not team_b_df.empty else 0
        
        # Doppel-Wins berechnen (Spieler 1 gehört zum Team des Gewinners)
        dw_a = 0
        dw_b = 0
        if not doubles_matches_df.empty:
            for _, drow in doubles_matches_df.iterrows():
                if drow['legs_won'] > drow['legs_lost']:
                    if drow['team'] == 'A-Team':
                        dw_a += 1
                    else:
                        dw_b += 1
        total_wins_a = int(wins_a) + dw_a
        total_wins_b = int(wins_b) + dw_b
        
        # Legs aus Einzel und Doppel zusammenrechnen
        single_legs_a = team_a_df['Legs_Won'].sum() if not team_a_df.empty else 0
        single_legs_b = team_b_df['Legs_Won'].sum() if not team_b_df.empty else 0
        double_legs_a = doubles_matches_df[doubles_matches_df['team'] == 'A-Team']['legs_won'].sum() if not doubles_matches_df.empty else 0
        double_legs_b = doubles_matches_df[doubles_matches_df['team'] == 'B-Team']['legs_won'].sum() if not doubles_matches_df.empty else 0
        total_legs_a = int(single_legs_a) + int(double_legs_a)
        total_legs_b = int(single_legs_b) + int(double_legs_b)
        
        def calc_bar(val_a, val_b):
            tot = (val_a + val_b) if (val_a + val_b) > 0 else 1
            pct_a = min(max(int((val_a / tot) * 100), 20), 80)
            return pct_a, 100 - pct_a

        bar_avg_a, bar_avg_b = calc_bar(avg_a, avg_b)
        bar_a9_a, bar_a9_b = calc_bar(avg9_a, avg9_b)
        bar_a18_a, bar_a18_b = calc_bar(avg18_a, avg18_b)
        bar_sets_a, bar_sets_b = calc_bar(total_wins_a, total_wins_b)
        bar_leg_single_a, bar_leg_single_b = calc_bar(int(single_legs_a), int(single_legs_b))
        bar_leg_double_a, bar_leg_double_b = calc_bar(int(double_legs_a), int(double_legs_b))
        bar_leg_total_a, bar_leg_total_b = calc_bar(total_legs_a, total_legs_b)

        st.markdown(f"""<div class="mockup-card">
<div class="card-title"><span>TEAM BATTLE</span><span style="font-size: 11.5px; color: #64748B; font-weight: 600;">VERGLEICH</span></div>
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 10px;">
<div class="team-pill-a" style="flex: 1;">A-Team</div>
<span style="font-weight: 700; color: #64748B; font-size: 12px; letter-spacing: 1px;">VS</span>
<div class="team-pill-b" style="flex: 1;">B-Team</div>
</div>

<div class="battle-row"><span class="battle-val-a">{avg_a:.1f}</span><span class="battle-label">Gesamt-Average</span><span class="battle-val-b">{avg_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_avg_a}%;"></div><div class="battle-bar-b" style="width: {bar_avg_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{avg9_a:.1f}</span><span class="battle-label">Durchschnitts-Average 9 Darts</span><span class="battle-val-b">{avg9_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a9_a}%;"></div><div class="battle-bar-b" style="width: {bar_a9_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{avg18_a:.1f}</span><span class="battle-label">Durchschnitts-Average 18 Darts</span><span class="battle-val-b">{avg18_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a18_a}%;"></div><div class="battle-bar-b" style="width: {bar_a18_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(hf_a)}</span><span class="battle-label">High Finish</span><span class="battle-val-b">{int(hf_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: 50%;"></div><div class="battle-bar-b" style="width: 50%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(sp_a)}</span><span class="battle-label">Specials</span><span class="battle-val-b">{int(sp_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: 50%;"></div><div class="battle-bar-b" style="width: 50%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{total_wins_a}</span><span class="battle-label">Gewonnene Sets</span><span class="battle-val-b">{total_wins_b}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_sets_a}%;"></div><div class="battle-bar-b" style="width: {bar_sets_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(single_legs_a)}</span><span class="battle-label">↳ Gewonnene Legs (Single)</span><span class="battle-val-b">{int(single_legs_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_leg_single_a}%;"></div><div class="battle-bar-b" style="width: {bar_leg_single_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(double_legs_a)}</span><span class="battle-label">↳ Gewonnene Legs (Doppel)</span><span class="battle-val-b">{int(double_legs_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_leg_double_a}%;"></div><div class="battle-bar-b" style="width: {bar_leg_double_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{total_legs_a}</span><span class="battle-label">Gewonnene Legs Gesamt</span><span class="battle-val-b">{total_legs_b}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_leg_total_a}%;"></div><div class="battle-bar-b" style="width: {bar_leg_total_b}%;"></div></div>
</div>""", unsafe_allow_html=True)

    # ====================================================
    # SPALTE 2: TOP 3 PODIUM MIT ECHTEN FOTOS
    # ====================================================
    with col2:
        if not res_df.empty:
            top_month = res_df.groupby(['Spieler', 'Team']).agg({
                'Base_Rating': 'mean',
                'Specials': 'sum'
            }).reset_index()
            top_month['Rating'] = top_month['Base_Rating'] + (top_month['Specials'] * 0.5) + top_month['Spieler'].map(lambda p: doubles_bonus_map.get(p, 0.0))
            top_month = top_month.sort_values(by='Rating', ascending=False).head(3).reset_index(drop=True)
        else:
            top_month = pd.DataFrame()
            
        p1 = top_month.iloc[0] if len(top_month) > 0 else {'Spieler': 'Offen', 'Rating': 0.0}
        p2 = top_month.iloc[1] if len(top_month) > 1 else {'Spieler': 'Offen', 'Rating': 0.0}
        p3 = top_month.iloc[2] if len(top_month) > 2 else {'Spieler': 'Offen', 'Rating': 0.0}
        
        # Bild 2: Größere Avatare und größeres Podium
        av1 = get_avatar_svg(p1['Spieler'], "#FFD700", 88)
        av2 = get_avatar_svg(p2['Spieler'], "#C0C0C0", 70)
        av3 = get_avatar_svg(p3['Spieler'], "#CD7F32", 70)
        
        st.markdown(f"""<div class="mockup-card" style="margin-bottom: 12px;">
<div class="card-title"><span>TOP 3 • MONATSWERTUNG</span><span style="font-size: 11.5px; color: #64748B; font-weight: 600;">PODIUM</span></div>
<div style="display: flex; align-items: flex-end; justify-content: center; gap: 8px; margin-top: 4px; min-height: 235px;">
<div style="flex: 1; text-align: center;">
{av2}
<div style="background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 10px; padding: 8px 3px; margin-top: 6px;">
<div style="font-size: 12px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">2. Platz</div>
<div style="font-size: 12px; font-weight: 600; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{get_short_name(p2['Spieler'])}</div>
<div style="font-size: 12px; color: #00D4FF; font-weight: 700;">{p2['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1.2; text-align: center; margin-bottom: 6px;">
{av1}
<div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 10px; padding: 10px 4px; margin-top: 6px;">
<div style="font-size: 13px; font-weight: 800; color: #F59E0B; text-transform: uppercase; letter-spacing: 0.5px;">1. Platz</div>
<div style="font-size: 13px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{get_short_name(p1['Spieler'])}</div>
<div style="font-size: 13px; color: #00D4FF; font-weight: 800;">{p1['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1; text-align: center;">
{av3}
<div style="background: rgba(180, 83, 9, 0.08); border: 1px solid rgba(180, 83, 9, 0.25); border-radius: 10px; padding: 8px 3px; margin-top: 6px;">
<div style="font-size: 12px; font-weight: 700; color: #D97706; text-transform: uppercase; letter-spacing: 0.5px;">3. Platz</div>
<div style="font-size: 12px; font-weight: 600; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{get_short_name(p3['Spieler'])}</div>
<div style="font-size: 12px; color: #00D4FF; font-weight: 700;">{p3['Rating']:.2f} Pkt</div>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
        
        # Lustiges 26er Ranking ("Die Frühstücks-Könige" / "The Breakfast Club") - 3 Spieler
        try:
            df_26 = get_top_26er_players(season=selected_season, limit=3)
        except Exception:
            df_26 = pd.DataFrame()
            
        rows_list = []
        rank_styles = [
            {"num_color": "#EF4444", "bg": "linear-gradient(90deg, rgba(239, 68, 68, 0.12), rgba(255,255,255,0.02))", "border": "rgba(239, 68, 68, 0.35)", "cnt_color": "#EF4444"},
            {"num_color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.05)", "border": "rgba(245, 158, 11, 0.25)", "cnt_color": "#F59E0B"},
            {"num_color": "#94A3B8", "bg": "rgba(255, 255, 255, 0.02)", "border": "rgba(148, 163, 184, 0.2)", "cnt_color": "#CBD5E1"}
        ]
        
        for idx, row in df_26.iterrows():
            r_idx = min(idx, len(rank_styles) - 1)
            style = rank_styles[r_idx]
            p_name = get_short_name(row['player_name'])
            av = get_avatar_svg(row['player_name'], style["num_color"], 34)
            t_name = row['team']
            cnt = int(row['count_26'])
            
            rows_list.append(f"""<div style="display: flex; align-items: center; justify-content: space-between; background: {style['bg']}; padding: 5px 12px; border-radius: 9px; border: 1px solid {style['border']};">
    <div style="display: flex; align-items: center; gap: 8px;">
        <div style="font-size: 13.5px; font-weight: 800; color: {style['num_color']}; width: 16px;">{idx + 1}.</div>
        {av}
        <div>
            <div style="font-size: 13px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{p_name}</div>
            <div style="font-size: 10px; color: #94A3B8; font-weight: 600;">{t_name}</div>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 15px; font-weight: 800; color: {style['cnt_color']};">{cnt}×</div>
        <div style="font-size: 9px; color: #64748B; font-weight: 600; text-transform: uppercase;">26er Scores</div>
    </div>
</div>""")

        if rows_list:
            p26_rows_html = "\n".join(rows_list)
        else:
            p26_rows_html = '<div style="color:#94A3B8;text-align:center;padding:10px;font-size:12px;">Noch kein Frühstück serviert ☕</div>'

        st.markdown(f"""<div class="mockup-card" style="margin-bottom: 12px; padding: 12px 18px;">
<div class="card-title" style="font-size: 14px !important; margin-bottom: 8px; padding-bottom: 4px;"><span>🥐 DIE FRÜHSTÜCKS-KÖNIGE (26er)</span><span style="font-size: 11px; color: #EF4444; font-weight: 700; background: rgba(239, 68, 68, 0.12); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3);">FLOP 3 🎯</span></div>
<div style="display: flex; flex-direction: column; gap: 6px;">
{p26_rows_html}
</div>
</div>""", unsafe_allow_html=True)
        
        # Bild 1: Saison Highlights kompakter
        tot_specials = (res_df['Specials'].sum() if not res_df.empty else 0) + len(doubles_df)
        
        st.markdown(f"""<div class="mockup-card" style="margin-bottom: 0px; padding: 12px 18px;">
<div class="card-title" style="font-size: 14px !important; margin-bottom: 8px; padding-bottom: 4px;"><span>SAISON HIGHLIGHTS</span><span style="font-size: 11.5px; color: #64748B; font-weight: 600;">STATISTIK</span></div>
<div style="display: flex; flex-direction: column; gap: 6px;">
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.02); padding: 7px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
<div>
<div style="font-size: 10.5px; color: #64748B; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">Specials Gesamt (Einzel & Doppel)</div>
<div style="font-size: 13.5px; font-weight: 700; color: #FFFFFF;">{int(tot_specials)} Specials</div>
</div>
<span style="font-size: 12px; color: #00D4FF; font-weight: 700;">•</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.02); padding: 7px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
<div>
<div style="font-size: 10.5px; color: #64748B; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">Geworfene Doppel-Specials</div>
<div style="font-size: 13.5px; font-weight: 700; color: #00D4FF;">{len(doubles_df)} Doppel-Specials (+{len(doubles_df)*0.5:.1f} Pkt)</div>
</div>
<span style="font-size: 12px; color: #34D399; font-weight: 700;">•</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # ====================================================
    # SPALTE 3: RANKINGS (MIT DOPPEL-BONUS)
    # ====================================================
    with col3:
        if not res_df.empty:
            leaderboard = res_df.groupby(['Spieler', 'Team']).agg({
                'Base_Rating': 'mean',
                'Gesamt Avg': 'mean',
                'Match_ID': 'count',
                'Specials': 'sum'
            }).reset_index()
            leaderboard['Rating'] = leaderboard['Base_Rating'] + (leaderboard['Specials'] * 0.5) + leaderboard['Spieler'].map(lambda p: doubles_bonus_map.get(p, 0.0))
            leaderboard = leaderboard.sort_values(by='Rating', ascending=False).reset_index(drop=True)
        else:
            leaderboard = pd.DataFrame()
        
        rankings_body = ""
        for idx, r_row in leaderboard.iterrows():
            rank_num = idx + 1
            av_sm = get_avatar_svg(r_row['Spieler'], "#00D4FF", 26)
            bg = "rgba(255,255,255,0.05)" if idx % 2 == 0 else "transparent"
            rankings_body += f"""<div style="display:flex;align-items:center;padding:8px 6px;border-radius:10px;margin-bottom:5px;background:{bg};border:1px solid rgba(0,212,255,0.1);">
<div style="width:26px;color:#00D4FF;font-weight:800;font-size:15px;flex-shrink:0;">{rank_num}</div>
<div style="width:32px;flex-shrink:0;">{av_sm}</div>
<div style="flex:1;font-weight:700;font-size:15px;color:#FFFFFF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-left:4px;">{get_short_name(r_row['Spieler'])}</div>
<div style="width:52px;text-align:right;font-size:14px;color:#CBD5E1;font-weight:600;flex-shrink:0;margin-right:8px;">{int(r_row['Match_ID'])}</div>
<div style="width:58px;text-align:right;font-size:16px;color:#00D4FF;font-weight:900;flex-shrink:0;">{r_row['Rating']:.2f}</div>
</div>"""

        st.markdown(f"""<div class="mockup-card" style="min-height:490px;margin-bottom:0px;display:flex;flex-direction:column;">
<div class="card-title"><span>RANGLISTE</span><span style="font-size: 11.5px; color: #64748B; font-weight: 600;">TOP SPIELER</span></div>
<div style="display:flex;align-items:center;padding:0 6px 8px 6px;">
<div style="width:26px;font-size:10.5px;font-weight:700;color:#64748B;flex-shrink:0;">#</div>
<div style="width:32px;flex-shrink:0;"></div>
<div style="flex:1;font-size:10.5px;font-weight:700;color:#64748B;padding-left:4px;white-space:nowrap;letter-spacing:0.5px;text-transform:uppercase;">Spieler</div>
<div style="width:52px;text-align:right;font-size:10.5px;font-weight:700;color:#64748B;white-space:nowrap;flex-shrink:0;margin-right:8px;letter-spacing:0.5px;text-transform:uppercase;">Spiele</div>
<div style="width:58px;text-align:right;font-size:10.5px;font-weight:700;color:#00D4FF;white-space:nowrap;flex-shrink:0;letter-spacing:0.5px;text-transform:uppercase;">Punkte</div>
</div>
<div style="flex:1;overflow-y:auto;padding-right:4px;">
{rankings_body if rankings_body else '<div style="color:#94A3B8;text-align:center;padding:20px;">Noch keine Daten</div>'}
</div>
<div style="padding-top: 8px; margin-top: 6px; text-align: center; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; color: #64748B; font-weight: 500;">
    Detaillierte Punkteaufschlüsselung in der Matrix unten
</div>
</div>""", unsafe_allow_html=True)

    # ====================================================
    # VOLLBREITE: 5 KPI KARTEN (UNTER DEN 3 SPALTEN)
    # ====================================================
    best_avg_row = res_df.loc[res_df['Gesamt Avg'].idxmax()] if not res_df.empty else None
    best_avg_val = f"{best_avg_row['Gesamt Avg']:.1f}" if best_avg_row is not None else "0.0"
    
    # 180er pro Spieler berechnen
    total_180s_df = res_df.groupby('Spieler')['180er'].sum().reset_index().set_index('Spieler') if not res_df.empty else pd.DataFrame(columns=['Spieler', '180er']).set_index('Spieler')
    if not doubles_df.empty:
        for _, row in doubles_df[doubles_df['special_type'].str.contains('180')].iterrows():
            p_name = row['player_name']
            if p_name in total_180s_df.index:
                total_180s_df.at[p_name, '180er'] += 1
            else:
                total_180s_df.loc[p_name] = {'180er': 1}
                
    total_180s_df = total_180s_df.reset_index()
    if not total_180s_df.empty and total_180s_df['180er'].sum() > 0:
        best_180_row = total_180s_df.loc[total_180s_df['180er'].idxmax()]
        best_180_val = int(best_180_row['180er'])
        best_180_name = get_short_name(best_180_row['Spieler'])
    else:
        best_180_val = 0
        best_180_name = "Noch offen"
        
    max_hf_row = res_df.loc[res_df['High Finishes'].idxmax()] if not res_df.empty else None
    
    # Bestes Short Game: Spieler mit den meisten Short-Game-Specials (aus Doppel-Specials)
    short_game_name = "Noch offen"
    short_game_val = 0
    if not doubles_df.empty:
        sg_df = doubles_df[doubles_df['special_type'].str.contains('Short', case=False)]
        if not sg_df.empty:
            sg_counts = sg_df.groupby('player_name').size().reset_index(name='count')
            best_sg = sg_counts.loc[sg_counts['count'].idxmax()]
            short_game_val = int(best_sg['count'])
            short_game_name = get_short_name(best_sg['player_name'])
    # Auch Einzel Short Legs berücksichtigen
    if not res_df.empty:
        sl_df = res_df.groupby('Spieler')['Short Legs'].sum().reset_index()
        for _, slr in sl_df.iterrows():
            if slr['Short Legs'] > 0:
                total_sl = int(slr['Short Legs'])
                if not doubles_df.empty:
                    sg_player = doubles_df[(doubles_df['player_name'] == slr['Spieler']) & (doubles_df['special_type'].str.contains('Short', case=False))]
                    total_sl += len(sg_player)
                if total_sl > short_game_val:
                    short_game_val = total_sl
                    short_game_name = get_short_name(slr['Spieler'])
    
    # Bestes Doppel: Doppel-Match mit dem höchsten Gesamt-Average
    best_doppel_avg = 0.0
    best_doppel_names = "Noch offen"
    if not doubles_matches_df.empty:
        best_dm_idx = doubles_matches_df['avg_total'].idxmax()
        best_dm_row = doubles_matches_df.loc[best_dm_idx]
        best_doppel_avg = float(best_dm_row['avg_total'])
        best_doppel_names = f"{get_short_name(best_dm_row['p1_name'])} & {get_short_name(best_dm_row['p2_name'])}"

    st.markdown(f"""<div style="display: flex; gap: 12px; width: 100%; margin-top: 14px; margin-bottom: 8px;">
<div class="kpi-box" style="flex: 1; min-width: 0;">
<div class="kpi-tag">HIGHEST AVERAGE</div>
<div class="kpi-main" style="color: #00D4FF;">Ø {best_avg_val}</div>
<div class="kpi-sub">{get_short_name(best_avg_row['Spieler']) if best_avg_row is not None else '-'}</div>
</div>
<div class="kpi-box" style="flex: 1; min-width: 0;">
<div class="kpi-tag">MEISTE 180er</div>
<div class="kpi-main" style="color: #F8FAFC;">{best_180_val}</div>
<div class="kpi-sub">{best_180_name}</div>
</div>
<div class="kpi-box" style="flex: 1; min-width: 0;">
<div class="kpi-tag">HIGH FINISH</div>
<div class="kpi-main" style="color: #00D4FF;">{int(max_hf_row['High Finishes']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else '0'}</div>
<div class="kpi-sub">{get_short_name(max_hf_row['Spieler']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else 'Noch offen'}</div>
</div>
<div class="kpi-box" style="flex: 1; min-width: 0;">
<div class="kpi-tag">SHORT GAME</div>
<div class="kpi-main" style="color: #34D399;">{short_game_val}</div>
<div class="kpi-sub">{short_game_name}</div>
</div>
<div class="kpi-box" style="flex: 1; min-width: 0;">
<div class="kpi-tag">BESTES DOPPEL</div>
<div class="kpi-main" style="color: #F59E0B;">Ø {best_doppel_avg:.1f}</div>
<div class="kpi-sub">{best_doppel_names}</div>
</div>
</div>""", unsafe_allow_html=True)

    # ----------------------------------------------------
    # VOLLSTÄNDIGE PUNKTE-AUFSCHLÜSSELUNG (LEADERBOARD MATRIX)
    # ----------------------------------------------------
    if not res_df.empty:
        b_rows = []
        for _, m in matches_df.iterrows():
            perf = calculate_match_performance(m.to_dict(), settings)
            b_rows.append({
                'Spieler': m['player_name'],
                'Team': m['team'],
                'Match_ID': m['id'],
                'pts_win_w': perf['pts_win'] * (settings['win_weight'] / 100.0),
                'pts_avg_w': perf['pts_avg'] * (settings['avg_weight'] / 100.0),
                'pts_9_18_w': (perf['pts_avg9'] * (settings['avg9_weight'] / 100.0)) + (perf['pts_avg18'] * (settings['avg18_weight'] / 100.0)),
                'pts_scores_w': perf['pts_scores'] * (settings['scores_weight'] / 100.0),
                'specials_bonus': perf['specials_bonus'],
                'total_rating': perf['total_rating']
            })

        b_df = pd.DataFrame(b_rows)
        b_summary = b_df.groupby('Spieler').agg({
            'Match_ID': 'count',
            'pts_win_w': 'mean',
            'pts_avg_w': 'mean',
            'pts_9_18_w': 'mean',
            'pts_scores_w': 'mean',
            'specials_bonus': 'sum'
        }).reset_index()

        b_summary['doppel_bonus'] = b_summary['Spieler'].map(lambda p: doubles_bonus_map.get(p, 0.0))
        b_summary['total_specials_bonus'] = b_summary['specials_bonus'] + b_summary['doppel_bonus']
        b_summary['base_score'] = b_summary['pts_win_w'] + b_summary['pts_avg_w'] + b_summary['pts_9_18_w'] + b_summary['pts_scores_w']
        b_summary['final_score'] = b_summary['base_score'] + b_summary['total_specials_bonus']
        b_summary = b_summary.sort_values(by='final_score', ascending=False).reset_index(drop=True)

        table_rows_html = ""
        for idx, brow in b_summary.iterrows():
            rank_n = idx + 1
            p_name = brow['Spieler']
            sp_cnt = int(brow['Match_ID'])
            win_p = brow['pts_win_w']
            avg_p = brow['pts_avg_w']
            nine_p = brow['pts_9_18_w']
            scores_p = brow['pts_scores_w']
            spec_tot = brow['total_specials_bonus']
            tot_p = brow['final_score']
            
            av_mini = get_avatar_svg(p_name, "rgba(255,255,255,0.15)", 26)
            row_bg = "rgba(255, 255, 255, 0.02)" if idx % 2 == 0 else "transparent"
            
            spec_str = f"+{spec_tot:.2f}" if spec_tot > 0 else "-"
            spec_color = "#34D399" if spec_tot > 0 else "#64748B"
            
            table_rows_html += f"""<tr style="background: {row_bg}; border-bottom: 1px solid rgba(255, 255, 255, 0.04); transition: background 0.15s;">
<td style="padding: 10px 8px; text-align: center; font-weight: 700; color: #94A3B8; font-size: 12.5px;">{rank_n}</td>
<td style="padding: 10px 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<div style="flex-shrink: 0;">{av_mini}</div>
<span style="font-weight: 600; color: #F8FAFC; font-size: 13.5px;">{p_name}</span>
</div>
</td>
<td style="padding: 10px 8px; text-align: center; color: #94A3B8; font-weight: 500; font-size: 13px;">{sp_cnt}</td>
<td style="padding: 10px 8px; text-align: right; color: #E2E8F0; font-weight: 500; font-size: 13px;">{win_p:.2f}</td>
<td style="padding: 10px 8px; text-align: right; color: #E2E8F0; font-weight: 500; font-size: 13px;">{avg_p:.2f}</td>
<td style="padding: 10px 8px; text-align: right; color: #E2E8F0; font-weight: 500; font-size: 13px;">{nine_p:.2f}</td>
<td style="padding: 10px 8px; text-align: right; color: #E2E8F0; font-weight: 500; font-size: 13px;">{scores_p:.2f}</td>
<td style="padding: 10px 8px; text-align: right; color: {spec_color}; font-weight: 600; font-size: 13px;">{spec_str}</td>
<td style="padding: 10px 12px; text-align: right; color: #00D4FF; font-weight: 800; font-size: 14.5px;">{tot_p:.2f}</td>
</tr>"""

        st.markdown(f"""<div class="mockup-card" style="margin-top: 20px; margin-bottom: 20px; padding: 20px 22px;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 12px; margin-bottom: 14px;">
<div>
<div style="font-size: 14px; font-weight: 700; color: #F8FAFC; letter-spacing: 0.75px; text-transform: uppercase;">
PUNKTE-AUFSCHLÜSSELUNG DER RANGLISTE
</div>
<div style="font-size: 12px; color: #64748B; margin-top: 2px;">
Zusammensetzung der Ranking-Punkte nach offizieller Gewichtung der Lions League
</div>
</div>
<div style="display: flex; gap: 6px; font-size: 11px; flex-wrap: wrap;">
<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); color: #94A3B8; border-radius: 4px; padding: 3px 8px; font-weight: 600;">Siege: 50%</span>
<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); color: #94A3B8; border-radius: 4px; padding: 3px 8px; font-weight: 600;">3D-Avg: 20%</span>
<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); color: #94A3B8; border-radius: 4px; padding: 3px 8px; font-weight: 600;">9/18D: 15%</span>
<span style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); color: #94A3B8; border-radius: 4px; padding: 3px 8px; font-weight: 600;">Scores: 15%</span>
<span style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); color: #34D399; border-radius: 4px; padding: 3px 8px; font-weight: 600;">Specials: +0.50</span>
</div>
</div>
<div style="overflow-x: auto;">
<table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
<thead>
<tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); color: #64748B; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;">
<th style="padding: 8px; width: 40px; text-align: center;">#</th>
<th style="padding: 8px;">Spieler</th>
<th style="padding: 8px; width: 75px; text-align: center;">Spiele</th>
<th style="padding: 8px; text-align: right; color: #94A3B8;" title="Punkte aus gewonnenen Matches (50% Gewichtung, max 2.50 Pkt)">Sieg (50%)</th>
<th style="padding: 8px; text-align: right; color: #94A3B8;" title="Punkte aus dem 3-Dart Gesamtaverage (20% Gewichtung, max 1.40 Pkt)">Avg (20%)</th>
<th style="padding: 8px; text-align: right; color: #94A3B8;" title="Punkte aus First 9 & 18 Darts Average (7.5% + 7.5% Gewichtung, max 1.05 Pkt)">9/18D (15%)</th>
<th style="padding: 8px; text-align: right; color: #94A3B8;" title="Punkte aus High Scores 80+/100+/140+/180 pro Leg (15% Gewichtung, max 1.50 Pkt)">Scores (15%)</th>
<th style="padding: 8px; text-align: right; color: #34D399;" title="Bonus für alle Specials (Einzel & Doppel): +0.50 Pkt pro 180er, HF 101+, Short Leg ≤18 Darts">Specials</th>
<th style="padding: 8px 12px; text-align: right; color: #00D4FF; font-weight: 800; font-size: 12px;">GESAMT</th>
</tr>
</thead>
<tbody>
{table_rows_html}
</tbody>
</table>
</div>
<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.04); font-size: 11px; color: #64748B; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
<span><b>Formel:</b> <i>Gesamt = Sieg (50%) + Avg (20%) + 9/18D (15%) + Scores (15%) + Specials</i></span>
<span style="color: #94A3B8;">Max. Basiswertung pro Spiel: <b>6,45 Pkt</b> (+ Specials)</span>
</div>
</div>""", unsafe_allow_html=True)

    # ----------------------------------------------------
    # DETAILANALYSE INKLUSIVE DOPPEL-SPECIALS
    # ----------------------------------------------------
    with st.expander("🔍 Spieler-Detailanalyse & Match-Historie"):
        _p_df = get_players()
        if not _p_df.empty and 'team' in _p_df.columns:
            all_players_list = sorted(_p_df[_p_df['team'].isin(['A-Team', 'B-Team'])]['name'].tolist())
        else:
            all_players_list = sorted(_p_df['name'].tolist()) if not _p_df.empty else []
        detail_player = st.selectbox("Spieler für Detailanalyse", all_players_list, key="deep_dive_player")
        
        p_matches = res_df[res_df['Spieler'] == detail_player].sort_values('Match_ID') if not res_df.empty else pd.DataFrame()
        p_doubles = doubles_df[doubles_df['player_name'] == detail_player] if not doubles_df.empty else pd.DataFrame()
        
        # Doppel-Matches des Spielers ermitteln
        if not doubles_matches_df.empty:
            p_dm = doubles_matches_df[(doubles_matches_df['p1_name'] == detail_player) | (doubles_matches_df['p2_name'] == detail_player)].copy()
        else:
            p_dm = pd.DataFrame()
        dm_wins = len(p_dm[p_dm['legs_won'] > p_dm['legs_lost']]) if not p_dm.empty else 0
        dm_count = len(p_dm)
        single_wins = int(p_matches['Is_Win'].sum()) if not p_matches.empty else 0
        single_count = len(p_matches)
        
        d_bonus = len(p_doubles) * 0.5
        single_avg_rating = p_matches['Rating'].mean() if not p_matches.empty else 0.0
        total_rating = single_avg_rating + d_bonus
        
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        with p_c1: st.metric("Gesamt-Rating", f"{total_rating:.2f} Pkt", delta=f"+{d_bonus:.1f} Pkt (Doppel)" if d_bonus > 0 else None)
        with p_c2: st.metric("Gesamt-Average (Einzel)", f"{p_matches['Gesamt Avg'].mean():.1f}" if not p_matches.empty else "-")
        with p_c3: st.metric("Siege (Einzel | Doppel)", f"🎯 {single_wins}/{single_count}  •  👥 {dm_wins}/{dm_count}")
        with p_c4: st.metric("Specials (Einzel + Doppel)", f"{int(p_matches['Specials'].sum() if not p_matches.empty else 0)} + {len(p_doubles)}")
            
        if not p_matches.empty:
            st.markdown("#### 🎯 Einzel-Matches")
            st.dataframe(
                p_matches[['Datum', 'Gegner', 'Sieg', 'Legs_Won', 'Legs_Lost', 'Rating', 'Gesamt Avg', '9D Avg', '18D Avg', 'Scores/Leg', 'Specials']].style.format({
                    'Rating': '{:.2f} Pkt',
                    'Gesamt Avg': '{:.1f}',
                    '9D Avg': '{:.1f}',
                    '18D Avg': '{:.1f}',
                    'Scores/Leg': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )
            
        if not p_dm.empty:
            st.markdown("#### 👥 Doppel-Matches")
            p_dm['Datum'] = pd.to_datetime(p_dm['match_date']).dt.strftime('%d.%m.%Y')
            p_dm['Partner'] = p_dm.apply(lambda r: r['p2_name'] if r['p1_name'] == detail_player else r['p1_name'], axis=1)
            p_dm['Gegner'] = p_dm['opponent']
            p_dm['Sieg'] = p_dm.apply(lambda r: '✅' if r['legs_won'] > r['legs_lost'] else '❌', axis=1)
            p_dm['Legs'] = p_dm.apply(lambda r: f"{int(r['legs_won'])}:{int(r['legs_lost'])}", axis=1)
            p_dm['Scores (80+)'] = p_dm['scores_80'] + p_dm['scores_100'] + p_dm['scores_140'] + p_dm['scores_180']
            
            st.dataframe(
                p_dm[['Datum', 'Partner', 'Gegner', 'Sieg', 'Legs', 'avg_total', 'avg_9', 'avg_18', 'Scores (80+)', 'scores_180', 'high_finishes', 'short_legs', 'specials_count']].rename(columns={
                    'avg_total': 'Gesamt Avg',
                    'avg_9': '9D Avg',
                    'avg_18': '18D Avg',
                    'scores_180': '180er',
                    'high_finishes': 'High Finish',
                    'short_legs': 'Short Legs',
                    'specials_count': 'Specials'
                }).style.format({
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
                    'special_type': 'Geworfenes Special',
                    'partner_name': 'Teampartner',
                    'opponent_team': 'Gegnerisches Team',
                    'description': 'Details / Notiz'
                }),
                use_container_width=True,
                hide_index=True
            )

# Footer
st.markdown("""<div style='text-align: center; margin-top: 30px; color: #64748B; font-size: 12px; border-top: 1px solid rgba(0,212,255,0.15); padding-top: 15px;'>
🦁 <b>Lions Weyhausen</b> • Dartsport im Sportclub Weyhausen von 1921 e.V. • <span style="color: #00D4FF; font-weight: 700;">Version V1.10</span><br>
Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)
</div>""", unsafe_allow_html=True)
