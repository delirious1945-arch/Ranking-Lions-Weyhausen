import streamlit as st
from utils import apply_custom_theme, require_login, render_impressum_footer

st.set_page_config(page_title="Lions League - Hilfe", page_icon="assets/logo.png", layout="wide")
apply_custom_theme()
require_login()

st.title("❓ Hilfe & Erklärungen zum Ranking")
st.caption("Das Punkte- und Wertungssystem der Lions League verständlich erklärt.")

st.markdown("""
<div class="mockup-card">
<h3 style="color: #00D4FF; margin-top: 0; font-size: 26px;">🎯 Wie berechnen sich die Punkte?</h3>
<p style="font-size: 19px; color: #CBD5E1;">
Jeder Spieler sammelt Punkte durch seine Leistung in Einzel-Matches sowie Bonuspunkte für Specials. 
Die Berechnung basiert auf 5 gewichteten Kategorien plus einem Special-Bonus:
</p>
<ul style="font-size: 19px; line-height: 1.8; color: #FFFFFF;">
    <li><b>Siegquote (Gewichtung 50%):</b> Sieg im Best-of-5 Match = 5 Punkte gewichtet.</li>
    <li><b>Gesamt-Average (Gewichtung 20%):</b> Punkte nach gestaffeltem Average-Schlüssel.</li>
    <li><b>9-Dart Average (Gewichtung 7,5%):</b> Belohnt starke Starts in jedes Leg.</li>
    <li><b>18-Dart Average (Gewichtung 7,5%):</b> Belohnt Konstanz im mittleren Legverlauf.</li>
    <li><b>Hohe Scores (Gewichtung 15%):</b> Punkte für die Anzahl hoher Scores (80+, 100+, 140+, 180er) pro Leg.</li>
    <li><b>Specials (Einzel &amp; Doppel): +0,5 Pkt Bonus</b> für jeden geworfenen Special: 180er, High Finishes (101–170), Short Games (≤ 18 Darts) und Bull-Finishes.</li>
</ul>
<p style="font-size: 17px; color: #94A3B8; margin-top: 10px;">
⚠️ Die Gewichtungen können vom Admin unter <b>Einstellungen</b> jederzeit angepasst werden. Das Ranking aktualisiert sich automatisch.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mockup-card">
<h3 style="color: #00D4FF; margin-top: 0; font-size: 26px;">📊 Average-Punkte-Tabelle</h3>
<table style="width: 100%; border-collapse: collapse; font-size: 17px; color: #FFFFFF;">
<thead>
<tr style="background: rgba(0,212,255,0.2); color: #00D4FF; font-weight: 800;">
<th style="padding: 10px; text-align: left; border-bottom: 2px solid rgba(0,212,255,0.4);">Average-Bereich</th>
<th style="padding: 10px; text-align: center; border-bottom: 2px solid rgba(0,212,255,0.4);">Punkte</th>
</tr>
</thead>
<tbody>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">Unter 20</td><td style="padding: 9px; text-align: center; color: #94A3B8;">0 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">20 – 29,9</td><td style="padding: 9px; text-align: center;">1 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">30 – 39,9</td><td style="padding: 9px; text-align: center;">2 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">40 – 44,9</td><td style="padding: 9px; text-align: center;">3 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">45 – 49,9</td><td style="padding: 9px; text-align: center;">4 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">50 – 54,9</td><td style="padding: 9px; text-align: center;">5 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">55 – 59,9</td><td style="padding: 9px; text-align: center;">6 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">60 und höher</td><td style="padding: 9px; text-align: center; color: #00D4FF; font-weight: 800;">7 Pkt</td></tr>
</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mockup-card">
<h3 style="color: #00D4FF; margin-top: 0; font-size: 26px;">📈 High-Score-Punkte-Tabelle (Scores pro Leg)</h3>
<table style="width: 100%; border-collapse: collapse; font-size: 17px; color: #FFFFFF;">
<thead>
<tr style="background: rgba(0,212,255,0.2); color: #00D4FF; font-weight: 800;">
<th style="padding: 10px; text-align: left; border-bottom: 2px solid rgba(0,212,255,0.4);">Scores/Leg-Verhältnis</th>
<th style="padding: 10px; text-align: center; border-bottom: 2px solid rgba(0,212,255,0.4);">Punkte</th>
</tr>
</thead>
<tbody>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">0 Scores</td><td style="padding: 9px; text-align: center; color: #94A3B8;">0 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">0,01 – 0,40</td><td style="padding: 9px; text-align: center;">1 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">0,41 – 0,80</td><td style="padding: 9px; text-align: center;">2 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">0,81 – 1,20</td><td style="padding: 9px; text-align: center;">3 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">1,21 – 1,60</td><td style="padding: 9px; text-align: center;">4 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">1,61 – 2,00</td><td style="padding: 9px; text-align: center;">5 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">2,01 – 2,40</td><td style="padding: 9px; text-align: center;">6 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">2,41 – 2,80</td><td style="padding: 9px; text-align: center;">7 Pkt</td></tr>
<tr style="background: rgba(255,255,255,0.03);"><td style="padding: 9px 10px;">2,81 – 3,60</td><td style="padding: 9px; text-align: center;">9 Pkt</td></tr>
<tr><td style="padding: 9px 10px;">Über 3,60</td><td style="padding: 9px; text-align: center; color: #00D4FF; font-weight: 800;">10 Pkt</td></tr>
</tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mockup-card">
<h3 style="color: #FFD700; margin-top: 0; font-size: 26px;">🔢 Rechenbeispiel: Martin Thomas (Spieltag 22.08.2026)</h3>
<p style="color: #CBD5E1; font-size: 17px; margin-bottom: 16px;">
An diesem Spieltag hat Martin Thomas zwei Einzel gegen <b>HSV Isedarter B</b> bestritten und am Ende ein Rating von <b style="color: #00D4FF;">4,62 Punkten</b> erzielt.
So wurde dieser Wert Schritt für Schritt berechnet:
</p>

<h4 style="color: #00D4FF; margin-top: 18px;">⚡ Grundprinzip der Gewichtung</h4>
<p style="font-size: 17px; color: #CBD5E1;">
Jede Kategorie erzielt eine Rohpunktzahl (je nach Leistung). Diese wird mit ihrer Gewichtung multipliziert, um den Beitrag am Gesamtrating zu ermitteln:
</p>
<div style="background: rgba(0,212,255,0.08); border-left: 4px solid #00D4FF; padding: 12px 18px; border-radius: 8px; font-size: 17px; color: #FFFFFF; margin-bottom: 18px;">
Gewichtete Punkte = Erreichte Rohpunkte × (Gewichtung in % / 100)
</div>

<h4 style="color: #00D4FF;">🎯 Einzel 1: Sieg 3:0 gegen HSV Isedarter B</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 16px; color: #FFFFFF; margin-bottom: 12px;">
<thead>
<tr style="background: rgba(0,212,255,0.15); color: #00D4FF; font-weight: 700; font-size: 14px;">
<th style="padding: 8px 10px; text-align: left;">Kategorie</th>
<th style="padding: 8px; text-align: center;">Rohwert</th>
<th style="padding: 8px; text-align: center;">Punkte (Tabelle)</th>
<th style="padding: 8px; text-align: center;">Gewichtung</th>
<th style="padding: 8px; text-align: center;">Rechnung</th>
<th style="padding: 8px; text-align: right;">Teilergebnis</th>
</tr>
</thead>
<tbody>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>Siegquote</b></td>
<td style="padding: 8px; text-align: center;">Sieg 3:0 = 100%</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">5</td>
<td style="padding: 8px; text-align: center;">50%</td>
<td style="padding: 8px; text-align: center;">5 × 0,50</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">2,50 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>Gesamt Avg</b></td>
<td style="padding: 8px; text-align: center;">44,2</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">3</td>
<td style="padding: 8px; text-align: center;">20%</td>
<td style="padding: 8px; text-align: center;">3 × 0,20</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,60 Pkt</td>
</tr>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>9-Dart Avg</b></td>
<td style="padding: 8px; text-align: center;">49,8</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">4</td>
<td style="padding: 8px; text-align: center;">7,5%</td>
<td style="padding: 8px; text-align: center;">4 × 0,075</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,30 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>18-Dart Avg</b></td>
<td style="padding: 8px; text-align: center;">57,1</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">6</td>
<td style="padding: 8px; text-align: center;">7,5%</td>
<td style="padding: 8px; text-align: center;">6 × 0,075</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,45 Pkt</td>
</tr>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>Hohe Scores</b></td>
<td style="padding: 8px; text-align: center;">6 Scores / 3 Legs = 2,00</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">5</td>
<td style="padding: 8px; text-align: center;">15%</td>
<td style="padding: 8px; text-align: center;">5 × 0,15</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,75 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>Specials</b></td>
<td style="padding: 8px; text-align: center;">0 Specials</td>
<td style="padding: 8px; text-align: center;">–</td>
<td style="padding: 8px; text-align: center;">+0,5 Bonus/Stk</td>
<td style="padding: 8px; text-align: center;">0 × 0,5</td>
<td style="padding: 8px; text-align: right; color: #94A3B8;">0,00 Pkt</td>
</tr>
</tbody>
</table>
<div style="background: rgba(0,212,255,0.12); border: 1px solid rgba(0,212,255,0.4); border-radius: 10px; padding: 10px 16px; font-size: 18px; font-weight: 800; margin-bottom: 20px;">
🏆 Rating Einzel 1: 2,50 + 0,60 + 0,30 + 0,45 + 0,75 + 0,00 = <span style="color: #00D4FF;">4,60 Punkte</span>
</div>

<h4 style="color: #00D4FF;">🎯 Einzel 2: Sieg 3:1 gegen HSV Isedarter B</h4>
<table style="width: 100%; border-collapse: collapse; font-size: 16px; color: #FFFFFF; margin-bottom: 12px;">
<thead>
<tr style="background: rgba(0,212,255,0.15); color: #00D4FF; font-weight: 700; font-size: 14px;">
<th style="padding: 8px 10px; text-align: left;">Kategorie</th>
<th style="padding: 8px; text-align: center;">Rohwert</th>
<th style="padding: 8px; text-align: center;">Punkte (Tabelle)</th>
<th style="padding: 8px; text-align: center;">Gewichtung</th>
<th style="padding: 8px; text-align: center;">Rechnung</th>
<th style="padding: 8px; text-align: right;">Teilergebnis</th>
</tr>
</thead>
<tbody>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>Siegquote</b></td>
<td style="padding: 8px; text-align: center;">Sieg 3:1 = 100%</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">5</td>
<td style="padding: 8px; text-align: center;">50%</td>
<td style="padding: 8px; text-align: center;">5 × 0,50</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">2,50 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>Gesamt Avg</b></td>
<td style="padding: 8px; text-align: center;">46,1</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">4</td>
<td style="padding: 8px; text-align: center;">20%</td>
<td style="padding: 8px; text-align: center;">4 × 0,20</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,80 Pkt</td>
</tr>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>9-Dart Avg</b></td>
<td style="padding: 8px; text-align: center;">52,5</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">5</td>
<td style="padding: 8px; text-align: center;">7,5%</td>
<td style="padding: 8px; text-align: center;">5 × 0,075</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,375 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>18-Dart Avg</b></td>
<td style="padding: 8px; text-align: center;">53,6</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">5</td>
<td style="padding: 8px; text-align: center;">7,5%</td>
<td style="padding: 8px; text-align: center;">5 × 0,075</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,375 Pkt</td>
</tr>
<tr style="background: rgba(255,255,255,0.04);">
<td style="padding: 8px 10px;"><b>Hohe Scores</b></td>
<td style="padding: 8px; text-align: center;">6 Scores / 4 Legs = 1,50</td>
<td style="padding: 8px; text-align: center; color: #00D4FF; font-weight: 800;">4</td>
<td style="padding: 8px; text-align: center;">15%</td>
<td style="padding: 8px; text-align: center;">4 × 0,15</td>
<td style="padding: 8px; text-align: right; color: #00D4FF; font-weight: 700;">0,60 Pkt</td>
</tr>
<tr>
<td style="padding: 8px 10px;"><b>Specials</b></td>
<td style="padding: 8px; text-align: center;">0 Specials</td>
<td style="padding: 8px; text-align: center;">–</td>
<td style="padding: 8px; text-align: center;">+0,5 Bonus/Stk</td>
<td style="padding: 8px; text-align: center;">0 × 0,5</td>
<td style="padding: 8px; text-align: right; color: #94A3B8;">0,00 Pkt</td>
</tr>
</tbody>
</table>
<div style="background: rgba(0,212,255,0.12); border: 1px solid rgba(0,212,255,0.4); border-radius: 10px; padding: 10px 16px; font-size: 18px; font-weight: 800; margin-bottom: 20px;">
🏆 Rating Einzel 2: 2,50 + 0,80 + 0,375 + 0,375 + 0,60 + 0,00 = <span style="color: #00D4FF;">4,65 Punkte</span>
</div>

<h4 style="color: #FFD700;">📊 Gesamtrating in der Rangliste</h4>
<p style="font-size: 17px; color: #CBD5E1;">
Da Martin Thomas an diesem Spieltag 2 Einzel gespielt hat, bildet die App den <b>Durchschnitt beider Match-Ratings</b>:
</p>
<div style="background: rgba(255,215,0,0.1); border: 2px solid rgba(255,215,0,0.4); border-radius: 10px; padding: 14px 18px; font-size: 20px; font-weight: 900; color: #FFD700; margin-top: 8px;">
Gesamtrating = (4,60 + 4,65) ÷ 2 = <span style="color: #00D4FF;">4,625 ≈ 4,62 Punkte</span>
</div>

<div style="margin-top: 18px; padding: 12px 16px; background: rgba(255,255,255,0.04); border-radius: 10px; font-size: 16px; color: #94A3B8;">
💡 <b>Warum diese Methode?</b>
Da alle Gewichtungen zusammen exakt 100% ergeben, bleibt das Basis-Rating automatisch im Bereich von 0 bis ca. 7 Punkten.
Der Sieg macht mit 50% genau die Hälfte des Gewichts aus. Specials bringen je +0,5 Bonuspunkte obendrauf.
</div>
</div>
""", unsafe_allow_html=True)

render_impressum_footer()
