import os

# 1. config.toml erstellen (Base Theme: Blau/Weiß/Hell)
os.makedirs('.streamlit', exist_ok=True)
with open('.streamlit/config.toml', 'w', encoding='utf-8') as f:
    f.write('''[theme]
primaryColor="#0369a1"
backgroundColor="#f0f6fc"
secondaryBackgroundColor="#ffffff"
textColor="#0f172a"
font="sans serif"
''')

# 2. utils.py um CSS Funktion erweitern (Glassmorphism Stil)
css_code = '''
import streamlit as st
def apply_custom_theme():
    st.markdown("""
    <style>
    /* Hintergrund Gradient */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #e0f2fe 0%, #f8fafc 100%);
    }
    
    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    /* KPI Kacheln Glassmorphism */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.65);
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 50, 0.04);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.8);
    }
    
    /* Eingabe Formulare Glassmorphism */
    div.stForm {
        background: rgba(255, 255, 255, 0.65);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 50, 0.04);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.8);
    }
    
    /* Überschriften Blau */
    h1, h2, h3 {
        color: #0369a1 !important;
    }
    
    /* Dataframes etwas aufhellen */
    div.stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)
'''
with open('utils.py', 'a', encoding='utf-8') as f:
    f.write(css_code)

# 3. app.py modifizieren
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('from utils import calculate_match_performance', 'from utils import calculate_match_performance, apply_custom_theme')
content = content.replace('init_db()', 'init_db()\\napply_custom_theme()')
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 4. 1_Eingabe.py modifizieren
with open('pages/1_Eingabe.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('import streamlit as st', 'import streamlit as st\\nfrom utils import apply_custom_theme')
content = content.replace('st.title("📝 Spieldaten Eingabe")', 'st.set_page_config(page_title="Eingabe", page_icon="📝", layout="wide")\\napply_custom_theme()\\nst.title("📝 Spieldaten Eingabe")')
with open('pages/1_Eingabe.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 5. 2_Einstellungen.py modifizieren
with open('pages/2_Einstellungen.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('import streamlit as st', 'import streamlit as st\\nfrom utils import apply_custom_theme')
content = content.replace('st.title("⚙️ Einstellungen & Spieler")', 'st.set_page_config(page_title="Einstellungen", page_icon="⚙️", layout="wide")\\napply_custom_theme()\\nst.title("⚙️ Einstellungen & Spieler")')
with open('pages/2_Einstellungen.py', 'w', encoding='utf-8') as f:
    f.write(content)
