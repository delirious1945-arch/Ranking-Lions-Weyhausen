"""
Layout- und Screen-Klassifikator für 2K / 3K Darts Screenshots.
Unterscheidet zuverlässig zwischen 'SPIELINFO', 'STATISTIKEN' und 'SCOREBOARD'.
"""
import re
from typing import List, Dict, Any

def detect_screen_type(ocr_items: List[Dict[str, Any]], filename: str = "") -> Dict[str, Any]:
    """
    Analysiert erkannte Texte und Dateinamen und bestimmt den Screen-Typ.
    Rückgabe: {'type': 'SPIELINFO'|'STATISTIKEN'|'SCOREBOARD'|'UNKNOWN', 'confidence': float}
    """
    fname_lower = filename.lower()
    if fname_lower:
        if "spiel" in fname_lower:
            return {'type': 'SPIELINFO', 'confidence': 1.0}
        if "statistik" in fname_lower:
            return {'type': 'STATISTIKEN', 'confidence': 1.0}
        if "leg" in fname_lower or "score" in fname_lower:
            return {'type': 'SCOREBOARD', 'confidence': 1.0}
        if "gesamt" in fname_lower:
            return {'type': 'STATISTIKEN', 'confidence': 0.95}

    # Header-Texte (obere 15% des Bildes) ignorieren, da alle 3 Tabs (Spielinfo, Statistiken, Scoreboard) dort immer stehen
    body_items = [item for item in ocr_items if item['box'][0][1] > 70]
    body_text = " ".join([item['text'].lower() for item in body_items])
    
    # 1. SCOREBOARD Erkennung: Hat 501, Leg 1/2/3/4/5 oder Punkte-Tabelle im Body
    has_501 = any(item['text'].strip() == "501" for item in body_items)
    has_leg_tab = any(re.search(r'leg\s*[1-9]', item['text'], re.IGNORECASE) for item in ocr_items)
    has_rest_scores = any(item['text'].isdigit() and int(item['text']) in [501, 401, 301, 201, 100] for item in body_items)
    
    if has_501 or (has_leg_tab and len(body_items) > 15):
        return {'type': 'SCOREBOARD', 'confidence': 0.98}
        
    # 2. STATISTIKEN Erkennung: Hat Scoring-Tabelle, Averages, Darts/Leg
    if any(k in body_text for k in ["scoring", "averages", "darts/leg", "first 9d", "checkouts/leg", "60+", "80+", "100+"]):
        return {'type': 'STATISTIKEN', 'confidence': 0.98}
        
    # 3. SPIELINFO Erkennung: Hat Spielstart, Spielende, Schreiber, Board, Modus
    if any(k in body_text for k in ["spielstart", "spielende", "schreiber", "in runde", "spielnummer", "dauer"]):
        return {'type': 'SPIELINFO', 'confidence': 0.98}
        
    # Fallback
    if len(body_items) > 20:
        return {'type': 'SCOREBOARD', 'confidence': 0.70}
        
    return {'type': 'UNKNOWN', 'confidence': 0.50}
