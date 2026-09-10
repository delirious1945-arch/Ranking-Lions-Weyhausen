# analytics/ai_scouting.py
"""
KI-Leistungsdiagnostik, Verhaltens-Einschaetzung und Taktik-Scouting
fuer die DAE (Dart Analytics Engine).
Berechnet datenbasiert detaillierte textliche Einschaetzungen zu:
- Schwache vs. starke Aufnahmen (Streuung & Bounce-Back / Reaktion auf Rueckschlaege)
- Gegnerdruck & Nervenstaerke (Verhalten wenn Gegner im Finish-Bereich Rest <= 170 steht)
- Match-Fokus & Ausdauer ueber die Spieldauer (Kurzzeit-Fokus im Leg & Leg-fuer-Leg Ausdauer)
- Head-to-Head Duell-Psychologie & Dynamik-Vergleich
"""
import math
import numpy as np
from typing import Dict, Any, List

def analyze_player_behavioral_metrics(ana: dict) -> dict:
    """
    Berechnet die psychologischen und verhaltensbasierten Kennzahlen aus den Leg-Visits:
    1. Bounce-Back: Wie reagiert der Spieler unmittelbar nach einer schwachen Aufnahme (<= 45)?
    2. Gegnerdruck: Wie scoret der Spieler, wenn der Gegner bei Rest <= 170 (Finishbereich) steht vs. im offenen Spiel?
    3. Fokus & Spannungsabfall im Leg: Scoring Visits 1-3 vs. 4-6 vs. 7+ (nur Visits mit Rest > 80).
    """
    legs = ana.get('legs_visits', [])
    all_scores = ana.get('all_scores', [])
    
    if not all_scores or not legs:
        return {
            'bounce_back_avg': 0.0,
            'bounce_back_delta': 0.0,
            'poor_count': 0,
            'poor_pct': 0.0,
            'pressure_avg': 0.0,
            'normal_avg': 0.0,
            'pressure_delta': 0.0,
            'pressure_sample': 0,
            'focus_early': 0.0,
            'focus_mid': 0.0,
            'focus_late': 0.0,
            'focus_drop': 0.0,
            'overall_mean': 0.0
        }

    total_visits = len(all_scores)
    
    # 1. Schwache Aufnahmen & Bounce-Back
    poor_count = 0
    follow_ups = []
    for leg in legs:
        for i in range(len(leg) - 1):
            if leg[i]['score'] <= 45 and leg[i]['rest_score'] > 80:
                poor_count += 1
                if leg[i+1]['rest_score'] > 50:
                    follow_ups.append(leg[i+1]['score'])
                    
    poor_pct = round((poor_count / total_visits) * 100, 1) if total_visits > 0 else 0.0
    overall_mean = float(np.mean(all_scores)) if all_scores else 0.0
    bounce_back_avg = round(float(np.mean(follow_ups)), 1) if follow_ups else overall_mean
    bounce_back_delta = round(bounce_back_avg - overall_mean, 1)

    # 2. Gegnerdruck (Gegner Rest <= 170 & Spieler Rest > 90) vs Normal (Gegner Rest > 200)
    pressure_scores = [
        v['score'] for leg in legs for v in leg 
        if v.get('opponent_rest', 501) <= 170 and v['rest_score'] > 90
    ]
    normal_scores = [
        v['score'] for leg in legs for v in leg 
        if v.get('opponent_rest', 501) > 200 and v['rest_score'] > 90
    ]
    
    pressure_avg = round(float(np.mean(pressure_scores)), 1) if pressure_scores else overall_mean
    normal_avg = round(float(np.mean(normal_scores)), 1) if normal_scores else overall_mean
    pressure_delta = round(pressure_avg - normal_avg, 1) if normal_scores and pressure_scores else 0.0

    # 3. Fokus-Verlauf im Leg (Aufnahmen 1-3 vs 4-6 vs 7+, ohne Doppelwuerfe)
    sc_early = [v['score'] for leg in legs for v in leg if v['order'] <= 3 and v['rest_score'] > 80]
    sc_mid = [v['score'] for leg in legs for v in leg if 4 <= v['order'] <= 6 and v['rest_score'] > 80]
    sc_late = [v['score'] for leg in legs for v in leg if v['order'] >= 7 and v['rest_score'] > 80]
    
    focus_early = round(float(np.mean(sc_early)), 1) if sc_early else overall_mean
    focus_mid = round(float(np.mean(sc_mid)), 1) if sc_mid else overall_mean
    focus_late = round(float(np.mean(sc_late)), 1) if sc_late else focus_mid
    focus_drop = round(focus_late - focus_early, 1)

    return {
        'bounce_back_avg': bounce_back_avg,
        'bounce_back_delta': bounce_back_delta,
        'poor_count': poor_count,
        'poor_pct': poor_pct,
        'pressure_avg': pressure_avg,
        'normal_avg': normal_avg,
        'pressure_delta': pressure_delta,
        'pressure_sample': len(pressure_scores),
        'focus_early': focus_early,
        'focus_mid': focus_mid,
        'focus_late': focus_late,
        'focus_drop': focus_drop,
        'overall_mean': overall_mean
    }

