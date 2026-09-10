"""
Leg-Phasen, Visit-Performance-Kurve und Start-Analyse der Dart Analytics Engine.
Ebene 2 (Leg).
"""
import numpy as np
from typing import List, Dict, Any
from .config import (
    OPENING_VISITS, MID_GAME_START, MID_GAME_END, FINISH_REST_THRESHOLD,
    POOR_SCORE_THRESHOLD, GOOD_SCORE_THRESHOLD, EXCELLENT_SCORE_THRESHOLD
)

def analyze_start_performance(legs_visits: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Detaillierte Startanalyse (Visits 1-3) und Berechnung des Start Index (0-100).
    legs_visits: Liste von Legs, jedes Leg enthält eine Liste von Dicts {'score': int, 'rest_score': int, 'order': int}.
    """
    v1_scores = []
    v2_scores = []
    v3_scores = []
    all_first3_scores = []
    
    for leg in legs_visits:
        for idx, v in enumerate(leg):
            score = v['score']
            order = v.get('order', idx + 1)
            if order == 1:
                v1_scores.append(score)
                all_first3_scores.append(score)
            elif order == 2:
                v2_scores.append(score)
                all_first3_scores.append(score)
            elif order == 3:
                v3_scores.append(score)
                all_first3_scores.append(score)
                
    total_starts = len(all_first3_scores)
    if total_starts == 0:
        return {
            'avg_visit_1': 0.0,
            'avg_visit_2': 0.0,
            'avg_visit_3': 0.0,
            'first_3_avg': 0.0,
            'count_100': 0, 'pct_100': 0.0,
            'count_140': 0, 'pct_140': 0.0,
            'count_180': 0, 'pct_180': 0.0,
            'count_poor': 0, 'pct_poor': 0.0,
            'start_index': 50.0
        }
        
    c_60 = sum(1 for s in all_first3_scores if 60 <= s < 100)
    c_100 = sum(1 for s in all_first3_scores if 100 <= s < 140)
    c_140 = sum(1 for s in all_first3_scores if 140 <= s < 180)
    c_180 = sum(1 for s in all_first3_scores if s == 180)
    c_poor = sum(1 for s in all_first3_scores if s <= 35) # Echte Fehlstarts/Streuer (<=35)
    
    pct_60 = (c_60 / total_starts) * 100
    pct_100 = (c_100 / total_starts) * 100
    pct_140 = (c_140 / total_starts) * 100
    pct_180 = (c_180 / total_starts) * 100
    pct_poor = (c_poor / total_starts) * 100
    
    first3_avg = float(np.mean(all_first3_scores))
    
    # START INDEX BERECHNUNG (0 - 100) - Kalibriert auf Amateur-/Kreisklasse-Niveau:
    # 15 First-9 Avg = 0 Pkt, 50 First-9 Avg = 50 Pkt, 85+ First-9 Avg = 100 Pkt
    base_score = min(max((first3_avg - 15.0) * (100.0 / 70.0), 0.0), 100.0)
    
    # Dynamischer Bonus für Scoring-Power (60+, 100+, 140+, 180) & minimale Dämpfung für Fehlstarts (<=35)
    scoring_bonus = (pct_60 * 0.04) + (pct_100 * 0.12) + (pct_140 * 0.22) + (pct_180 * 0.35)
    poor_penalty = pct_poor * 0.12
    start_index = min(max(base_score + scoring_bonus - poor_penalty, 0.0), 100.0)
    
    return {
        'avg_visit_1': round(float(np.mean(v1_scores)), 1) if v1_scores else 0.0,
        'avg_visit_2': round(float(np.mean(v2_scores)), 1) if v2_scores else 0.0,
        'avg_visit_3': round(float(np.mean(v3_scores)), 1) if v3_scores else 0.0,
        'first_3_avg': round(first3_avg, 1),
        'count_60': c_60,
        'pct_60': round(pct_60, 1),
        'count_100': c_100,
        'pct_100': round(pct_100, 1),
        'count_140': c_140,
        'pct_140': round(pct_140, 1),
        'count_180': c_180,
        'pct_180': round(pct_180, 1),
        'count_poor': c_poor,
        'pct_poor': round(pct_poor, 1),
        'start_index': round(start_index, 1)
    }

def calculate_performance_curve(legs_visits: List[List[Dict[str, Any]]], max_visit_depth: int = 12) -> List[Dict[str, Any]]:
    """
    Berechnet die Performance-Kurve nach Visit-Nummer (Visit 1, 2, 3, 4, 5, 6...).
    Liefert für jeden Visit: Average, Median, StdDev, 100+ Rate, 140+ Rate, 180 Rate.
    """
    visit_buckets = {i: [] for i in range(1, max_visit_depth + 1)}
    
    for leg in legs_visits:
        for idx, v in enumerate(leg):
            order = v.get('order', idx + 1)
            if 1 <= order <= max_visit_depth:
                visit_buckets[order].append(v['score'])
                
    curve = []
    for order in range(1, max_visit_depth + 1):
        scores = visit_buckets[order]
        if scores:
            scores_arr = np.array(scores)
            cnt = len(scores)
            curve.append({
                'visit_order': order,
                'visit_label': f"Visit {order}",
                'sample_count': cnt,
                'average': round(float(np.mean(scores_arr)), 1),
                'median': round(float(np.median(scores_arr)), 1),
                'volatility_std': round(float(np.std(scores_arr)), 1),
                'rate_100_pct': round((sum(1 for s in scores if s >= 100) / cnt) * 100, 1),
                'rate_140_pct': round((sum(1 for s in scores if s >= 140) / cnt) * 100, 1),
                'rate_180_pct': round((sum(1 for s in scores if s == 180) / cnt) * 100, 1)
            })
    return curve

def calculate_leg_phases(legs_visits: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Unterteilt Aufnahmen in drei Leg-Phasen:
    - Opening: Visits 1 - 3
    - Mid Game: Visits 4 - 6
    - Finish: Visits sobald Restscore <= 170 erreicht wurde
    """
    opening_scores = []
    mid_scores = []
    finish_scores = []
    
    for leg in legs_visits:
        reached_finish = False
        for idx, v in enumerate(leg):
            score = v['score']
            order = v.get('order', idx + 1)
            rest_score = v.get('rest_score', 501)
            
            # Finish-Phase Trigger: Restscore nach vorheriger Aufnahme war <= 170
            # oder Restscore VOR der Aufnahme war <= 170 (d.h. rest_score + score <= 170)
            score_before = rest_score + score
            if score_before <= FINISH_REST_THRESHOLD or reached_finish:
                reached_finish = True
                finish_scores.append(score)
            elif order <= OPENING_VISITS:
                opening_scores.append(score)
            elif MID_GAME_START <= order <= MID_GAME_END:
                mid_scores.append(score)
            else:
                # Spätes Mid-Game (noch kein Finish-Bereich erreicht)
                mid_scores.append(score)
                
    def get_phase_summary(scores):
        if not scores:
            return {
                'average': 0.0,
                'volatility_std': 0.0,
                'sample_count': 0,
                'rate_100_pct': 0.0,
                'rate_140_pct': 0.0,
                'rate_180_pct': 0.0
            }
        scores_arr = np.array(scores)
        cnt = len(scores)
        return {
            'average': round(float(np.mean(scores_arr)), 1),
            'volatility_std': round(float(np.std(scores_arr)), 1),
            'sample_count': cnt,
            'rate_100_pct': round((sum(1 for s in scores if s >= 100) / cnt) * 100, 1),
            'rate_140_pct': round((sum(1 for s in scores if s >= 140) / cnt) * 100, 1),
            'rate_180_pct': round((sum(1 for s in scores if s == 180) / cnt) * 100, 1)
        }

    opening_data = get_phase_summary(opening_scores)
    mid_data = get_phase_summary(mid_scores)
    finish_data = get_phase_summary(finish_scores)
    
    # Phasen-Interpretation ableiten
    if opening_data['average'] > 0 and finish_data['average'] > 0:
        delta = finish_data['average'] - opening_data['average']
        if delta > 8.0:
            trend = "Starker Finisher (steigert sich zum Leg-Ende)"
        elif delta < -8.0:
            trend = "Starker Starter / Fader (baut nach starkem Start ab)"
        else:
            trend = "Konstanter Phasen-Verlauf"
    else:
        trend = "Zu geringe Stichprobe"

    return {
        'opening': opening_data,
        'mid_game': mid_data,
        'finish': finish_data,
        'phase_trend': trend
    }

def calculate_skill_radar_metrics(
    start_index: float,
    mid_avg: float,
    match_avg: float,
    vol_std: float,
    darts_per_leg: float,
    threshold_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Berechnet die 6 Dimensionen für das Skill-Radar (0 - 100 Punkte),
    kalibriert auf das Amateur- & Kreisklasse-/Bezirksklasse-Niveau.
    Top-Spieler (z. B. Sebastian Kirste / Martin Thomas) bilden die Referenzklasse bei ~70–75%.
    """
    # 1. Start-Stärke (Auftakt in Visits 1-3, First 9 Darts)
    score_start = min(max(float(start_index) * 1.15, 0.0), 100.0)
    
    # 2. Mid-Game (Visits 4-6: 58er Schnitt -> ~76 Pkt, 45er Schnitt -> ~55 Pkt)
    score_mid = min(max(15.0 + (float(mid_avg) - 20.0) * 1.6, 10.0), 100.0) if mid_avg > 0 else 0.0
    
    # 3. Power-Scoring (Match Average: 45er Schnitt -> ~70 Pkt, 35er Schnitt -> ~48 Pkt)
    score_power = min(max(15.0 + (float(match_avg) - 20.0) * 2.2, 10.0), 100.0) if match_avg > 0 else 0.0
    
    # 4. Wurfkonstanz (Inverses der Streuung: sigma 24 -> 78 Pkt, sigma 32 -> 63 Pkt)
    if vol_std > 0:
        score_konstanz = min(max(100.0 - ((float(vol_std) - 12.0) * 1.8), 20.0), 100.0)
    else:
        score_konstanz = 50.0
        
    # 5. Finish-Effizienz (Darts per Leg bei gewonnenen Legs: 21 Darts=100 Pkt, 32 Darts=72 Pkt, 40 Darts=53 Pkt)
    if darts_per_leg > 0:
        score_finish = min(max(100.0 - ((float(darts_per_leg) - 21.0) * 2.5), 15.0), 100.0)
    else:
        score_finish = 40.0
        
    # 6. Highscore-Gefahr (Raten pro 100 Visits: Kirste mit 140ern & 180ern -> ~77 Pkt, 100er -> ~38 Pkt)
    r_100 = float(threshold_dict.get('100+', {}).get('rate_per_100', 0.0) or 0.0)
    r_140 = float(threshold_dict.get('140+', {}).get('rate_per_100', 0.0) or 0.0)
    r_180 = float(threshold_dict.get('180', {}).get('rate_per_100', 0.0) or 0.0)
    score_danger = min(max(20.0 + (r_100 * 3.5) + (r_140 * 10.0) + (r_180 * 20.0), 10.0), 100.0)
    
    def get_rating_label(v: float) -> str:
        if v >= 80: return "Herausragend"
        if v >= 65: return "Stark"
        if v >= 50: return "Solide"
        if v >= 35: return "Ausbaufähig"
        return "Basis-Niveau"

    metrics = [
        {'dim': '🏹 Start-Stärke', 'key': 'start', 'value': round(score_start, 1), 'label': get_rating_label(score_start), 'desc': 'Auftaktstärke & Druck in Visits 1–3'},
        {'dim': '⚔️ Mid-Game', 'key': 'mid', 'value': round(score_mid, 1), 'label': get_rating_label(score_mid), 'desc': 'Konstanz & Scoring in Visits 4–6'},
        {'dim': '🎯 Power-Scoring', 'key': 'power', 'value': round(score_power, 1), 'label': get_rating_label(score_power), 'desc': 'Gesamt-Durchschnitt & Wurfgewalt'},
        {'dim': '🔥 Highscore-Gefahr', 'key': 'danger', 'value': round(score_danger, 1), 'label': get_rating_label(score_danger), 'desc': 'Frequenz von 100+, 140+ und 180ern'},
        {'dim': '⚡ Wurfkonstanz', 'key': 'konstanz', 'value': round(score_konstanz, 1), 'label': get_rating_label(score_konstanz), 'desc': 'Geringe Streuung & Wiederholgenauigkeit'},
        {'dim': '🏁 Finish-Effizienz', 'key': 'finish', 'value': round(score_finish, 1), 'label': get_rating_label(score_finish), 'desc': 'Effizienz auf Doppel & Darts per Leg'}
    ]
    
    overall_skill = round(float(np.mean([m['value'] for m in metrics])), 1)
    
    return {
        'dimensions': metrics,
        'overall_skill': overall_skill,
        'overall_label': get_rating_label(overall_skill)
    }

