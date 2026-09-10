import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from utils import apply_custom_theme, require_admin, render_sidebar_auth, render_impressum_footer
from database import get_matches, get_players, get_settings, get_doubles_specials, get_doubles_matches
from utils import calculate_match_performance, get_avatar_svg

def get_short_name(full_name):
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][0]}."
    return full_name

st.set_page_config(page_title="Lions League - Export", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_admin()

st.title("📄 Statischer HTML-Export (WhatsApp)")
st.caption("Generiert eine Offline-fähige HTML-Datei der aktuellen Rankings, die du per WhatsApp an die Spieler verschicken kannst.")

def generate_export_html():
    settings = get_settings()
    matches_df = get_matches()
    players_df = get_players()
    doubles_df = get_doubles_specials()
    doubles_matches_df = get_doubles_matches()
    
    # Ranking berechnen (wie in app.py)
    results = []
    if not matches_df.empty:
        for p_id in matches_df['player_id'].unique():
            p_matches = matches_df[matches_df['player_id'] == p_id]
            perf_sum = 0
            for _, m in p_matches.iterrows():
                perf = calculate_match_performance(m, settings)
                perf_sum += perf['total_rating']
                
            p_name = p_matches.iloc[0]['player_name']
            p_team = p_matches.iloc[0]['team']
            
            p_doubles = doubles_df[doubles_df['player_name'] == p_name]
            doubles_bonus = len(p_doubles) * 0.5
            
            p_avg_total = p_matches['avg_total'].mean()
            p_avg_9 = p_matches['avg_9'].mean()
            p_avg_18 = p_matches['avg_18'].mean()
            
            is_win_sum = sum([1 for _, m in p_matches.iterrows() if m['legs_won'] > m['legs_lost']])
            legs_won_sum = p_matches['legs_won'].sum()
            legs_lost_sum = p_matches['legs_lost'].sum()
            high_finishes = p_matches['high_finishes'].max()
            specials_sum = p_matches['specials_count'].sum()
            
            rating = (perf_sum / len(p_matches)) + doubles_bonus
            
            results.append({
                'Spieler': p_name,
                'Team': p_team,
                'Match_ID': len(p_matches),
                'Gesamt Avg': p_avg_total,
                '9D Avg': p_avg_9,
                '18D Avg': p_avg_18,
                'Rating': round(rating, 2),
                'Is_Win': is_win_sum,
                'Legs_Won': legs_won_sum,
                'Legs_Lost': legs_lost_sum,
                'High Finishes': high_finishes,
                'Specials': specials_sum,
                'Doubles_Bonus': doubles_bonus
            })
            
    res_df = pd.DataFrame(results)
    
    # Leaderboard HTML generieren
    leaderboard_html = ""
    if not res_df.empty:
        leaderboard = res_df.sort_values(by='Rating', ascending=False).reset_index(drop=True)
        for idx, row in leaderboard.iterrows():
            rank_num = idx + 1
            av_sm = get_avatar_svg(row['Spieler'], "#00D4FF", 26)
            bg = "rgba(255,255,255,0.05)" if idx % 2 == 0 else "transparent"
            name = get_short_name(row['Spieler'])
            spiele = int(row['Match_ID'])
            punkte = f"{row['Rating']:.2f}"
            
            leaderboard_html += f"""
            <div style="display:flex;align-items:center;padding:12px 10px;border-radius:10px;margin-bottom:6px;background:{bg};border:1px solid rgba(0,212,255,0.1);">
                <div style="width:30px;color:#00D4FF;font-weight:800;font-size:16px;">{rank_num}</div>
                <div style="width:36px;">{av_sm}</div>
                <div style="flex:1;font-weight:700;font-size:16px;color:#FFFFFF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
                <div style="width:50px;text-align:right;font-size:15px;color:#CBD5E1;font-weight:600;">{spiele}</div>
                <div style="width:60px;text-align:right;font-size:17px;color:#00D4FF;font-weight:900;">{punkte}</div>
            </div>
            """
            
        # TEAM BATTLE BERECHNEN
        team_a_df = res_df[res_df['Team'] == 'A-Team']
        team_b_df = res_df[res_df['Team'] == 'B-Team']
        
        avg_a = team_a_df['Gesamt Avg'].mean() if not team_a_df.empty else 0.0
        avg_b = team_b_df['Gesamt Avg'].mean() if not team_b_df.empty else 0.0
        
        avg9_a = team_a_df['9D Avg'].mean() if not team_a_df.empty else 0.0
        avg9_b = team_b_df['9D Avg'].mean() if not team_b_df.empty else 0.0
        
        avg18_a = team_a_df['18D Avg'].mean() if not team_a_df.empty else 0.0
        avg18_b = team_b_df['18D Avg'].mean() if not team_b_df.empty else 0.0
        
        sp_a = (team_a_df['Specials'].sum() if not team_a_df.empty else 0) + (len(doubles_df[doubles_df['team'] == 'A-Team']) if not doubles_df.empty else 0)
        sp_b = (team_b_df['Specials'].sum() if not team_b_df.empty else 0) + (len(doubles_df[doubles_df['team'] == 'B-Team']) if not doubles_df.empty else 0)
        
        wins_a = team_a_df['Is_Win'].sum() if not team_a_df.empty else 0
        wins_b = team_b_df['Is_Win'].sum() if not team_b_df.empty else 0
        
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
        
        team_battle_html = f"""
        <div class="card">
            <h2>🎯 Team-Battle</h2>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px;">
                <div class="team-pill-a" style="flex: 1; margin-right: 8px;">A-Team</div>
                <span style="font-weight: 900; color: #00D4FF; font-size: 16px; text-shadow: 0 0 10px #00D4FF;">VS</span>
                <div class="team-pill-b" style="flex: 1; margin-left: 8px;">B-Team</div>
            </div>

            <div class="battle-row"><span class="battle-val-a">{avg_a:.1f}</span><span class="battle-label">Gesamt-Average</span><span class="battle-val-b">{avg_b:.1f}</span></div>
            <div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_avg_a}%;"></div><div class="battle-bar-b" style="width: {bar_avg_b}%;"></div></div>

            <div class="battle-row"><span class="battle-val-a">{avg9_a:.1f}</span><span class="battle-label">Ø Avg 9 Darts</span><span class="battle-val-b">{avg9_b:.1f}</span></div>
            <div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a9_a}%;"></div><div class="battle-bar-b" style="width: {bar_a9_b}%;"></div></div>

            <div class="battle-row"><span class="battle-val-a">{avg18_a:.1f}</span><span class="battle-label">Ø Avg 18 Darts</span><span class="battle-val-b">{avg18_b:.1f}</span></div>
            <div class="battle-bar-wrap"><div class="battle-bar-a" style="width: {bar_a18_a}%;"></div><div class="battle-bar-b" style="width: {bar_a18_b}%;"></div></div>

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
        </div>
        """
        
    else:
        leaderboard_html = "<div style='color: #94A3B8; text-align: center; padding: 20px;'>Noch keine Spieldaten vorhanden.</div>"
        team_battle_html = ""

    # Basis HTML
    html_template = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lions League Ranking - {datetime.now().strftime('%d.%m.%Y')}</title>
        <style>
            body {{
                background-color: #061129;
                color: #FFFFFF;
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 15px;
            }}
            .card {{
                background: rgba(8, 20, 48, 0.78);
                border: 2px solid rgba(0, 212, 255, 0.4);
                border-radius: 20px;
                padding: 16px;
                margin-bottom: 20px;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }}
            h2 {{
                color: #FFFFFF;
                margin-top: 0;
                margin-bottom: 15px;
                text-align: center;
                font-size: 22px;
            }}
            .subtitle {{
                color: #CBD5E1;
                text-align: center;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            .header-row {{
                display: flex;
                align-items: center;
                padding: 0 10px 8px 10px;
                margin-bottom: 8px;
                border-bottom: 1px solid rgba(0, 212, 255, 0.2);
            }}
            .header-row > div {{
                font-size: 12px;
                font-weight: 700;
                color: #64748B;
                text-transform: uppercase;
            }}
            .footer {{
                text-align: center;
                color: #64748B;
                font-size: 12px;
                margin-top: 30px;
                margin-bottom: 30px;
            }}
            .team-pill-a {{
                background: linear-gradient(90deg, #00D4FF, #0284C7);
                color: #050B1A;
                font-weight: 900;
                font-size: 16px;
                padding: 8px 14px;
                border-radius: 25px;
                text-align: center;
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
            }}
            .team-pill-b {{
                background: linear-gradient(90deg, #1D4ED8, #3B82F6);
                color: #FFFFFF;
                font-weight: 900;
                font-size: 16px;
                padding: 8px 14px;
                border-radius: 25px;
                text-align: center;
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
            }}
            .battle-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin: 6px 0 3px 0;
            }}
            .battle-val-a {{
                color: #00D4FF;
                font-weight: 800;
                font-size: 16px;
                width: 45px;
                text-align: left;
            }}
            .battle-label {{
                color: #CBD5E1;
                font-weight: 600;
                font-size: 14px;
                flex: 1;
                text-align: center;
            }}
            .battle-val-b {{
                color: #60A5FA;
                font-weight: 800;
                font-size: 16px;
                width: 45px;
                text-align: right;
            }}
            .battle-bar-wrap {{
                display: flex;
                height: 6px;
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.12);
                overflow: hidden;
                margin-bottom: 8px;
            }}
            .battle-bar-a {{
                background: #00D4FF;
                height: 100%;
            }}
            .battle-bar-b {{
                background: #3B82F6;
                height: 100%;
            }}
        </style>
    </head>
    <body>
        <div style="text-align:center; margin-bottom: 15px;">
            <h1 style="color: #00D4FF; margin: 0; font-size: 28px; font-weight: 900;">LIONS LEAGUE</h1>
            <div style="color: #CBD5E1; font-size: 14px;">Saison 2026/27 (Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')})</div>
        </div>

        {team_battle_html}

        <div class="card">
            <h2>🏆 Rankings</h2>
            <div class="header-row">
                <div style="width:30px;">#</div>
                <div style="width:36px;"></div>
                <div style="flex:1;">Spieler</div>
                <div style="width:50px; text-align:right;">Spiele</div>
                <div style="width:60px; text-align:right; color:#00D4FF;">Punkte</div>
            </div>
            {leaderboard_html}
        </div>
        
        <div class="footer">
            🦁 <b>Lions Weyhausen</b> • Dartsport im SC Weyhausen
        </div>
    </body>
    </html>
    """
    
    return html_template

st.markdown("""
### WhatsApp Export Anleitung
Klicke auf den Button unten, um die aktuelle Rangliste als HTML-Datei herunterzuladen. 
Du kannst diese Datei dann ganz einfach als Dokument oder Anhang in eure WhatsApp-Gruppe schicken. 
Jeder Spieler kann die Datei auf seinem Handy anklicken und öffnet so das komplette Ranking in seinem Browser – **ganz ohne Login oder App-Installation.**
""")

if st.button("🔄 Export-Datei generieren", type="primary"):
    with st.spinner("Generiere Ranking-Datei..."):
        html_content = generate_export_html()
        
        st.success("Datei wurde erfolgreich generiert! Lade sie jetzt herunter:")
        
        # Download Button
        st.download_button(
            label="📥 Lions Ranking V1.html herunterladen",
            data=html_content,
            file_name=f"Lions_Ranking_V1_{datetime.now().strftime('%Y-%m-%d')}.html",
            mime="text/html"
        )

render_impressum_footer()
