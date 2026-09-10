"""
Deterministische Basis-Kennzahlen der Dart Analytics Engine.
Ebene 1 (Spieler) und Ebene 2 (Leg).
"""
import numpy as np
from typing import List, Dict, Any
from .config import (
    POOR_SCORE_THRESHOLD, NORMAL_SCORE_MIN, NORMAL_SCORE_MAX,
    GOOD_SCORE_THRESHOLD, GOOD_SCORE_MAX, EXCELLENT_SCORE_THRESHOLD, MAX_SCORE
)

def calculate_3dart_average(total_points: int, total_darts: int) -> float:
    """
    Berechnet den Standard-3-Dart-Average im Darts:
    Average = (Gesamtpunktzahl / Anzahl geworfener Darts) * 3
    """
    if total_darts <= 0:
        return 0.0
    return round((total_points / total_darts) * 3, 2)

def calculate_visit_statistics(scores: List[int], total_darts: int = 0) -> Dict[str, Any]:
    """Berechnet grundlegende Visit-Statistiken (Average, Median, Volatilität, Min/Max)."""
    if not scores:
        return {
            'total_visits': 0,
            'total_score': 0,
            'average_visit': 0.0,
            'match_average': 0.0,
            'median_score': 0.0,
            'volatility_std': 0.0,
            'min_score': 0,
            'max_score': 0
        }
    
    scores_arr = np.array(scores, dtype=float)
    total_pts = int(np.sum(scores_arr))
    d_count = total_darts if total_darts > 0 else (len(scores) * 3)
    match_avg = calculate_3dart_average(total_pts, d_count)
    
    return {
        'total_visits': len(scores),
        'total_score': total_pts,
        'average_visit': round(float(np.mean(scores_arr)), 2),
        'match_average': match_avg,  # Exakt nach (Gesamtpunkte / Gesamtdarts) * 3
        'median_score': round(float(np.median(scores_arr)), 1),
        'volatility_std': round(float(np.std(scores_arr)), 2),
        'min_score': int(np.min(scores_arr)),
        'max_score': int(np.max(scores_arr))
    }

def calculate_first_n_averages(legs_visits: List[List[int]]) -> Dict[str, float]:
    """
    Berechnet First 9, First 12, First 15 und First 18 Averages über alle Legs.
    legs_visits: Liste von Listen, wobei jede innere Liste die Scores der Visits eines Legs in Reihenfolge enthält.
    """
    first_9_scores = []   # Erste 3 Visits
    first_12_scores = []  # Erste 4 Visits
    first_15_scores = []  # Erste 5 Visits
    first_18_scores = []  # Erste 6 Visits
    
    for leg in legs_visits:
        if len(leg) >= 1:
            first_9_scores.extend(leg[:3])
        if len(leg) >= 1:
            first_12_scores.extend(leg[:4])
        if len(leg) >= 1:
            first_15_scores.extend(leg[:5])
        if len(leg) >= 1:
            first_18_scores.extend(leg[:6])
            
    return {
        'first_9_avg': round(float(np.mean(first_9_scores)), 2) if first_9_scores else 0.0,
        'first_12_avg': round(float(np.mean(first_12_scores)), 2) if first_12_scores else 0.0,
        'first_15_avg': round(float(np.mean(first_15_scores)), 2) if first_15_scores else 0.0,
        'first_18_avg': round(float(np.mean(first_18_scores)), 2) if first_18_scores else 0.0
    }

def calculate_score_distribution(scores: List[int]) -> Dict[str, Any]:
    """
    Analysiert Scores nach Kategorien und Schwellenwerten.
    Liefert Anzahl, Anteil (%) und Rate pro 100 Visits.
    """
    total = len(scores)
    if total == 0:
        return {'buckets': {}, 'thresholds': {}, 'total_visits': 0}
    
    # 1. BUCKETS (Disjunkte Kategorien)
    buckets = {
        '0-60': 0,
        '61-99': 0,
        '100-119': 0,
        '120-139': 0,
        '140-179': 0,
        '180': 0
    }
    
    # 2. THRESHOLDS (Kumulative Schwellenwerte)
    thresholds = {
        '60+': 0,
        '80+': 0,
        '100+': 0,
        '120+': 0,
        '140+': 0,
        '180': 0
    }
    
    for s in scores:
        # Buckets
        if s <= 60: buckets['0-60'] += 1
        elif s <= 99: buckets['61-99'] += 1
        elif s <= 119: buckets['100-119'] += 1
        elif s <= 139: buckets['120-139'] += 1
        elif s <= 179: buckets['140-179'] += 1
        elif s == 180: buckets['180'] += 1
        
        # Thresholds
        if s >= 60: thresholds['60+'] += 1
        if s >= 80: thresholds['80+'] += 1
        if s >= 100: thresholds['100+'] += 1
        if s >= 120: thresholds['120+'] += 1
        if s >= 140: thresholds['140+'] += 1
        if s == 180: thresholds['180'] += 1
        
    def format_rates(raw_dict):
        result = {}
        for key, count in raw_dict.items():
            pct = round((count / total) * 100, 1)
            rate_per_100 = pct  # Mathematisch identisch zu (count / total) * 100
            result[key] = {
                'count': count,
                'pct': pct,
                'rate_per_100': rate_per_100
            }
        return result

    return {
        'total_visits': total,
        'buckets': format_rates(buckets),
        'thresholds': format_rates(thresholds)
    }

def calculate_darts_per_leg(won_legs_visits_count: List[int]) -> float:
    """Berechnet durchschnittliche Darts pro gewonnenem Leg (3 Darts pro Visit)."""
    if not won_legs_visits_count:
        return 0.0
    # Jeder Visit entspricht 3 Darts
    total_darts = [v * 3 for v in won_legs_visits_count]
    return round(float(np.mean(total_darts)), 1)
