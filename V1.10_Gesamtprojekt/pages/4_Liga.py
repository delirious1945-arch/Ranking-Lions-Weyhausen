import streamlit as st
from utils import apply_custom_theme, require_login, render_impressum_footer

st.set_page_config(page_title="Lions League - Liga", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_login()

st.title("🏆 Liga-Tabellen & Staffeln")
st.caption("Offizielle Tabellen der 2. Kreisklasse Staffel 07 (A-Team) und Staffel 11 (B-Team).")

tab_a, tab_b = st.tabs(["🦁 A-Team (Staffel 07)", "🐯 B-Team (Staffel 11)"])

with tab_a:
    st.subheader("2. Kreisklasse Staffel 07")
    st.info("🔗 Die aktuelle Live-Tabelle von **2K Darts Software** für unser A-Team:")
    st.markdown("""
    <div style='background: rgba(8, 20, 48, 0.85); border: 2px solid #00D4FF; border-radius: 16px; padding: 24px; text-align: center;'>
        <h3 style='color: #FFFFFF; font-size: 24px;'>3K - 2. Kreisklasse 07 Table</h3>
        <p style='color: #94A3B8; font-size: 18px;'>Klicke auf den Button unten, um die offizielle Verbandstabelle von 2K Darts Software zu öffnen:</p>
        <a href='https://2k-dart-software.com/frontend/events/10/event/1343/table' target='_blank' style='display: inline-block; background: linear-gradient(90deg, #00D4FF, #0284C7); color: #050B1A; font-weight: 800; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-size: 20px; box-shadow: 0 0 20px rgba(0, 212, 255, 0.5);'>
            📊 2. Kreisklasse Staffel 07 Tabelle öffnen
        </a>
    </div>
    """, unsafe_allow_html=True)

with tab_b:
    st.subheader("2. Kreisklasse Staffel 11")
    st.info("🔗 Die aktuelle Live-Tabelle von **2K Darts Software** für unser B-Team:")
    st.markdown("""
    <div style='background: rgba(8, 20, 48, 0.85); border: 2px solid #3B82F6; border-radius: 16px; padding: 24px; text-align: center;'>
        <h3 style='color: #FFFFFF; font-size: 24px;'>3K - 2. Kreisklasse 11 Table</h3>
        <p style='color: #94A3B8; font-size: 18px;'>Klicke auf den Button unten, um die offizielle Verbandstabelle von 2K Darts Software zu öffnen:</p>
        <a href='https://2k-dart-software.com/frontend/events/10/event/1347/table' target='_blank' style='display: inline-block; background: linear-gradient(90deg, #1D4ED8, #3B82F6); color: #FFFFFF; font-weight: 800; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-size: 20px; box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);'>
            📊 2. Kreisklasse Staffel 11 Tabelle öffnen
        </a>
    </div>
    """, unsafe_allow_html=True)

render_impressum_footer()