def generate_ai_player_profile(ana: dict, player_name: str) -> dict:
    """
    Erzeugt einen vollstaendigen KI-Scouting-Report inklusive ausfuehrlicher
    textlicher Einschaetzung zu Druck, Fokus und Wurfverhalten.
    """
    radar = ana.get('radar_metrics', {})
    dims = {d['key']: d['value'] for d in radar.get('dimensions', [])}
    
    p_power = dims.get('power', 50.0)
    p_start = dims.get('start', 50.0)
    p_mid = dims.get('mid', 50.0)
    p_finish = dims.get('finish', 50.0)
    p_danger = dims.get('danger', 50.0)
    p_consistency = dims.get('konstanz', 50.0)
    total_score = radar.get('overall_skill', 50.0)
    
    first_n = ana.get('first_n', {})
    first9 = first_n.get('first_9_avg', 0.0)
    first18 = first_n.get('first_18_avg', 0.0)
    
    v_stats = ana.get('visit_stats', {})
    overall_avg = v_stats.get('match_average', 0.0)
    std_dev = ana.get('vol_std', 30.0)
    darts_per_leg = ana.get('darts_per_leg', 0.0)

    bm = analyze_player_behavioral_metrics(ana)

    # 1. Archetypen-Bestimmung
    archetype = "Der anpassungsfaehige Allrounder"
    archetype_icon = "🎯"
    archetype_desc = "Solide Balance ueber alle Spielphasen mit verlaesslichen Grundwerten."

    if total_score >= 68 and p_finish >= 65 and p_mid >= 68:
        archetype = "Dominanter Matchwinner & Allrounder"
        archetype_icon = "👑"
        archetype_desc = "Kontrolliert das Board souveraen von der ersten Aufnahme bis zum Doppel. Bestimmt das Spieltempo und bestraft Schwaechen gnadenlos."
    elif p_finish >= 68 and p_finish > p_power + 6:
        archetype = "Eiskalter Checkout-Spezialist"
        archetype_icon = "❄️"
        archetype_desc = "Geduldig im Aufbau, aber toedlich auf den Doppeln. Gewinnt Legs oft ueber Konter und ueberragende Nervenstaerke im Finish-Bereich."
    elif p_power >= 65 and p_power > p_finish + 6:
        archetype = "Highscore-Gewehr & Scoring-Brecher"
        archetype_icon = "⚡"
        archetype_desc = "Enorme Wucht im Scoring und hohe Trefferdichte im Triple-Segment. Setzt Gegner frueh unter Druck, kaempft aber gelegentlich auf Doppel."
    elif p_start >= 65 and p_start > p_mid + 6:
        archetype = "Blitz-Starter & Sprint-Gefahr"
        archetype_icon = "🚀"
        archetype_desc = "Explodiert in den ersten 9 Darts. Zwingt den Gegner sofort in die Defensive, muss jedoch die Intensitaet im Mid-Game stabilisieren."
    elif p_consistency >= 68 and std_dev < 24:
        archetype = "Das Praezisions-Uhrwerk"
        archetype_icon = "⚙️"
        archetype_desc = "Extrem niedrige Streuung, kaum Fehlwuerfe. Spielt fast wie ein Metronom und laesst sich durch gegnerische Highscores nicht aus der Ruhe bringen."
    elif p_mid >= 65:
        archetype = "Mid-Game Stratege & Rhythmus-Stabilisator"
        archetype_icon = "🏹"
        archetype_desc = "Findet nach verhaltenem Start rasch den Flow und zieht zwischen Dart 10 und 18 das Tempo massiv an."

    # 2. Staerken & Handlungsfelder
    dim_scores = [
        ("Power-Scoring (Grund-Scoring & 60+)", p_power, f"{p_power:.0f}/100"),
        (f"Start-Staerke (First-9: {first9:.1f})", p_start, f"{p_start:.0f}/100"),
        (f"Mid-Game Konstanz (Aufnahmen 4-6: {first18:.1f})", p_mid, f"{p_mid:.0f}/100"),
        (f"Finish-Effizienz (Darts/Leg: {darts_per_leg:.1f})", p_finish, f"{p_finish:.0f}/100"),
        ("Highscore-Gefahr (140+/180er)", p_danger, f"{p_danger:.0f}/100"),
        (f"Wurfkonstanz (Streuung: +- {std_dev:.1f})", p_consistency, f"{p_consistency:.0f}/100"),
    ]
    sorted_dims = sorted(dim_scores, key=lambda x: x[1], reverse=True)
    top_strengths = sorted_dims[:2]
    bottom_weaknesses = sorted_dims[-2:]

    # 3. TEXTLICHE EINSCHAETZUNG: 3 Kernkarten mit Badges
    # A) Bounce-Back & Frustration
    if bm['bounce_back_delta'] >= 4.0:
        badge_bounce = "Exzellenter Rebound"
        badge_bounce_color = "#34D399"
        text_bounce = (
            f"Starker Rebound-Effekt: Nach Fehlaufnahmen unter 45 Punkten schlaegt {player_name} mit durchschnittlich "
            f"<b>{bm['bounce_back_avg']:.1f} Punkten</b> zurueck (+{bm['bounce_back_delta']:.1f} gegenueber Schnitt). "
            f"Fehlwuerfe werden sofort abgehakt und loesen keine Negativserie aus."
        )
    elif bm['bounce_back_delta'] <= -4.0:
        badge_bounce = "Leichte Negativserie"
        badge_bounce_color = "#F87171"
        text_bounce = (
            f"Leichte Anfaelligkeit fuer Serienfehler: Nach Wuerfen <= 45 faellt der Folgescore auf Ø <b>{bm['bounce_back_avg']:.1f}</b> "
            f"({bm['bounce_back_delta']:.1f} unter Schnitt). Frustmomente sollten noch schneller aus dem Wurfablauf ausgeblendet werden."
        )
    else:
        badge_bounce = "Solider Grundrhythmus"
        badge_bounce_color = "#38BDF8"
        text_bounce = (
            f"Verlaessliche Routine: Nach Fehlaufnahmen pendelt sich der Folgescore sofort wieder beim soliden Liganiveau "
            f"von Ø <b>{bm['bounce_back_avg']:.1f} Punkten</b> ein. Keine auffaelligen Schwankungen nach Fehlern."
        )

    # B) Nervenstaerke & Gegnerdruck
    if bm['pressure_sample'] < 2:
        badge_pressure = "Wenig Druckphasen"
        badge_pressure_color = "#94A3B8"
        text_pressure = "Bislang wenige direkte Finish-Druckphasen des Gegners erfasst. Im normalen Spielverlauf wird der Rhythmus souveraen diktiert."
    elif bm['pressure_delta'] >= 4.0:
        badge_pressure = "Wettkampf-Fighter"
        badge_pressure_color = "#34D399"
        text_pressure = (
            f"Echter Kaempfertyp: Sobald der Kontrahent in den Checkout-Bereich (Rest <= 170) vorrueckt, steigert {player_name} "
            f"sein Scoring um <b>+{bm['pressure_delta']:.1f} Punkte</b> (Ø {bm['pressure_avg']:.1f} unter Druck). Drohende Leg-Verluste triggern maximale Fokussierung."
        )
    elif bm['pressure_delta'] <= -5.0:
        badge_pressure = "Druckempfindlich"
        badge_pressure_color = "#FBBF24"
        text_pressure = (
            f"Spuerbarer Druckabfall: Steht der Gegner auf Doppel, sinkt der Schnitt von Ø {bm['normal_avg']:.1f} auf <b>{bm['pressure_avg']:.1f}</b>. "
            f"Das Bewusstsein um den gegnerischen Leg-Gewinn fuehrt zu etwas vorsichtigeren Wuerfen."
        )
    else:
        badge_pressure = "Druckresistent"
        badge_pressure_color = "#38BDF8"
        text_pressure = (
            f"Hohe Nervenstaerke: Der Score unter gegnerischer Checkout-Gefahr (Ø <b>{bm['pressure_avg']:.1f}</b>) bleibt nahezu identisch "
            f"zum regulaeren Wurf (Ø {bm['normal_avg']:.1f}). Der Spieler laesst sich durch gegnerische Chancen nicht irritieren."
        )

    # C) Fokus & Spieldauer
    if bm['focus_drop'] <= -10.0:
        badge_focus = "Fruehes Finish bevorzugt"
        badge_focus_color = "#FBBF24"
        text_focus = (
            f"Hohe Startintensitaet (Visits 1-3: Ø <b>{bm['focus_early']:.1f}</b>), baut jedoch in verlaengerten Legs (ab Visit 7) "
            f"im reinen Vor-Finish-Scoring etwas ab (Ø <b>{bm['focus_late']:.1f}</b>). Kurze, rasche Legs spielen ihm voll in die Karten."
        )
    elif bm['focus_drop'] >= 4.0:
        badge_focus = "Zaeher Dauerlaeufer"
        badge_focus_color = "#34D399"
        text_focus = (
            f"Hervorragende Steherqualitaeten: Startet solide (Ø <b>{bm['focus_early']:.1f}</b>) und legt bei Legs, die laenger dauern, "
            f"ab Aufnahme 7 sogar noch an Praezision zu (Ø <b>{bm['focus_late']:.1f}</b>)."
        )
    else:
        badge_focus = "Konstanter Rhythmus"
        badge_focus_color = "#38BDF8"
        text_focus = (
            f"Vorbildliche Rhythmus-Konstanz: Haelt den Scoring-Druck von der ersten Aufnahme (Ø <b>{bm['focus_early']:.1f}</b>) "
            f"bis ins tiefere Leg (Ø <b>{bm['focus_late']:.1f}</b>) konstant hoch. Kaum Ermuedungserscheinungen."
        )

    # 4. Trainingsempfehlung
    weakest = sorted_dims[-1]
    w_name = weakest[0]
    if "Finish" in w_name or p_finish < 52:
        train_title = "🎯 Doppel-Praezision & Bob's 27"
        train_text = "Taeglich 20 Minuten Checkout-Drills: 'Around the Clock Double' und 'Bob's 27'. Fokus auf D16, D20 und D8 unter Wettkampfdruck."
    elif "Power-Scoring" in w_name or p_power < 52:
        train_title = "⚡ Triple-20 Korridor-Training"
        train_text = "100 Darts ausschliesslich auf T20 werfen. Ziel: Mindestens 45% aller Pfeile im 20er-Bett halten, Gruppierung vor Tempo."
    elif "Start-Staerke" in w_name or p_start < 52:
        train_title = "🚀 First-9 Sprint-Sets"
        train_text = "Kurze 9-Dart-Simulationen gegen virtuellen Bot (Avg 55). Jeder Wurfbeginn muss mit mentalem Fokus wie im echten Ligaspiel gestartet werden."
    elif "Wurfkonstanz" in w_name or p_consistency < 52:
        train_title = "⚙️ Rhythmus- & Streuungs-Reduktion"
        train_text = "Fokus auf identische Wurfbewegung und konstantes Release-Timing. Bouncer und Ausreisser in 1er/5er-Segmente durch ruhigen Stand minimieren."
    elif "Highscore" in w_name or p_danger < 52:
        train_title = "🔥 Maximal-Aufnahmen & 180er Setup"
        train_text = "Gezieltes Einpeilen auf den Triple-Draht. Nach dem ersten Triple nicht nachlassen, sondern direkt nachlegen."
    else:
        train_title = "🏹 Wettkampf-Simulation 501 D.O."
        train_text = "Best of 7 Legs gegen wechselnde Ziel-Averages mit gezieltem Drucktraining bei Rest 60-100."

    # 5. Taktischer Gegner-Scouting-Tipp
    strongest = sorted_dims[0]
    if "Finish" in strongest[0]:
        scout_tip = f"Vorsicht im Finish-Bereich: {player_name} nutzt Checkouts sehr konsequent. Gegner muessen Legs fruehzeitig im Scoring dominieren, um gar nicht erst in ein direktes Doppel-Duell zu geraten."
    elif "Power" in strongest[0] or "Highscore" in strongest[0]:
        scout_tip = f"{player_name} baut massiven Scoring-Druck auf. Gegner duerfen sich von Highscores nicht entmutigen lassen, sondern muessen ueber saubere Setup-Shots den eigenen Flow schuetzen."
    elif "Start" in strongest[0]:
        scout_tip = f"{player_name} startet extrem schnell. Wenn man die ersten beiden Aufnahmen pariert, bricht die Kadenz im Mid-Game oft etwas ein – hier liegt die Chance zum Gegenstoss."
    else:
        scout_tip = f"{player_name} agiert sehr ausgeglichen. Geduldige Match-Strategie und konsequente Bestrafung kleiner Setup-Fehler sind der Schluessel."

    return {
        'archetype': archetype,
        'archetype_icon': archetype_icon,
        'archetype_desc': archetype_desc,
        'strengths': top_strengths,
        'weaknesses': bottom_weaknesses,
        'training_title': train_title,
        'training_text': train_text,
        'scout_tip': scout_tip,
        'total_score': total_score,
        'behavior_metrics': bm,
        'badge_bounce': badge_bounce,
        'badge_bounce_color': badge_bounce_color,
        'text_bounce': text_bounce,
        'badge_pressure': badge_pressure,
        'badge_pressure_color': badge_pressure_color,
        'text_pressure': text_pressure,
        'badge_focus': badge_focus,
        'badge_focus_color': badge_focus_color,
        'text_focus': text_focus
    }

