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
    validate_password_strength,
    render_impressum_footer
)

st.set_page_config(page_title="Lions League - SC Weyhausen", layout="wide", page_icon="assets/logo.png")
init_db()
apply_custom_theme()
init_session_auth()

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
        st.image("assets/logo.png", width=220)
        st.markdown("""
        <h1 style='text-align: center; color: #FFFFFF; font-size: 42px; margin-bottom: 0px; text-shadow: 0 0 25px rgba(0,212,255,0.6);'>
            LIONS LEAGUE
        </h1>
        <p style='text-align: center; color: #00D4FF; font-size: 19px; font-weight: 700; margin-top: 2px; letter-spacing: 0.5px;'>
            SC WEYHAUSEN VON 1921 E.V. • SPARTE DARTSPORT
        </p>
        <p style='text-align: center; color: #94A3B8; font-size: 15px;'>
            Geschlossenes Mitgliederportal der Lions Weyhausen.
        </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.session_state.get('pending_pw_change'):
            with st.form("first_login_pw_form"):
                st.markdown("<h4 style='color: #00D4FF; font-size: 22px;'>🔑 Erstanmeldung: Neues Passwort festlegen</h4>", unsafe_allow_html=True)
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
                st.markdown("<h4 style='color: #00D4FF; margin-bottom: 12px; font-size: 22px;'>🔒 Mitglieder Login</h4>", unsafe_allow_html=True)
                
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
        
        render_impressum_footer()
    st.stop()

render_sidebar_auth()

logo_b64 = get_base64_image("assets/logo.png")

st.markdown(f"""<div style="background: rgba(8, 20, 48, 0.85); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 20px; padding: 12px 26px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 25px rgba(0, 212, 255, 0.15); backdrop-filter: blur(16px); margin-bottom: 20px;">
<div style="display: flex; align-items: center; gap: 16px;">
<img src="data:image/png;base64,{logo_b64}" width="48" height="48" style="border-radius: 50%; box-shadow: 0 0 12px #00D4FF;" />
<span style="font-weight: 900; font-size: 24px; color: #FFFFFF; letter-spacing: 1px; text-shadow: 0 0 12px rgba(0,212,255,0.5);">LIONS LEAGUE - SC WEYHAUSEN</span>
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

    col1, col2, col3 = st.columns([1.1, 1.1, 1.1])
    
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
        legs_b = team_b_df['Legs_Lost'].sum() if not team_b_df.empty else 0
        
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
<span style="font-weight: 900; color: #00D4FF; font-size: 20px; text-shadow: 0 0 10px #00D4FF;">VS</span>
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
        
        best_avg_row = res_df.loc[res_df['Gesamt Avg'].idxmax()] if not res_df.empty else None
        best_avg_val = f"{best_avg_row['Gesamt Avg']:.1f}" if best_avg_row is not None else "0.0"
        total_180s = (res_df['180er'].sum() if not res_df.empty else 0) + (len(doubles_df[doubles_df['special_type'].str.contains('180')]) if not doubles_df.empty else 0)
        max_hf_row = res_df.loc[res_df['High Finishes'].idxmax()] if not res_df.empty else None

        st.markdown(f"""<div style="display: flex; gap: 10px;">
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">HIGHEST AVERAGE</div>
<div class="kpi-main" style="color: #00D4FF;">{best_avg_val}</div>
<div style="font-size: 20px; margin: 2px 0;">🎯</div>
<div class="kpi-sub">{get_short_name(best_avg_row['Spieler']) if best_avg_row is not None else '-'}</div>
</div>
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">SEASON 180s</div>
<div class="kpi-main" style="color: #60A5FA;">{int(total_180s)}</div>
<div style="font-size: 20px; margin: 2px 0;">🏹</div>
<div class="kpi-sub">Gesamtes Team</div>
</div>
<div class="kpi-box" style="flex: 1;">
<div class="kpi-tag">HIGH FINISHES</div>
<div class="kpi-main" style="color: #00D4FF;">{int(max_hf_row['High Finishes']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else '0'}</div>
<div style="font-size: 20px; margin: 2px 0;">🏁</div>
<div class="kpi-sub">{get_short_name(max_hf_row['Spieler']) if (max_hf_row is not None and max_hf_row['High Finishes'] > 0) else 'Noch offen'}</div>
</div>
</div>""", unsafe_allow_html=True)

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
        
        av1 = get_avatar_svg(p1['Spieler'], "#FFD700", 78)
        av2 = get_avatar_svg(p2['Spieler'], "#C0C0C0", 64)
        av3 = get_avatar_svg(p3['Spieler'], "#CD7F32", 64)
        
        st.markdown(f"""<div class="mockup-card">
<div class="card-title"><span>Top 3 of the Month</span><span class="icon">🎯</span></div>
<div style="display: flex; align-items: flex-end; justify-content: center; gap: 10px; margin-top: 10px; min-height: 210px;">
<div style="flex: 1; text-align: center;">
{av2}
<div style="background: rgba(192, 192, 192, 0.12); border: 1px solid #C0C0C0; border-radius: 14px; padding: 8px 4px; margin-top: 8px;">
<div style="font-size: 15px; font-weight: 800; color: #C0C0C0;">2<sup>nd</sup></div>
<div style="font-size: 14px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p2['Spieler'])}</div>
<div style="font-size: 14px; color: #00D4FF; font-weight: 800;">{p2['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1.15; text-align: center; margin-bottom: 12px;">
{av1}
<div style="background: linear-gradient(180deg, rgba(255, 215, 0, 0.22), rgba(255, 215, 0, 0.05)); border: 2px solid #FFD700; border-radius: 16px; padding: 10px 4px; margin-top: 8px; box-shadow: 0 0 18px rgba(255, 215, 0, 0.35);">
<div style="font-size: 18px; font-weight: 900; color: #FFD700;">1<sup>st</sup></div>
<div style="font-size: 15px; font-weight: 800; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p1['Spieler'])}</div>
<div style="font-size: 15px; color: #00D4FF; font-weight: 900;">{p1['Rating']:.2f} Pkt</div>
</div>
</div>
<div style="flex: 1; text-align: center;">
{av3}
<div style="background: rgba(205, 127, 50, 0.12); border: 1px solid #CD7F32; border-radius: 14px; padding: 8px 4px; margin-top: 8px;">
<div style="font-size: 15px; font-weight: 800; color: #CD7F32;">3<sup>rd</sup></div>
<div style="font-size: 14px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{get_short_name(p3['Spieler'])}</div>
<div style="font-size: 14px; color: #00D4FF; font-weight: 800;">{p3['Rating']:.2f} Pkt</div>
</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
        
        tot_specials = (res_df['Specials'].sum() if not res_df.empty else 0) + len(doubles_df)
        
        st.markdown(f"""<div class="mockup-card" style="margin-bottom: 0px;">
<div class="card-title"><span>SAISON HIGHLIGHTS</span><span class="icon">🏆</span></div>
<div style="display: flex; flex-direction: column; gap: 12px; padding: 4px 0;">
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.04); padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(0,212,255,0.15);">
<div>
<div style="font-size: 13px; color: #94A3B8; font-weight: 600;">MEISTE SPECIALS (EINZEL & DOPPEL)</div>
<div style="font-size: 17px; font-weight: 800; color: #FFFFFF;">{int(tot_specials)} Specials gesamt</div>
</div>
<div style="font-size: 24px;">⚡</div>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.04); padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(0,212,255,0.15);">
<div>
<div style="font-size: 13px; color: #94A3B8; font-weight: 600;">GEWORFENE DOPPEL-SPECIALS</div>
<div style="font-size: 17px; font-weight: 800; color: #00D4FF;">{len(doubles_df)} Doppel-Specials (+{len(doubles_df)*0.5:.1f} Pkt)</div>
</div>
<div style="font-size: 24px;">🤝</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

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
            av_sm = get_avatar_svg(r_row['Spieler'], "#00D4FF", 32)
            
            rankings_rows_html += f"""<div class="rank-row">
<div class="rank-num">{rank_num}</div>
<div>{av_sm}</div>
<div class="rank-name">{get_short_name(r_row['Spieler'])}</div>
<div class="rank-stat">{int(r_row['Match_ID'])}</div>
<div class="rank-pts">{r_row['Rating']:.2f}</div>
</div>"""
            
        # RANKINGS KACHEL AUF GLEICHE HÖHE WIE SPALTE 1 STRECKEN
        rankings_header = """<div style="display:flex;align-items:center;padding:0 8px 10px 8px;gap:4px;">
<div style="width:28px;font-size:11px;font-weight:700;color:#64748B;flex-shrink:0;">#</div>
<div style="width:36px;flex-shrink:0;"></div>
<div style="flex:1;font-size:11px;font-weight:700;color:#64748B;padding-left:6px;white-space:nowrap;">Spieler</div>
<div style="width:48px;text-align:right;font-size:11px;font-weight:700;color:#64748B;white-space:nowrap;flex-shrink:0;">Spiele</div>
<div style="width:64px;text-align:right;font-size:11px;font-weight:700;color:#00D4FF;white-space:nowrap;flex-shrink:0;">Punkte</div>
</div>"""

        rankings_body = ""
        for idx, r_row in leaderboard.iterrows():
            rank_num = idx + 1
            av_sm = get_avatar_svg(r_row['Spieler'], "#00D4FF", 30)
            bg = "rgba(255,255,255,0.05)" if idx % 2 == 0 else "transparent"
            rankings_body += f"""<div style="display:flex;align-items:center;padding:8px;border-radius:10px;margin-bottom:6px;background:{bg};border:1px solid rgba(0,212,255,0.1);gap:4px;">
<div style="width:28px;color:#00D4FF;font-weight:800;font-size:16px;flex-shrink:0;">{rank_num}</div>
<div style="width:36px;flex-shrink:0;">{av_sm}</div>
<div style="flex:1;font-weight:700;font-size:16px;color:#FFFFFF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding-left:6px;">{get_short_name(r_row['Spieler'])}</div>
<div style="width:48px;text-align:right;font-size:15px;color:#CBD5E1;font-weight:600;flex-shrink:0;">{int(r_row['Match_ID'])}</div>
<div style="width:64px;text-align:right;font-size:17px;color:#00D4FF;font-weight:900;flex-shrink:0;">{r_row['Rating']:.2f}</div>
</div>"""

        st.markdown(f"""<div class="mockup-card" style="min-height:720px;margin-bottom:0px;">
<div class="card-title"><span>RANKINGS</span><span class="icon">🎯</span></div>
{rankings_header}
<div style="max-height:620px;overflow-y:auto;padding-right:4px;">
{rankings_body if rankings_body else '<div style="color:#94A3B8;text-align:center;padding:20px;">Noch keine Daten</div>'}
</div>
</div>""", unsafe_allow_html=True)

render_impressum_footer()
