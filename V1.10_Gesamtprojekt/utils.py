import streamlit as st
import base64
import os
import re
import sqlite3
from database import DB_PATH, get_connection, update_player_password

def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

def validate_password_strength(password):
    p = password.strip()
    if len(p) < 10:
        return False, "Das Passwort muss mindestens 10 Zeichen lang sein."
    if not any(c.isdigit() for c in p):
        return False, "Das Passwort muss mindestens eine Zahl (0-9) enthalten."
    if not re.search(r"[^a-zA-Z0-9]", p):
        return False, "Das Passwort muss mindestens ein Sonderzeichen (z.B. !, ?, @, #, $, %, -, _) enthalten."
    return True, "Gültig"

def get_player_photo_path(name):
    folder = "assets/players"
    if not os.path.exists(folder):
        return None
    name_clean = name.strip().lower()
    files = os.listdir(folder)
    
    for f in files:
        if os.path.splitext(f)[0].lower() == name_clean:
            return os.path.join(folder, f)
            
    for f in files:
        f_no_ext = os.path.splitext(f)[0].lower()
        if f_no_ext == name_clean or name_clean in f_no_ext:
            return os.path.join(folder, f)
            
    if 'nicholas' in name_clean or 'nick' in name_clean:
        for f in files:
            if 'nick' in f.lower(): return os.path.join(folder, f)
    if 'lucas' in name_clean or 'lukas' in name_clean:
        for f in files:
            if 'lukas' in f.lower(): return os.path.join(folder, f)
    if 'andré' in name_clean or 'andre' in name_clean:
        for f in files:
            if f.lower().startswith('andr'): return os.path.join(folder, f)
            
    first = name_clean.split()[0]
    for f in files:
        f_no_ext = os.path.splitext(f)[0].lower()
        if f_no_ext == first:
            return os.path.join(folder, f)
            
    return None

def get_avatar_svg(name, border_color="#00D4FF", size=70):
    photo_path = get_player_photo_path(name)
    if photo_path and os.path.exists(photo_path):
        img_b64 = get_base64_image(photo_path)
        ext = "png" if photo_path.endswith(".png") else "jpeg"
        return f'<img src="data:image/{ext};base64,{img_b64}" style="width:{size}px;height:{size}px;border-radius:50%;border:3px solid {border_color};box-shadow:0 0 15px {border_color}88;object-fit:cover;display:block;margin:0 auto;" />'
    
    parts = name.strip().split()
    initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "🎯"
    font_s = max(int(size * 0.36), 14)
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#0A1936,#1E3A8A);border:3px solid {border_color};box-shadow:0 0 15px {border_color}88;display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:800;font-size:{font_s}px;letter-spacing:1px;margin:0 auto;">{initials}</div>'

