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

@st.cache_data(show_spinner=False)
def _get_optimized_avatar_b64(photo_path, max_dim=120):
    try:
        from PIL import Image
        import io
        with Image.open(photo_path) as img:
            img = img.convert("RGBA") if photo_path.endswith(".png") else img.convert("RGB")
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            if photo_path.endswith(".png"):
                img.save(buf, format="PNG", optimize=True)
                ext = "png"
            else:
                img.save(buf, format="JPEG", quality=80, optimize=True)
                ext = "jpeg"
            return ext, base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ("png" if photo_path.endswith(".png") else "jpeg"), get_base64_image(photo_path)

def get_avatar_svg(name, border_color="#3B82F6", size=70):
    photo_path = get_player_photo_path(name)
    if photo_path and os.path.exists(photo_path):
        target_dim = max(size * 2, 60)
        ext, img_b64 = _get_optimized_avatar_b64(photo_path, max_dim=target_dim)
        return f'<img src="data:image/{ext};base64,{img_b64}" style="width:{size}px;height:{size}px;border-radius:50%;border:2px solid {border_color};box-shadow:0 0 10px {border_color}88;object-fit:cover;display:block;margin:0 auto;" />'
    
    parts = name.strip().split()
    initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "🎯"
    font_s = max(int(size * 0.36), 11)
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#0B1226,#1E293B);border:2px solid {border_color};box-shadow:0 0 10px {border_color}66;display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:800;font-size:{font_s}px;letter-spacing:1px;margin:0 auto;">{initials}</div>'

