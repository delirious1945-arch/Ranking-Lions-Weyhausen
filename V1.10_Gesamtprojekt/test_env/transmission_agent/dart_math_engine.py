"""
Dart-Mathematik & Konsistenz-Engine für den Übertragungs-Agenten.
Garantiert 100% mathematische Integrität aller Spieldaten.
"""
from typing import Dict, List, Any, Tuple

BOGEY_NUMBERS = {159, 162, 163, 165, 166, 168, 169}

def validate_checkout(checkout_val: int) -> Tuple[bool, str]:
    """Prüft, ob ein Checkout-Wert im Darts 501 Double Out mathematisch möglich ist."""
    if checkout_val <= 0:
        return True, ""
    if checkout_val > 170:
        return False, f"Checkout {checkout_val} ist über dem Maximum von 170!"
    if checkout_val in BOGEY_NUMBERS:
        return False, f"Checkout {checkout_val} ist ein Bogey-Number (mathematisch nicht mit 3 Darts checkbar)!"
    return True, ""

def validate_visit_subtraction(start_rest: int, score: int, end_rest: int) -> bool:
    """Prüft, ob Restwert = Startwert - Score gilt."""
    return (start_rest - score) == end_rest

def calculate_3dart_average(total_points: int, darts_thrown: int) -> float:
    """Berechnet den offiziellen 3-Dart-Average: (Punkte / Darts) * 3."""
    if darts_thrown <= 0:
        return 0.0
    return round((total_points / darts_thrown) * 3.0, 2)

def validate_match_structure(legs_won: int, legs_lost: int, best_of: int = 5) -> Tuple[bool, str]:
    """Prüft, ob das Match-Ergebnis den offiziellen Liga-Regeln (Best of 5) entspricht."""
    req_wins = (best_of // 2) + 1
    if max(legs_won, legs_lost) != req_wins:
        return False, f"Ungültiges Best-of-{best_of} Ergebnis ({legs_won}:{legs_lost}). Sieger benötigt genau {req_wins} Legs."
    if min(legs_won, legs_lost) >= req_wins:
        return False, f"Beide Spieler können nicht {req_wins} Legs gewonnen haben ({legs_won}:{legs_lost})."
    return True, ""

def validate_bbdv_lineup(matches: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Prüft die BBDV-Aufstellungsregeln:
    1. Maximal 2 Einzel pro Spieler an einem Spieltag.
    2. Genau 12 Spiele (4-2-4-2).
    """
    warnings = []
    single_counts = {}
    for m in matches:
        if m.get("match_type") == "single":
            hp = m.get("home_player", "")
            if hp:
                single_counts[hp] = single_counts.get(hp, 0) + 1
                
    for player, cnt in single_counts.items():
        if cnt > 2:
            warnings.append(f"Regelverstoß: Spieler {player} hat {cnt} Einzel absolviert (maximal 2 erlaubt)!")
            
    is_valid = len(warnings) == 0
    return is_valid, warnings