def generate_ai_h2h_scouting(ana_a: dict, ana_b: dict, p_a_name: str, p_b_name: str) -> dict:
    """
    Erzeugt eine tiefgehende KI-Duell-Prognose fuer den direkten Head-to-Head Vergleich zweier Spieler,
    strukturiert nach klaren Duell-Karten.
    """
    score_a = ana_a.get('radar_metrics', {}).get('overall_skill', 50.0)
    score_b = ana_b.get('radar_metrics', {}).get('overall_skill', 50.0)
    diff = score_a - score_b

    prob_a = 1 / (1 + math.exp(-0.10 * diff))
    win_prob_a = round(prob_a * 100, 1)
    win_prob_b = round(100 - win_prob_a, 1)

    dims_a = {d['key']: d['value'] for d in ana_a.get('radar_metrics', {}).get('dimensions', [])}
    dims_b = {d['key']: d['value'] for d in ana_b.get('radar_metrics', {}).get('dimensions', [])}

    bm_a = analyze_player_behavioral_metrics(ana_a)
    bm_b = analyze_player_behavioral_metrics(ana_b)

    # Phasen
    start_diff = dims_a.get('start', 50) - dims_b.get('start', 50)
    if abs(start_diff) < 4: phase_opening = "Ausgeglichen (beide starten auf Augenhoehe)"
    elif start_diff > 0: phase_opening = f"Vorteil {p_a_name} (schnellerer Rhythmus in Visits 1-3)"
    else: phase_opening = f"Vorteil {p_b_name} (starker Break-Druck ab Wurf 1)"

    mid_diff = dims_a.get('mid', 50) - dims_b.get('mid', 50)
    if abs(mid_diff) < 4: phase_mid = "Offenes Schlagabtausch-Szenario im Setup-Bereich"
    elif mid_diff > 0: phase_mid = f"Vorteil {p_a_name} (haelt Scoring zwischen Dart 10-18 konstanter)"
    else: phase_mid = f"Vorteil {p_b_name} (bringt mehr Power im Setup-Bereich)"

    fin_diff = dims_a.get('finish', 50) - dims_b.get('finish', 50)
    if abs(fin_diff) < 4: phase_finish = "Nervenkitzel pur auf Doppel – Tagesform entscheidet"
    elif fin_diff > 0: phase_finish = f"Vorteil {p_a_name} (hoehere Effizienz und Kaltschnaeuzigkeit)"
    else: phase_finish = f"Vorteil {p_b_name} (starke Doppel-Quote bei Drucksituationen)"

    if abs(diff) < 3:
        matchup_title = "⚔️ Ausgeglichenes Duell auf Augenhoehe"
        tactical_summary = f"Beide Kontrahenten begegnen sich mit aehnlicher Gesamtstaerke ({score_a:.0f} vs. {score_b:.0f}). Winzige Nuancen im Setup-Bereich und Checkout-Praezision werden die Entscheidung bringen."
    elif diff >= 8:
        matchup_title = f"👑 Klare Favoritenrolle fuer {p_a_name}"
        tactical_summary = f"{p_a_name} geht mit statistischem Vorteil ({score_a:.0f} vs. {score_b:.0f}) ins Match. {p_b_name} muss mit maximalem Scoring in den ersten 9 Darts Nadelstiche setzen, um Legs zu stehlen."
    elif diff <= -8:
        matchup_title = f"👑 Klare Favoritenrolle fuer {p_b_name}"
        tactical_summary = f"{p_b_name} besitzt aktuell das staerkere Profil ({score_b:.0f} vs. {score_a:.0f}). Fuer {p_a_name} liegt der Schluessel im geduldigen Spiel und gnadenlosem Bestrafen gegnerischer Fehlwuerfe."
    else:
        fav = p_a_name if diff > 0 else p_b_name
        matchup_title = f"⚡ Leichtes Momentum bei {fav}"
        tactical_summary = f"Enges Verfolger-Duell mit Vorteilen fuer {fav}. Der Sieg wird massgeblich ueber die Stabilitaet im Mittelspiel entschieden."

    # Vergleichende Texte fuer A und B
    # A) Bounce-Back
    stat_bb_a = f"Folgescore Ø {bm_a['bounce_back_avg']:.1f} ({bm_a['bounce_back_delta']:+.1f})"
    stat_bb_b = f"Folgescore Ø {bm_b['bounce_back_avg']:.1f} ({bm_b['bounce_back_delta']:+.1f})"
    if bm_a['bounce_back_delta'] > bm_b['bounce_back_delta'] + 3:
        txt_bb_a = f"<b>{p_a_name}</b> schuettelt Fehlwuerfe sofort ab und kontert mit hohem Folgescore."
        txt_bb_b = f"<b>{p_b_name}</b> benoetigt nach Ausrutschern meist einen Wurf mehr zur Rhythmus-Korrektur."
    elif bm_b['bounce_back_delta'] > bm_a['bounce_back_delta'] + 3:
        txt_bb_a = f"<b>{p_a_name}</b> neigt nach schwaecheren Aufnahmen kurzzeitig zu Rhythmusproblemen."
        txt_bb_b = f"<b>{p_b_name}</b> zeigt starken Rebound und laesst sich von Fehlern nicht beirren."
    else:
        txt_bb_a = f"<b>{p_a_name}</b> verarbeitet Schwaechen unaufgeregt und fegt Ausrutscher schnell aus dem Kopf."
        txt_bb_b = f"<b>{p_b_name}</b> reagiert gleichermassen stabil und stabilisiert das Scoring souveraen."

    # B) Nervenstaerke unter Druck
    stat_pr_a = f"Druck-Score Ø {bm_a['pressure_avg']:.1f} ({bm_a['pressure_delta']:+.1f})"
    stat_pr_b = f"Druck-Score Ø {bm_b['pressure_avg']:.1f} ({bm_b['pressure_delta']:+.1f})"
    if bm_a['pressure_delta'] > bm_b['pressure_delta'] + 4:
        txt_pr_a = f"Wird gefaehrlicher, wenn der Gegner auf Doppel steht (+{bm_a['pressure_delta']:.1f} Pkt)."
        txt_pr_b = f"Agierte in bisherigen Legs unter gegnerischem Checkout-Druck etwas defensiver."
    elif bm_b['pressure_delta'] > bm_a['pressure_delta'] + 4:
        txt_pr_a = f"Kann verkrampfen, wenn der Gegner auf Doppel wartet – hier muss der eigene Fokus geschuetzt werden."
        txt_pr_b = f"Kuehler Kopf bei gegnerischen Chancen: Kontert mit stabiler Praezision (+{bm_b['pressure_delta']:.1f} Pkt)."
    else:
        txt_pr_a = f"Bleibt souveraen im eigenen Tunnel, unabhaengig vom gegnerischen Rest-Score."
        txt_pr_b = f"Behaelt seinen Wurfrhythmus auch bei gegnerischer Checkout-Gefahr konstant bei."

    # C) Fokus in langen Legs
    stat_fc_a = f"Trend hinten raus: {bm_a['focus_drop']:+.1f} Pkt"
    stat_fc_b = f"Trend hinten raus: {bm_b['focus_drop']:+.1f} Pkt"
    if bm_a['focus_drop'] > bm_b['focus_drop'] + 6:
        txt_fc_a = f"Haelt den Fokus auch bei laengeren Legs bis zur Checkout-Zone konstant hoch."
        txt_fc_b = f"Verliert bei Marathon-Legs nach Visit 6 etwas an Durchschlagskraft im Scoring."
    elif bm_b['focus_drop'] > bm_a['focus_drop'] + 6:
        txt_fc_a = f"Fokus ist auf den schnellen Sprint (Visits 1-5) optimiert; profitiert von kurzen Legs."
        txt_fc_b = f"Besitzt hohe Zaehigkeit und haelt die Wurfqualitaet auch ab Aufnahme 7 stabil."
    else:
        txt_fc_a = f"Konstante Energieuebertragung ueber das gesamte Leg ohne nennenswerten Leistungsabfall."
        txt_fc_b = f"Vergleichbare Spannungskurve mit stabiler Rhythmusfuehrung bis zum Doppel."

    # Keys to victory
    if dims_a.get('power', 50) >= dims_b.get('power', 50):
        key_a = f"Scoring-Vorteil halten und {p_b_name} keine offenen Doppel-Darts schenken."
    else:
        key_a = f"Nervenstark auf die Doppel bleiben und gegnerische Highscores trocken parieren."

    if dims_b.get('power', 50) >= dims_a.get('power', 50):
        key_b = f"Mit Highscores frueh davonziehen und den Finish-Bereich vor {p_a_name} absichern."
    else:
        key_b = f"Fehler im Mid-Game minimieren und jeden Wurf auf Doppel eiskalt nutzen."

    return {
        'matchup_title': matchup_title,
        'tactical_summary': tactical_summary,
        'phase_opening': phase_opening,
        'phase_mid': phase_mid,
        'phase_finish': phase_finish,
        'key_a': key_a,
        'key_b': key_b,
        'win_prob_a': win_prob_a,
        'win_prob_b': win_prob_b,
        'score_a': score_a,
        'score_b': score_b,
        'bm_a': bm_a,
        'bm_b': bm_b,
        'stat_bb_a': stat_bb_a,
        'stat_bb_b': stat_bb_b,
        'txt_bb_a': txt_bb_a,
        'txt_bb_b': txt_bb_b,
        'stat_pr_a': stat_pr_a,
        'stat_pr_b': stat_pr_b,
        'txt_pr_a': txt_pr_a,
        'txt_pr_b': txt_pr_b,
        'stat_fc_a': stat_fc_a,
        'stat_fc_b': stat_fc_b,
        'txt_fc_a': txt_fc_a,
        'txt_fc_b': txt_fc_b,
    }
