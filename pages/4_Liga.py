import streamlit as st
from utils import apply_custom_theme, require_login, render_impressum_footer

st.set_page_config(page_title="Lions League - Liga", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_login()

st.title("🏆 Liga-Tabellen & Staffeln")
st.caption("Offizielle Tabellen der 2. Kreisklasse Staffel 07 (A-Team) und Staffel 11 (B-Team).")

tab_a, tab_b = st.tabs(["🦁 A-Team (Staffel 07)", "🐯 B-Team (Staffel 11)"])

with tab_a:
    st.subheader("2. Kreisklasse Staffel 07 (Lions A)")
    st.info("🔗 Offizielle Tabellen, Statistiken und Bestleistungen aus dem **3K Darts Portal**:")
    st.markdown("""
    <div style='background: rgba(8, 20, 48, 0.85); border: 2px solid #00D4FF; border-radius: 16px; padding: 24px; text-align: center;'>
        <h3 style='color: #FFFFFF; font-size: 24px;'>3K Darts - 2. Kreisklasse 07</h3>
        <p style='color: #94A3B8; font-size: 16px;'>Wähle die gewünschte offizielle Ansicht im 3K-Verbandsportal:</p>
        <div style='display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 15px;'>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1343/table' target='_blank' style='background: linear-gradient(90deg, #00D4FF, #0284C7); color: #050B1A; font-weight: 800; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px; box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);'>
                📊 Tabelle öffnen
            </a>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1343/statistics/statistics' target='_blank' style='background: rgba(0, 212, 255, 0.15); border: 1px solid #00D4FF; color: #00D4FF; font-weight: 700; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px;'>
                🎯 Rangliste & Averages
            </a>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1343/performances' target='_blank' style='background: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; color: #FBBF24; font-weight: 700; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px;'>
                ⭐ Bestleistungen & Specials
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab_b:
    st.subheader("2. Kreisklasse Staffel 11 (Lions B)")
    st.info("🔗 Offizielle Tabellen, Statistiken und Bestleistungen aus dem **3K Darts Portal**:")
    st.markdown("""
    <div style='background: rgba(8, 20, 48, 0.85); border: 2px solid #3B82F6; border-radius: 16px; padding: 24px; text-align: center;'>
        <h3 style='color: #FFFFFF; font-size: 24px;'>3K Darts - 2. Kreisklasse 11</h3>
        <p style='color: #94A3B8; font-size: 16px;'>Wähle die gewünschte offizielle Ansicht im 3K-Verbandsportal:</p>
        <div style='display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 15px;'>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1347/table' target='_blank' style='background: linear-gradient(90deg, #1D4ED8, #3B82F6); color: #FFFFFF; font-weight: 800; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);'>
                📊 Tabelle öffnen
            </a>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1347/statistics/statistics' target='_blank' style='background: rgba(59, 130, 246, 0.15); border: 1px solid #3B82F6; color: #93C5FD; font-weight: 700; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px;'>
                🎯 Rangliste & Averages
            </a>
            <a href='https://portal.3k-darts.com/frontend/events/10/event/1347/performances' target='_blank' style='background: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; color: #FBBF24; font-weight: 700; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-size: 16px;'>
                ⭐ Bestleistungen & Specials
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_impressum_footer()