def apply_custom_theme():
    st.markdown("""
    <style>
    /* 1. SIDEBAR & DEFAULT HEADER PERMANENT AUSBLENDEN */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarNav"], 
    [data-testid="stSidebarNavItems"],
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    header [data-testid="stHeaderActionElements"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
        transform: translateX(-9999px) !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        transform: translateX(-9999px) !important;
    }
    header, [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        pointer-events: none !important;
    }

    /* 2. EDLES MATT-SCHWARZES THEME (Obsidian + Silber + Blau) */
    html, body, [data-testid="stAppViewContainer"] {
        background: #050811 !important;
        color: #FFFFFF !important;
        font-size: 17px !important;
    }
    
    p, span, div, label, input, button, select {
        font-size: 16px !important;
    }
    
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 98% !important;
    }
    
    /* 3. KARTEN & CONTAINER */
    .mockup-card {
        background: rgba(11, 16, 29, 0.88);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        margin-bottom: 16px;
    }
    
    .card-title {
        color: #FFFFFF;
        font-size: 14px !important;
        font-weight: 700;
        letter-spacing: 0.75px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
    }
    
    .card-title span.icon {
        color: #94A3B8;
        font-size: 14px !important;
    }
    
    /* TEAM PILLS: BLAU (A-Team) vs SILBER (B-Team) */
    .team-pill-a {
        background: rgba(37, 99, 235, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.35);
        font-weight: 700;
        font-size: 13px !important;
        letter-spacing: 0.5px;
        padding: 6px 14px;
        border-radius: 8px;
        text-align: center;
    }
    
    .team-pill-b {
        background: rgba(226, 232, 240, 0.08);
        color: #E2E8F0;
        border: 1px solid rgba(226, 232, 240, 0.25);
        font-weight: 700;
        font-size: 13px !important;
        letter-spacing: 0.5px;
        padding: 6px 14px;
        border-radius: 8px;
        text-align: center;
    }
    
    /* BATTLE BARS */
    .battle-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 6px 0 2px 0;
        font-size: 13px !important;
    }
    .battle-val-a {
        color: #60A5FA;
        font-weight: 700;
        font-size: 14px !important;
        width: 45px;
        text-align: left;
    }
    .battle-label {
        color: #94A3B8;
        font-weight: 500;
        font-size: 12.5px !important;
        flex: 1;
        text-align: center;
    }
    .battle-val-b {
        color: #E2E8F0;
        font-weight: 700;
        font-size: 14px !important;
        width: 45px;
        text-align: right;
    }
    .battle-bar-wrap {
        display: flex;
        height: 4px;
        border-radius: 2px;
        background: rgba(255, 255, 255, 0.08);
        overflow: hidden;
        margin-bottom: 8px;
    }
    .battle-bar-a {
        background: #3B82F6;
        height: 100%;
    }
    .battle-bar-b {
        background: #CBD5E1;
        height: 100%;
        margin-left: auto;
    }
    
    /* KPI BOXES */
    .kpi-box {
        background: rgba(11, 16, 29, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
        height: 100%;
        transition: border-color 0.2s;
    }
    .kpi-box:hover {
        border-color: rgba(59, 130, 246, 0.4);
    }
    .kpi-tag {
        font-size: 11px !important;
        color: #64748B;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }
    .kpi-main {
        font-size: 23px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin: 4px 0 2px 0;
        letter-spacing: -0.3px;
    }
    .kpi-sub {
        font-size: 12px !important;
        color: #94A3B8;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* RANGLISTEN-ZEILEN */
    .rank-row {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-radius: 12px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .rank-row:hover {
        background: rgba(37, 99, 235, 0.12);
        border-color: rgba(59, 130, 246, 0.35);
    }
    .rank-num {
        width: 30px;
        color: #3B82F6;
        font-weight: 800;
        font-size: 17px !important;
    }
    .rank-name {
        flex: 1;
        font-weight: 700;
        font-size: 16px !important;
        color: #FFFFFF;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding-left: 8px;
    }
    .rank-stat {
        width: 55px;
        text-align: right;
        font-size: 15px !important;
        color: #CBD5E1;
        font-weight: 600;
    }
    .rank-pts {
        width: 70px;
        text-align: right;
        font-size: 17px !important;
        color: #60A5FA;
        font-weight: 900;
    }

    /* TOP BROWSER-STYLE NAVIGATION: KEINE KACHELN, KEINE BOXEN! */
    [data-testid="stPageLink"] {
        padding: 0 !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
    }
    
    [data-testid="stPageLink"] a {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 6px 4px 8px 4px !important;
        color: #94A3B8 !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        letter-spacing: 0.2px !important;
        text-decoration: none !important;
        transition: color 0.15s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        height: auto !important;
        min-height: unset !important;
        width: auto !important;
        border-bottom: 2px solid transparent !important;
    }
    
    [data-testid="stPageLink"] a:hover {
        background: transparent !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid rgba(59, 130, 246, 0.45) !important;
    }
    
    [data-testid="stPageLink"] a[aria-current="page"],
    [data-testid="stPageLink"] a.active {
        background: transparent !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #3B82F6 !important;
        text-shadow: 0 0 12px rgba(59, 130, 246, 0.6) !important;
    }

    button[key="top_nav_logout_btn"] {
        height: 28px !important;
        min-height: 28px !important;
        font-size: 11.5px !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #94A3B8 !important;
        border-radius: 6px !important;
        padding: 0 8px !important;
        transition: all 0.15s ease !important;
    }
    button[key="top_nav_logout_btn"]:hover {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #FCA5A5 !important;
    }

    .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
    }
    input, select, .stSelectbox div {
        font-size: 16px !important;
    }
    button {
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def is_local_env():
    try:
        from database import is_postgres
        return not is_postgres()
    except Exception:
        return True

def init_session_auth():
    if is_local_env():
        if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
            st.session_state['authenticated'] = True
            st.session_state['user_name'] = 'Sebastian Kirste'
            st.session_state['player_id'] = 3
            st.session_state['must_change_pw'] = False
        if 'role' not in st.session_state or st.session_state['role'] is None:
            st.session_state['role'] = 'admin'
    else:
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

def get_dashboard_page():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx and ctx.main_script_path:
            basename = os.path.basename(ctx.main_script_path)
            if "Startseite" in basename:
                return "1_Startseite.py"
    except Exception:
        pass
    return "app.py"

def render_top_navbar():
    init_session_auth()
    if not st.session_state.get('authenticated', False):
        return

    # Always ensure sidebar is 100% hidden
    st.markdown("""
    <style>
    [data-testid="stSidebar"], 
    [data-testid="stSidebarNav"], 
    [data-testid="stSidebarNavItems"],
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    header [data-testid="stHeaderActionElements"],
    button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
        transform: translateX(-9999px) !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        transform: translateX(-9999px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    role = st.session_state.get('role', 'player')
    user_name = st.session_state.get('user_name', 'Spieler')
    is_admin = (role == 'admin')

    logo_b64 = get_base64_image("assets/logo.png")
    logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="width:24px;height:24px;border-radius:4px;vertical-align:middle;margin-right:8px;" />' if logo_b64 else '🦁 '

    dash_page = get_dashboard_page()

    # 1. Hauptmenü (Liga & Spielbetrieb)
    main_items = [
        (dash_page, "Dashboard"),
        ("pages/2_Teams.py", "Teams"),
        ("pages/3_Spieler.py", "Spieler"),
        ("pages/4_Liga.py", "Liga"),
        ("pages/10_Dart_Analytics_Engine.py", "Dart Analytics Engine"),
        ("pages/5_Hilfe.py", "Hilfe"),
    ]

    # 2. Adminbereich (nur Spartenleitung)
    admin_items = [
        ("pages/6_Eingabe.py", "Eingabe"),
        ("pages/7_Verwaltung.py", "Verwaltung"),
        ("pages/8_Einstellungen.py", "Optionen"),
    ]

    is_local = is_local_env()

    def _on_local_role_switch():
        choice = st.session_state.get('local_role_mode')
        if choice == "🎯 Spieler":
            st.session_state['role'] = 'player'
        else:
            st.session_state['role'] = 'admin'

    if is_admin:
        # Gewichte: Brand (1.5), 6 Main-Tabs, Trenner (0.12), 3 Admin-Tabs, User/Switcher
        if is_local:
            weights = [1.5, 0.7, 0.55, 0.55, 0.45, 1.4, 0.5, 0.12, 0.6, 0.75, 0.65, 2.0]
            cols = st.columns(weights, vertical_alignment="center", gap="small")
        else:
            weights = [1.5, 0.7, 0.55, 0.55, 0.45, 1.4, 0.5, 0.12, 0.6, 0.75, 0.65, 1.2, 0.7]
            cols = st.columns(weights, vertical_alignment="center", gap="small")

        with cols[0]:
            st.markdown(f"""
            <div style="display:flex;align-items:center;white-space:nowrap;line-height:1;">
                {logo_img}
                <span style="font-weight:800;font-size:14.5px;color:#FFFFFF;letter-spacing:0.5px;">LIONS LEAGUE</span>
            </div>
            """, unsafe_allow_html=True)

        for i, (path, label) in enumerate(main_items):
            with cols[i + 1]:
                st.page_link(path, label=label)

        with cols[7]:
            st.markdown('<span style="color:rgba(255,255,255,0.18);font-size:14px;display:block;text-align:center;">|</span>', unsafe_allow_html=True)

        for j, (path, label) in enumerate(admin_items):
            with cols[8 + j]:
                st.page_link(path, label=label)

        if is_local:
            current_mode = "👑 Admin" if is_admin else "🎯 Spieler"
            if 'local_role_mode' not in st.session_state or st.session_state['local_role_mode'] != current_mode:
                st.session_state['local_role_mode'] = current_mode

            with cols[-1]:
                st.segmented_control(
                    "Ansicht",
                    ["👑 Admin", "🎯 Spieler"],
                    key="local_role_mode",
                    on_change=_on_local_role_switch,
                    label_visibility="collapsed"
                )
        else:
            with cols[-2]:
                st.markdown(f"""
                <div style="text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px;color:#94A3B8;">
                    <span style="color:#FFFFFF;font-weight:600;">{user_name}</span> <span style="color:#3B82F6;font-size:10.5px;font-weight:700;">(Admin)</span>
                </div>
                """, unsafe_allow_html=True)

            with cols[-1]:
                if st.button("Abmelden", key="top_nav_logout_btn", use_container_width=True):
                    st.session_state['authenticated'] = False
                    st.session_state['role'] = None
                    st.session_state['user_name'] = None
                    st.session_state['player_id'] = None
                    st.session_state['must_change_pw'] = False
                    st.switch_page(dash_page)
    else:
        # Spieler-Ansicht
        if is_local:
            weights = [2.0, 0.85, 0.75, 0.75, 0.65, 1.5, 0.65, 2.0]
            cols = st.columns(weights, vertical_alignment="center", gap="small")
        else:
            weights = [2.0, 0.85, 0.75, 0.75, 0.65, 1.5, 0.65, 1.3, 0.75]
            cols = st.columns(weights, vertical_alignment="center", gap="small")

        with cols[0]:
            st.markdown(f"""
            <div style="display:flex;align-items:center;white-space:nowrap;line-height:1;">
                {logo_img}
                <span style="font-weight:800;font-size:14.5px;color:#FFFFFF;letter-spacing:0.5px;">LIONS LEAGUE</span>
            </div>
            """, unsafe_allow_html=True)

        for i, (path, label) in enumerate(main_items):
            with cols[i + 1]:
                st.page_link(path, label=label)

        if is_local:
            current_mode = "👑 Admin" if is_admin else "🎯 Spieler"
            if 'local_role_mode' not in st.session_state or st.session_state['local_role_mode'] != current_mode:
                st.session_state['local_role_mode'] = current_mode

            with cols[-1]:
                st.segmented_control(
                    "Ansicht",
                    ["👑 Admin", "🎯 Spieler"],
                    key="local_role_mode",
                    on_change=_on_local_role_switch,
                    label_visibility="collapsed"
                )
        else:
            with cols[-2]:
                st.markdown(f"""
                <div style="text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px;color:#94A3B8;">
                    <span style="color:#FFFFFF;font-weight:600;">{user_name}</span>
                </div>
                """, unsafe_allow_html=True)

            with cols[-1]:
                if st.button("Abmelden", key="top_nav_logout_btn", use_container_width=True):
                    st.session_state['authenticated'] = False
                    st.session_state['role'] = None
                    st.session_state['user_name'] = None
                    st.session_state['player_id'] = None
                    st.session_state['must_change_pw'] = False
                    st.switch_page(dash_page)


    # Feine durchgehende Trennlinie wie in einem Webbrowser
    st.markdown("""
    <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-top: 4px; margin-bottom: 18px;"></div>
    """, unsafe_allow_html=True)

def render_sidebar_auth():
    render_top_navbar()

def render_impressum_footer():
    st.markdown("""
    <div style='text-align: center; margin-top: 50px; color: #94A3B8; font-size: 13.5px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px;'>
        🦁 <b>Lions Weyhausen</b> • Dartsport im Sportclub Weyhausen von 1921 e.V. • <span style="color: #60A5FA; font-weight: 700;">Version V1.2</span><br>
        Spartenleiter: Sebastian Kirste (<code>sebastian.kirste@sc-weyhausen.de</code>)<br>
        <span style="font-size: 12px; color: #64748B;">© 2026 SC Weyhausen e.V. • Impressum & Datenschutz</span>
    </div>
    """, unsafe_allow_html=True)

def require_login():
    init_session_auth()
    dash_page = get_dashboard_page()
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="stSidebarNavItems"],
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        header [data-testid="stHeaderActionElements"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            transform: translateX(-9999px) !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            transform: translateX(-9999px) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔒 **Zugriff geschützt:** Bitte melde dich zuerst auf der Startseite an.")
            if st.button("⬅️ Zur Anmeldung auf der Startseite", key="btn_require_login_redirect", type="primary", use_container_width=True):
                st.switch_page(dash_page)
        st.stop()
    render_sidebar_auth()

def require_admin():
    init_session_auth()
    dash_page = get_dashboard_page()
    if not st.session_state.get('authenticated', False):
        st.markdown("""
        <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarNav"], 
        [data-testid="stSidebarNavItems"],
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        header [data-testid="stHeaderActionElements"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
            transform: translateX(-9999px) !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            transform: translateX(-9999px) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔒 **Zugriff geschützt:** Bitte melde dich zuerst auf der Startseite an.")
            if st.button("⬅️ Zur Anmeldung auf der Startseite", key="btn_require_admin_redirect", type="primary", use_container_width=True):
                st.switch_page(dash_page)
        st.stop()
    if st.session_state.get('role') != 'admin':
        if is_local_env():
            st.switch_page(dash_page)
        else:
            render_sidebar_auth()
            st.error("⛔ Zugriff verweigert. Diese Seite ist nur für den Spartenleiter (Admin) zugänglich.")
            if st.button("⬅️ Zur Startseite wechseln", type="primary", key="btn_require_admin_back"):
                st.switch_page(dash_page)
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
    
    base_rating = weighted_win + weighted_avg + weighted_avg9 + weighted_avg18 + weighted_scores
    total_rating = base_rating + specials_bonus
    
    return {
        'win_ratio': win_ratio,
        'score_ratio': score_ratio,
        'pts_win': pts_win,
        'pts_avg': pts_avg,
        'pts_avg9': pts_avg9,
        'pts_avg18': pts_avg18,
        'pts_scores': pts_scores,
        'base_rating': round(base_rating, 2),
        'specials_count': specials,
        'specials_bonus': specials_bonus,
        'total_rating': round(total_rating, 2)
    }

def get_short_name(full_name):
    p = str(full_name).split()
    return f"{p[0]} {p[1][0]}." if len(p) > 1 else str(full_name)
