"""
Mathematische Validierungs- und Plausibilitäts-Engine für den Dart Match Image Analyzer.
"""
from typing import List, Dict, Any, Tuple
from .models import VisitRecord, LegRecord, MatchRecord, ExtractedMatch

def validate_visits_math(visits: List[VisitRecord]) -> List[VisitRecord]:
    """
    Validiert die mathematische Konsistenz aller Aufnahmen (501-Subtraktion).
    Setzt den Status auf WARNING_MATH_MISMATCH bei Unstimmigkeiten.
    """
    validated_visits = []
    
    # Gruppieren nach (match_id, leg_number, player)
    groups: Dict[Tuple[str, int, str], List[VisitRecord]] = {}
    for v in visits:
        key = (v.match_id, v.leg_number, v.player)
        if key not in groups:
            groups[key] = []
        groups[key].append(v)
        
    for key, leg_visits in groups.items():
        # Chronologisch nach visit_number sortieren
        leg_visits.sort(key=lambda x: x.visit_number)
        
        running_expected_rest = 501
        for idx, v in enumerate(leg_visits):
            expected_remaining = running_expected_rest - v.score
            
            # Prüfen ob Startscore konsistent ist
            if v.start_score != running_expected_rest:
                v.validation_status = "WARNING_MATH_MISMATCH"
                v.validation_message = f"Startscore-Abweichung: Erwartet {running_expected_rest}, Erkannt {v.start_score}"
            # Prüfen ob Restscore nach Subtraktion stimmt
            elif v.remaining_score != expected_remaining:
                v.validation_status = "WARNING_MATH_MISMATCH"
                v.validation_message = f"Subtraktionsfehler: {v.start_score} - {v.score} = {expected_remaining}, Erkannt {v.remaining_score}"
            else:
                if v.confidence < 0.70:
                    v.validation_status = "NEEDS_REVIEW"
                    v.validation_message = f"Niedrige OCR-Konfidenz ({v.confidence * 100:.0f}%)"
                else:
                    v.validation_status = "VALID"
                    v.validation_message = "Mathematisch 100% verifiziert"
                    
            # Für die nächste Aufnahme weiterführen (entweder erwarteter oder erkannter Rest)
            running_expected_rest = v.remaining_score if v.remaining_score > 0 else expected_remaining
            validated_visits.append(v)
            
    return validated_visits

def validate_match_integrity(extracted: ExtractedMatch) -> ExtractedMatch:
    """
    Ganzheitliche Plausibilitätsprüfung für ein komplettes Match.
    """
    # 1. Visits mathematisch validieren
    extracted.visits = validate_visits_math(extracted.visits)
    
    warnings = []
    
    # 2. Prüfen ob Legs vorhanden sind
    if not extracted.legs:
        warnings.append("Keine Legs für dieses Match erkannt.")
        
    # 3. Leg-Gewinner vs. Match-Ergebnis abgleichen
    if extracted.match.result_str:
        try:
            parts = extracted.match.result_str.replace('-', ':').split(':')
            res_h = int(parts[0].strip())
            res_a = int(parts[1].strip())
            
            actual_h_wins = sum(1 for l in extracted.legs if l.winner_player == extracted.match.home_player)
            actual_a_wins = sum(1 for l in extracted.legs if l.winner_player == extracted.match.away_player)
            
            if len(extracted.legs) > 0 and (actual_h_wins != res_h or actual_a_wins != res_a):
                warnings.append(f"Ergebnis-Diskrepanz: Match-Ergebnis {res_h}:{res_a}, aber Legs gewonnen {actual_h_wins}:{actual_a_wins}")
        except Exception:
            pass
            
    # 4. Warnings zuweisen
    mismatch_count = sum(1 for v in extracted.visits if v.validation_status == "WARNING_MATH_MISMATCH")
    if mismatch_count > 0:
        warnings.append(f"{mismatch_count} Aufnahme(n) mit mathematischer Diskrepanz erkannt - Bitte Kontrollansicht prüfen!")
        
    extracted.warnings = warnings
    return extracted
