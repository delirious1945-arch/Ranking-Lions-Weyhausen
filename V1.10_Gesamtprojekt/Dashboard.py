import streamlit as st
import pandas as pd
import datetime
from database import init_db, get_matches, get_settings, get_players, update_player_password, get_doubles_specials
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

st.set_page_config(page_title="Lions League - SC Weyhausen", layout="wide", page_icon="assets/logo.png")
init_db()
apply_custom_theme()
init_session_auth()

# ----------------------------------------------------
# 1. NEUTRALE LANDINGPAGE (OHNE SEITENLEISTE / PRIVACY-DATENSCHUTZ)
# ----------------------------------------------------
if not st.session_state['authenticated']:
    st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col_l, col_center, col_r = st.columns([1, 1.6, 1])
    with col_center:
        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        st.image("assets/logo.png", width=200)
        st.markdown("""
        <h1 style='text-align: center; color: #FFFFFF; font-size: 38px; margin-bottom: 0px; text-shadow: 0 0 25px rgba(0,212,255,0.6);'>
            LIONS LEAGUE
        </h1>
        <p style='text-align: center; color: #00D4FF; font-size: 16px; font-weight: 700; margin-top: 2px; letter-spacing: 0.5px;'>
            SC WEYHAUSEN VON 1921 E.V. • SPARTE DARTSPORT
        </p>
        <p style='text-align: center; color: #94A3B8; font-size: 13px;'>
            Geschlossenes Mitgliederportal der Lions Weyhausen.
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Erstanmeldung: Passwortänderung mit strengen Regeln
        if st.session_state.get('pending_pw_change'):
            with st.form("first_login_pw_form"):
                st.markdown("<h4 style='color: #00D4FF;'>🔑 Erstanmeldung: Neues Passwort festlegen</h4>", unsafe_allow_html=True)
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
                st.markdown("<h4 style='color: #00D4FF; margin-bottom: 12px;'>🔒 Mitglieder Login</h4>", unsafe_allow_html=True)
                
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
        <div style='text-align: center; margin-top: 30px; color: #64748B; font-size: 12px;'>
            © 2026 Sportclub Weyhausen von 1921 e.V. • Sparte Darts<br>
            Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ----------------------------------------------------
# 2. HAUPT-DASHBOARD (1:1 MOCKUP DESIGN)
# ----------------------------------------------------
render_sidebar_auth()

logo_b64 = get_base64_image("assets/logo.png")

# Top Header Bar
st.markdown(f"""<div style="background: rgba(8, 20, 48, 0.85); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 20px; padding: 10px 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 25px rgba(0, 212, 255, 0.15); backdrop-filter: blur(16px); margin-bottom: 20px;">
<div style="display: flex; align-items: center; gap: 14px;">
<img src="data:image/png;base64,{logo_b64}" width="42" height="42" style="border-radius: 50%; box-shadow: 0 0 10px #00D4FF;" />
<span style="font-weight: 800; font-size: 20px; color: #FFFFFF; letter-spacing: 1px; text-shadow: 0 0 10px rgba(0,212,255,0.5);">LIONS LEAGUE - SC WEYHAUSEN</span>
</div>
<div></div>
</div>""", unsafe_allow_html=True)

matches_df = get_matches()
settings = get_settings()
doubles_df = get_doubles_specials()

if matches_df.empty and doubles_df.empty:
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
        
        legs_a = team_a_df['Legs_Won'].sum() if not team_a_df.empty else 0
        legs_b = team_b_df['Legs_Won'].sum() if not team_b_df.empty else 0
        
        def calc_bar(val_a, val_b):
            tot = (val_a + val_b) if (val_a + val_b) > 0 else 1
            pct_a = min(max(int((val_a / tot) * 100), 20), 80)
            return pct_a, 100 - pct_a

        bar_avg_a, bar_avg_b = calc_bar(avg_a, avg_b)
        bar_a9_a, bar_a9_b = calc_bar(avg9_a, avg9_b)
        bar_a18_a, bar_a18_b = calc_bar(avg18_a, avg18_b)
        bar_win_a, bar_win_b = calc_bar(wins_a, wins_b)
        bar_leg_a, bar_leg_b = calc_bar(legs_a, legs_b)

        st.markdown(f"""<div class="mockup-card">
<div class="card-title"><span>Team-Battle</span><span class="icon">🎯</span></div>
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
<div class="team-pill-a" style="flex: 1; margin-right: 8px;">A-Team</div>
<span style="font-weight: 900; color: #00D4FF; font-size: 18px; text-shadow: 0 0 10px #00D4FF;">VS</span>
<div class="team-pill-b" style="flex: 1; margin-left: 8px;">B-Team</div>
</div>

<div class="battle-row"><span class="battle-val-a">{avg_a:.1f}</span><span class="battle-label">Gesamt-Average</span><span class="battle-val-b">{avg_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_avg_a}%;"></div><div class="battle-bar-b" style="width: {bar_avg_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{avg9_a:.1f}</span><span class="battle-label">Durchschnitts-Average 9 Darts</span><span class="battle-val-b">{avg9_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a9_a}%;"></div><div class="battle-bar-b" style="width: {bar_a9_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{avg18_a:.1f}</span><span class="battle-label">Durchschnitts-Average 18 Darts</span><span class="battle-val-b">{avg18_b:.1f}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a18_a}%;"></div><div class="battle-bar-b" style="width: {bar_a18_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(hf_a)}</span><span class="battle-label">High Finish</span><span class="battle-val-b">{int(hf_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: 50%;"></div><div class="battle-bar-b" style="width: 50%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(sp_a)}</span><span class="battle-label">Specials (inkl. Doppel)</span><span class="battle-val-b">{int(sp_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: 50%;"></div><div class="battle-bar-b" style="width: 50%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(wins_a)}</span><span class="battle-label">Wins</span><span class="battle-val-b">{int(wins_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_win_a}%;"></div><div class="battle-bar-b" style="width: {bar_win_b}%;"></div></div>

<div class="battle-row"><span class="battle-val-a">{int(legs_a)}</span><span class="battle-label">Gewonnene Legs</span><span class="battle-val-b">{int(legs_b)}</span></div>
<div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_leg_a}%;"></div><div class="battle-bar-b" style="width: {bar_leg_b}%;"></div></div>
</div>""", unsafe_allow_html=True)
        
        # 2. Row of 3 KPI Cards
        best_avg_row = res_df.loc[res_df['Gesamt Avg'].idxmax()] if not res_df.empty else None
        best_avg_val = f"{best_avg_row['Gesamt Avg']:.1f}" if best_avg_row is not None else "0.0"
        total_180s = (res_df['180er'].sum() if not res_df.empty else 0) + (len(doubles_df[doubles_df['special_type'].str.contains('180')]) if not doubles_df.empty else 0)
        max_hf_row = res_df.loc[res_df['High Finishes'].idxmax()] if not res_df.empty else None

        st.markdown(f"""<div style="display: flex; gap: 8px;">
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">HIGHEST AVERAGE</div>
<div class="kpi-main" style="color: #00D4FF;">{best_avg_val}</div>
<div style="font-size: 18px; margin: 2px 0;">🎯</div>
<div class="kpi-sub">{get_short_name(best_avg_row['Spieler']) if best_avg_row is not None else '-'}</div>
</div>
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">SEASON 180s</div>
<div class="kpi-main" style="color: #60A5FA;">{int(total_180s)}</div>
<div style="font-size: 18px; margin: 2px 0;">🏹</div>
<div class="kpi-sub">Gesamtes Team</div>
</div>
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">HIGH FINISHES</div>
<div class="kpi-main" style="color: #00D4FF;">{int(max_hf_row['High Finishes']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else '0'}</div>
<div style="font-size: 18px; margin: 2px 0;">🏁</div>
<div class="kpi-sub">{get_short_name(max_hf_row['Spieler']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else 'Noch offen'}</div>
</div>
</div>""", unsafe_allow_html=True)

    # ====================================================
    # SPALTE 2: TOP 3 PODIUM MIT ECHTEN FOTOS
    # ====================================================
    with col2:
        if not res_df.empty:
            top_month = res_df.groupby(['Spieler', 'Team'])['Rating'].mean().reset_index()
            top_month['Rating'] = top_month.apply(lambda r: r['Rating'] + doubles_bonus_map.get(r['Spieler'], 0.0), axis=1)
            top_month = top_month.sort_values(by='Rating', ascending=False).head(3).reset_index(drop=True)
        else:
            top_month = pd.DataFrame()
            
        p1 = top_month.iloc[0] if len(top_month) > 0 else {'Spieler': 'Offen', 'Rating': 0.0}
        p2 = top_month.iloc[1] if len(top_month) > 1 else {'Spieler': 'Offen', 'Rating': 0.0}
        p3 = top_month.iloc[2] if len(top_month) > 2 else {'Spieler': 'Offen', 'Rating': 0.0}
        
        av1 = get_avatar_svg(p1['Spieler'], "#FFD700", 68)
        av2 = get_avatar_svg(p2['Spieler'], "#C0C0C0", 54)
        av3 = get_avatar_svg(p3['Spieler'], "#CD7F32", 54)
        
        st.markdown(f"""<div class="mockup-card">
<div class="card-title"><span>Top 3 of the Month</span><span class="icon">🎯</span></div>
<div style="display: flex; align-items: flex-end; justify-content: center; gap: 8px; margin-top: 8px; min-height: 190px;">
<div style="flex: 1; text-align: center;">
{av2}
<div style="background: rgba(192, 192, 192, 0.12); border: 1px solid #C0C0C0; border-radius: 12px; padding: 6px 2px; margin-top: 6px;">
<div style="font-size: 13px; font-weight: 800; color: #C0C0C0;">2<sup>nd</sup></div>
<div style="font-size: 11px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p2['Spieler'])}</div>
<div style="font-size: 11px; color: #00D4FF; font-weight: 700;">{p2['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1.15; text-align: center; margin-bottom: 10px;">
{av1}
<div style="background: linear-gradient(180deg, rgba(255, 215, 0, 0.22), rgba(255, 215, 0, 0.05)); border: 2px solid #FFD700; border-radius: 14px; padding: 8px 2px; margin-top: 6px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);">
<div style="font-size: 16px; font-weight: 900; color: #FFD700;">1<sup>st</sup></div>
<div style="font-size: 12px; font-weight: 800; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p1['Spieler'])}</div>
<div style="font-size: 12px; color: #00D4FF; font-weight: 800;">{p1['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1; text-align: center;">
{av3}
<div style="background: rgba(205, 127, 50, 0.12); border: 1px solid #CD7F32; border-radius: 12px; padding: 6px 2px; margin-top: 6px;">
<div style="font-size: 13px; font-weight: 800; color: #CD7F32;">3<sup>rd</sup></div>
<div style="font-size: 11px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p3['Spieler'])}</div>
<div style="font-size: 11px; color: #00D4FF; font-weight: 700;">{p3['Rating']:.2f} Pkt</div>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
        
        # Highlights Box
        tot_specials = (res_df['Specials'].sum() if not res_df.empty else 0) + len(doubles_df)
        
        st.markdown(f"""<div class="mockup-card" style="margin-bottom: 0px;">
<div class="card-title"><span>SAISON HIGHLIGHTS</span><span class="icon">🏆</span></div>
<div style="display: flex; flex-direction: column; gap: 10px; padding: 4px 0;">
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(0,212,255,0.1);">
<div>
<div style="font-size: 11px; color: #94A3B8; font-weight: 600;">MEISTE SPECIALS (EINZEL & DOPPEL)</div>
<div style="font-size: 14px; font-weight: 700; color: #FFFFFF;">{int(tot_specials)} Specials gesamt</div>
</div>
<div style="font-size: 20px;">⚡</div>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(0,212,255,0.1);">
<div>
<div style="font-size: 11px; color: #94A3B8; font-weight: 600;">GEWORFENE DOPPEL-SPECIALS</div>
<div style="font-size: 14px; font-weight: 700; color: #00D4FF;">{len(doubles_df)} Doppel-Specials (+{len(doubles_df)*0.5:.1f} Pkt)</div>
</div>
<div style="font-size: 20px;">🤝</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # ====================================================
    # SPALTE 3: RANKINGS (MIT DOPPEL-BONUS)
    # ====================================================
    with col3:
        if not res_df.empty:
            leaderboard = res_df.groupby(['Spieler', 'Team']).agg({
                'Rating': 'mean',
                'Gesamt Avg': 'mean',
                'Match_ID': 'count'
            }).reset_index()
            leaderboard['Rating'] = leaderboard.apply(lambda r: r['Rating'] + doubles_bonus_map.get(r['Spieler'], 0.0), axis=1)
            leaderboard = leaderboard.sort_values(by='Rating', ascending=False).reset_index(drop=True)
        else:
            leaderboard = pd.DataFrame()
        
        rankings_rows_html = ""
        for idx, r_row in leaderboard.iterrows():
            rank_num = idx + 1
            av_sm = get_avatar_svg(r_row['Spieler'], "#00D4FF", 26)
            
            rankings_rows_html += f"""<div class="rank-row">
<div class="rank-num">{rank_num}</div>
<div>{av_sm}</div>
<div class="rank-name">{get_short_name(r_row['Spieler'])}</div>
<div class="rank-stat">{int(r_row['Match_ID'])}</div>
<div class="rank-pts">{r_row['Rating']:.2f}</div>
<div class="rank-stat">{r_row['Gesamt Avg']:.1f}</div>
</div>"""
            
        st.markdown(f"""<div class="mockup-card" style="height: calc(100% - 16px); min-height: 520px;">
<div class="card-title"><span>RANKINGS</span><span class="icon">🎯</span></div>
<div style="display: flex; padding: 0 10px 8px 10px; font-size: 11px; font-weight: 700; color: #64748B; letter-spacing: 0.5px; text-transform: uppercase;">
<div style="width: 25px;">Rank</div>
<div style="width: 32px;"></div>
<div style="flex: 1;">Player</div>
<div style="width: 45px; text-align: right;">Played</div>
<div style="width: 55px; text-align: right; color: #00D4FF;">Points</div>
<div style="width: 45px; text-align: right;">Avg.</div>
</div>
<div style="max-height: 440px; overflow-y: auto; padding-right: 4px;">
{rankings_rows_html if rankings_rows_html else '<div style="color: #94A3B8; text-align: center; padding: 20px;">Noch keine Daten</div>'}
</div>
</div>""", unsafe_allow_html=True)

    # ----------------------------------------------------
    # DETAILANALYSE INKLUSIVE DOPPEL-SPECIALS
    # ----------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔍 Spieler-Detailanalyse & Match-Historie"):
        all_players_list = sorted(get_players()['name'].tolist())
        detail_player = st.selectbox("Spieler für Detailanalyse", all_players_list, key="deep_dive_player")
        
        p_matches = res_df[res_df['Spieler'] == detail_player].sort_values('Match_ID') if not res_df.empty else pd.DataFrame()
        p_doubles = doubles_df[doubles_df['player_name'] == detail_player] if not doubles_df.empty else pd.DataFrame()
        
        d_bonus = len(p_doubles) * 0.5
        single_avg_rating = p_matches['Rating'].mean() if not p_matches.empty else 0.0
        total_rating = single_avg_rating + d_bonus
        
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        with p_c1: st.metric("Gesamt-Rating", f"{total_rating:.2f} Pkt", delta=f"+{d_bonus:.1f} Pkt (Doppel)" if d_bonus > 0 else None)
        with p_c2: st.metric("Gesamt-Average", f"{p_matches['Gesamt Avg'].mean():.1f}" if not p_matches.empty else "-")
        with p_c3: st.metric("Einzel-Bilanz (Siege)", f"{p_matches['Is_Win'].sum()} / {len(p_matches)}" if not p_matches.empty else "0 / 0")
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
🦁 <b>Lions Weyhausen</b> • Dartsport im Sportclub Weyhausen von 1921 e.V.<br>
Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)
</div>""", unsafe_allow_html=True)
