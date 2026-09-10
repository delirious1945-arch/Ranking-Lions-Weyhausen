import streamlit as st
from utils import apply_custom_theme, require_admin, render_impressum_footer
from database import get_settings, update_settings, get_players, add_player, update_player_password, update_player_role

st.set_page_config(page_title="Lions League - Einstellungen", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_admin()

st.title("⚙️ Einstellungen & Gewichtungen")
st.caption("Punktegewichtungen konfigurieren, Spieler registrieren, Rollen & Zugangsdaten verwalten.")

tab1, tab2, tab3, tab4 = st.tabs([
    "⚖️ Kategorie-Gewichtung", 
    "👤 Spieler registrieren", 
    "🔑 Passwort-Reset (Admin)",
    "👑 Rollen & Admin-Rechte"
])

with tab1:
    st.subheader("Feinjustierung der 5 Grundkategorien (0,5% Schritte)")
    current = get_settings()
    
    with st.form("settings_form"):
        c1, c2 = st.columns(2)
        with c1:
            win_w = st.slider("Siegquote (%)", 0.0, 100.0, float(current['win_weight']), step=0.5)
            avg_w = st.slider("Gesamt Average (%)", 0.0, 100.0, float(current['avg_weight']), step=0.5)
            avg9_w = st.slider("9-Dart Average (%)", 0.0, 100.0, float(current['avg9_weight']), step=0.5)
        with c2:
            avg18_w = st.slider("18-Dart Average (%)", 0.0, 100.0, float(current['avg18_weight']), step=0.5)
            scores_w = st.slider("High Scores (%)", 0.0, 100.0, float(current['scores_weight']), step=0.5)
            
        total = win_w + avg_w + avg9_w + avg18_w + scores_w
        st.markdown(f"**Summe der Gewichtungen:** `{total:.1f}%` / `100.0%`")
        
        if abs(total - 100.0) > 0.01:
            st.warning("⚠️ Die Summe der 5 Kategorien muss exakt 100,0 % ergeben!")
            submit_disabled = True
        else:
            st.success("✅ Gewichtung ist perfekt ausbalanciert (100,0 %).")
            submit_disabled = False
            
        save_settings = st.form_submit_button("💾 Gewichtung Speichern", disabled=submit_disabled, use_container_width=True)
        
        if save_settings:
            update_settings(win_w, avg_w, avg9_w, avg18_w, scores_w)
            st.success("✅ Einstellungen erfolgreich in der Datenbank gespeichert!")

with tab2:
    st.subheader("Neuen Spieler zum Team hinzufügen")
    with st.form("add_player_form", clear_on_submit=True):
        p_name = st.text_input("Vollständiger Name des Spielers")
        p_team = st.selectbox("Mannschaftszuordnung", ["A-Team", "B-Team"])
        p_role = st.selectbox("Rolle", ["player", "admin"], format_func=lambda x: "👑 Admin" if x == "admin" else "🎯 Spieler")
        p_submit = st.form_submit_button("➕ Spieler anlegen", use_container_width=True)
        
        if p_submit:
            if not p_name.strip():
                st.error("Bitte gib einen Namen ein.")
            else:
                add_player(p_name.strip(), p_team, role=p_role)
                st.success(f"✅ Spieler **{p_name.strip()}** ({p_team}, {p_role}) mit Einmal-Passwort `lions2026` angelegt!")

with tab3:
    st.subheader("🔑 Einmal-Passwort für einen Spieler zurücksetzen")
    st.caption("Setzt das Passwort des Spielers auf das Standard-Einmal-Passwort 'lions2026' zurück.")
    
    players_df = get_players()
    if not players_df.empty:
        p_reset_name = st.selectbox("Spieler für Passwort-Reset wählen", players_df['name'].tolist())
        p_reset_row = players_df[players_df['name'] == p_reset_name].iloc[0]
        
        if st.button(f"🔄 Passwort für {p_reset_name} auf 'lions2026' zurücksetzen", type="secondary", use_container_width=True):
            update_player_password(int(p_reset_row['id']), "lions2026", must_change=True)
            st.success(f"Passwort für **{p_reset_name}** wurde auf `lions2026` zurückgesetzt! Er muss bei der nächsten Anmeldung ein neues Passwort festlegen.")

with tab4:
    st.subheader("👑 Rollen & Admin-Berechtigungen verwalten")
    st.caption("Hier kannst du Teammitgliedern Admin-Rechte für Match-Eingabe, DAE, Verwaltung & Einstellungen vergeben oder entziehen.")
    
    players_df = get_players()
    if not players_df.empty:
        col_r1, col_r2 = st.columns([1.5, 1.5])
        with col_r1:
            st.markdown("##### Aktuelle Admin-Übersicht")
            admins = players_df[players_df['role'] == 'admin']
            if not admins.empty:
                for _, adm in admins.iterrows():
                    st.markdown(f"👑 **{adm['name']}** ({adm['team']}) — `Admin`")
            else:
                st.info("Aktuell sind keine Spieler als Admin eingetragen.")
                
        with col_r2:
            st.markdown("##### Rolle ändern")
            selected_p_name = st.selectbox("Spieler auswählen", players_df['name'].tolist(), key="role_sel_player")
            sel_row = players_df[players_df['name'] == selected_p_name].iloc[0]
            curr_role = sel_row.get('role', 'player') or 'player'
            
            new_role = st.radio(
                f"Rolle für {selected_p_name}:",
                ["player", "admin"],
                index=1 if curr_role == "admin" else 0,
                format_func=lambda x: "👑 Admin (Vollzugriff)" if x == "admin" else "🎯 Spieler (Nur Lesezugriff)",
                key="role_radio"
            )
            
            if st.button(f"💾 Rolle für {selected_p_name} speichern", type="primary", use_container_width=True):
                update_player_role(int(sel_row['id']), new_role)
                st.success(f"✅ Rolle für **{selected_p_name}** erfolgreich auf **{new_role.upper()}** gesetzt!")
                st.rerun()

render_impressum_footer()
