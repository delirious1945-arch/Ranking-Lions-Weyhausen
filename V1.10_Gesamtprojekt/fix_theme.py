import os

# 1. config.toml umschreiben (Dunkles Theme mit blauen Akzenten)
with open('.streamlit/config.toml', 'w', encoding='utf-8') as f:
    f.write('''[theme]
primaryColor="#3b82f6"
backgroundColor="#0f172a"
secondaryBackgroundColor="#1e293b"
textColor="#f8fafc"
font="sans serif"
''')

# 2. utils.py modifizieren
with open('utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Schneide alte apply_custom_theme funktion ab
idx = content.find('def apply_custom_theme():')
if idx != -1:
    content = content[:idx]

new_css = '''def apply_custom_theme():
    import streamlit as st
    st.markdown("""
    <style>
    /* Dark Gradient Background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0b1120 0%, #020617 100%);
    }
    
    /* Sidebar Dark Glass */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    /* KPI Kacheln Dark Glass */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.15); /* Dezenter blauer Glow */
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.15); /* Glass-Kante */
    }
    
    /* Formulare Dark Glass */
    div.stForm {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    /* Überschriften Modern Light Blue */
    h1, h2, h3 {
        color: #bae6fd !important;
    }
    
    /* Dataframes Border */
    div.stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
'''

with open('utils.py', 'w', encoding='utf-8') as f:
    f.write(content + new_css)