def apply_custom_theme():
    bg_b64 = get_base64_image("assets/bg.jpg")
    bg_css = f"""
        background-image: linear-gradient(rgba(5, 11, 26, 0.78), rgba(3, 7, 18, 0.88)), url('data:image/jpeg;base64,{bg_b64}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """ if bg_b64 else "background: #050B1A;"

    st.markdown(f"""
    <style>
    /* Erste Seite in der Navigationsleiste immer zwingend als 'Startseite' beschriften */
    [data-testid="stSidebarNav"] li:first-child a span {{
        display: none !important;
    }}
    [data-testid="stSidebarNav"] li:first-child a::after {{
        content: "Startseite" !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin-left: 8px !important;
    }}

    /* Global Doppelte Schriftgröße */
    html, body, [data-testid="stAppViewContainer"] {{
        {bg_css}
        color: #FFFFFF !important;
        font-size: 19px !important;
    }}
    
    p, span, div, label, input, button, select {{
        font-size: 19px !important;
    }}
    
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: rgba(5, 12, 30, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 2px solid rgba(0, 212, 255, 0.35);
        font-size: 20px !important;
    }}
    
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }}
    
    .mockup-card {{
        background: rgba(8, 20, 48, 0.78);
        border: 2px solid rgba(0, 212, 255, 0.4);
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(0, 212, 255, 0.18);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        margin-bottom: 20px;
    }}
    
    .card-title {{
        color: #FFFFFF;
        font-size: 24px !important;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
        border-bottom: 2px solid rgba(0, 212, 255, 0.2);
        padding-bottom: 10px;
    }}
    
    .card-title span.icon {{
        color: #00D4FF;
        font-size: 26px !important;
    }}
    
    .team-pill-a {{
        background: linear-gradient(90deg, #00D4FF, #0284C7);
        color: #050B1A;
        font-weight: 900;
        font-size: 20px !important;
        padding: 10px 18px;
        border-radius: 25px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
    }}
    
    .team-pill-b {{
        background: linear-gradient(90deg, #1D4ED8, #3B82F6);
        color: #FFFFFF;
        font-weight: 900;
        font-size: 20px !important;
        padding: 10px 18px;
        border-radius: 25px;
        text-align: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
    }}
    
    .battle-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 8px 0 4px 0;
        font-size: 18px !important;
    }}
    .battle-val-a {{
        color: #00D4FF;
        font-weight: 800;
        font-size: 20px !important;
        width: 55px;
        text-align: left;
    }}
    .battle-label {{
        color: #CBD5E1;
        font-weight: 600;
        font-size: 17px !important;
        flex: 1;
        text-align: center;
    }}
    .battle-val-b {{
        color: #60A5FA;
        font-weight: 800;
        font-size: 20px !important;
        width: 55px;
        text-align: right;
    }}
    .battle-bar-wrap {{
        display: flex;
        height: 8px;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.12);
        overflow: hidden;
        margin-bottom: 10px;
    }}
    .battle-bar-a {{
        background: #00D4FF;
        box-shadow: 0 0 10px #00D4FF;
        height: 100%;
    }}
    .battle-bar-b {{
        background: #3B82F6;
        box-shadow: 0 0 10px #3B82F6;
        height: 100%;
        margin-left: auto;
    }}
    
    .kpi-box {{
        background: rgba(6, 16, 40, 0.85);
        border: 2px solid rgba(0, 212, 255, 0.35);
        border-radius: 18px;
        padding: 16px 10px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
        height: 100%;
    }}
    .kpi-tag {{
        font-size: 13px !important;
        color: #00D4FF;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    .kpi-main {{
        font-size: 28px !important;
        font-weight: 900;
        color: #FFFFFF;
        margin: 6px 0;
    }}
    .kpi-sub {{
        font-size: 15px !important;
        color: #CBD5E1;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    
    .rank-row {{
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-radius: 12px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(0, 212, 255, 0.12);
    }}
    .rank-row:hover {{
        background: rgba(0, 212, 255, 0.15);
        border-color: rgba(0, 212, 255, 0.4);
    }}
    .rank-num {{
        width: 30px;
        color: #00D4FF;
        font-weight: 800;
        font-size: 18px !important;
    }}
    .rank-name {{
        flex: 1;
        font-weight: 700;
        font-size: 18px !important;
        color: #FFFFFF;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding-left: 8px;
    }}
    .rank-stat {{
        width: 55px;
        text-align: right;
        font-size: 17px !important;
        color: #CBD5E1;
        font-weight: 600;
    }}
    .rank-pts {{
        width: 70px;
        text-align: right;
        font-size: 19px !important;
        color: #00D4FF;
        font-weight: 900;
    }}

    .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {{
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #00D4FF !important;
    }}
    input, select, .stSelectbox div {{
        font-size: 18px !important;
    }}
    button {{
        font-size: 19px !important;
        font-weight: 800 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Wenn nicht angemeldet: Seitenleiste und Navigation sofort per CSS unsichtbar machen
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)

def init_session_auth():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    if 'user_name' not in st.session_state:
        st.session_state['user_name'] = None
    if 'player_id' not in st.session_state:
        st.session_state['player_id'] = None
    if 'must_change_pw' not in st.session_state:
        st.session_state['must_change_pw'] = False

def check_login(username, password):
    u = username.strip().lower()
    p = password.strip()
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, team, password, must_change_password, role FROM players")
    players_data = c.fetchall()
    conn.close()
    
    for p_id, p_name, p_team, p_pass, p_must_change, p_role in players_data:
        p_name_lower = p_name.lower()
        first_name_lower = p_name_lower.split()[0]
        
        if u == p_name_lower or u == first_name_lower:
            if p == p_pass or p == 'lions2026':
                is_first_login = bool(p_must_change) or (p == 'lions2026')
                return {
                    'role': p_role if p_role else 'player',
                    'name': p_name,
                    'player_id': p_id,
                    'must_change_pw': is_first_login
                }
        
    return None

def render_sidebar_auth():
    init_session_auth()
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        return

    with st.sidebar:
        st.image("assets/logo.png", width=180)
        st.markdown("<h3 style='text-align: center; color: #00D4FF; margin-top: -5px; font-weight: 900;'>LIONS LEAGUE</h3>", unsafe_allow_html=True)
        st.caption("<div style='text-align: center; color: #CBD5E1; font-size: 15px;'>SC Weyhausen von 1921 e.V.</div>", unsafe_allow_html=True)
        st.divider()
        
        role_badge = "👑 **Admin**" if st.session_state.get('role') == 'admin' else "🎯 **Spieler**"
        st.markdown(f"Status:\n\n{role_badge} `{st.session_state.get('user_name')}`")
        if st.button("🚪 Abmelden", key="sidebar_logout_btn", use_container_width=True):
            st.session_state['authenticated'] = False
            st.session_state['role'] = None
            st.session_state['user_name'] = None
            st.session_state['player_id'] = None
            st.session_state['must_change_pw'] = False
            st.rerun()
        st.divider()

    if st.session_state.get('role') != 'admin':
        st.markdown("""
        <style>
        [data-testid="stSidebarNav"] a[href*="Eingabe"], 
        [data-testid="stSidebarNav"] a[href*="Verwaltung"], 
        [data-testid="stSidebarNav"] a[href*="Einstellungen"],
        [data-testid="stSidebarNav"] a[href*="Export"] {
            display: none !important;
        }
        [data-testid="stToolbar"] {
            visibility: hidden !important;
        }
        [data-testid="stHeader"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

def render_impressum_footer():
    st.markdown("""
    <div style='text-align: center; margin-top: 50px; color: #94A3B8; font-size: 14px; border-top: 1px solid rgba(0,212,255,0.2); padding-top: 20px;'>
        🦁 <b>Lions Weyhausen</b> • Dartsport im Sportclub Weyhausen von 1921 e.V.<br>
        Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)<br>
        <span style="font-size: 12px; color: #64748B;">© 2026 SC Weyhausen e.V. • Impressum & Datenschutz</span>
    </div>
    """, unsafe_allow_html=True)

def require_login():
    init_session_auth()
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔒 **Zugriff geschützt:** Bitte melde dich zuerst auf der Startseite an.")
            if st.button("⬅️ Zur Anmeldung auf der Startseite", key="btn_require_login_redirect", type="primary", use_container_width=True):
                st.switch_page("app.py")
        st.stop()
    render_sidebar_auth()

def require_admin():
    init_session_auth()
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔒 **Zugriff geschützt:** Bitte melde dich zuerst auf der Startseite an.")
            if st.button("⬅️ Zur Anmeldung auf der Startseite", key="btn_require_admin_redirect", type="primary", use_container_width=True):
                st.switch_page("app.py")
        st.stop()
    if st.session_state.get('role') != 'admin':
        st.error("⛔ Zugriff verweigert. Diese Seite ist nur für den Spartenleiter (Admin) zugänglich.")
        st.stop()
    render_sidebar_auth()

def get_points_for_average(value):
    if value < 20: return 0
    elif 20 <= value < 30: return 1
    elif 30 <= value < 40: return 2
    elif 40 <= value < 45: return 3
    elif 45 <= value < 50: return 4
    elif 50 <= value < 55: return 5
    elif 55 <= value < 60: return 6
    elif value >= 60: return 7

def get_points_for_win_ratio(ratio_percent):
    if ratio_percent <= 0: return 0
    elif ratio_percent <= 20: return 1
    elif ratio_percent <= 40: return 2
    elif ratio_percent <= 60: return 3
    elif ratio_percent <= 80: return 4
    else: return 5

def get_points_for_high_scores(score_ratio):
    if score_ratio <= 0: return 0
    elif score_ratio <= 0.40: return 1
    elif score_ratio <= 0.80: return 2
    elif score_ratio <= 1.20: return 3
    elif score_ratio <= 1.60: return 4
    elif score_ratio <= 2.00: return 5
    elif score_ratio <= 2.40: return 6
    elif score_ratio <= 2.80: return 7
    elif score_ratio <= 3.60: return 9
    else: return 10

def calculate_match_performance(match, settings):
    legs_played = match['legs_won'] + match['legs_lost']
    win_ratio = 100.0 if match['legs_won'] > match['legs_lost'] else 0.0
    
    total_high_scores = match['scores_80'] + match['scores_100'] + match['scores_140'] + match['scores_180']
    score_ratio = (total_high_scores / legs_played) if legs_played > 0 else 0
    
    pts_win = get_points_for_win_ratio(win_ratio)
    pts_avg = get_points_for_average(match['avg_total'])
    pts_avg9 = get_points_for_average(match['avg_9'])
    pts_avg18 = get_points_for_average(match['avg_18'])
    pts_scores = get_points_for_high_scores(score_ratio)
    
    specials = match.get('specials_count', 0) or 0
    specials_bonus = specials * 0.5  # +0,5 Pkt pro Special (180er, High Finish 101-170, Short Game ≤18 Darts, Bull-Finish)
    
    weighted_win = pts_win * (settings['win_weight'] / 100.0)
    weighted_avg = pts_avg * (settings['avg_weight'] / 100.0)
    weighted_avg9 = pts_avg9 * (settings['avg9_weight'] / 100.0)
    weighted_avg18 = pts_avg18 * (settings['avg18_weight'] / 100.0)
    weighted_scores = pts_scores * (settings['scores_weight'] / 100.0)
    
    total_rating = weighted_win + weighted_avg + weighted_avg9 + weighted_avg18 + weighted_scores + specials_bonus
    
    return {
        'win_ratio': win_ratio,
        'score_ratio': score_ratio,
        'pts_win': pts_win,
        'pts_avg': pts_avg,
        'pts_avg9': pts_avg9,
        'pts_avg18': pts_avg18,
        'pts_scores': pts_scores,
        'specials_count': specials,
        'specials_bonus': specials_bonus,
        'total_rating': round(total_rating, 2)
    }

def get_short_name(full_name):
    p = str(full_name).split()
    return f"{p[0]} {p[1][0]}." if len(p) > 1 else str(full_name)
