"""
Datenextraktor für 2K / 3K Darts Screenshots (Spielinfo, Statistiken, Scoreboards).
"""
import re
from typing import List, Dict, Any, Optional
from .models import MatchRecord, LegRecord, VisitRecord, StatisticsRecord

def clean_num(text: str) -> Optional[int]:
    """Säubert einen OCR-Text und wandelt ihn in ein Integer um."""
    nums = re.findall(r'\d+', str(text))
    return int(nums[0]) if nums else None

def clean_float(text: str) -> Optional[float]:
    """Säubert einen OCR-Text und wandelt ihn in einen Float um (z.B. 47.5 oder Ø 52.8)."""
    text_clean = str(text).replace('Ø', '').replace('O', '0').replace(',', '.').strip()
    floats = re.findall(r'\d+\.?\d*', text_clean)
    return float(floats[0]) if floats else None

def extract_spielinfo(ocr_items: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """Extrahiert Match-Kopfdaten aus dem Screen-Typ 'SPIELINFO'."""
    info = {
        'home_player': '',
        'away_player': '',
        'result_str': '',
        'board': 1,
        'writer': '',
        'mode': 'Best of 5 Legs',
        'duration_min': 0,
        'start_datetime': '',
        'end_datetime': '',
        'match_number': 0,
        'round': 1,
        'source_image': filename
    }
    
    lines = [item['text'].strip() for item in ocr_items if item['text'].strip()]
    full_text = "\n".join(lines)
    
    # 1. Spieler & Ergebnis aus Kopfzeile (#7 Sebastian Kirste 3 / Kristin Bastian 0)
    top_items = [item for item in ocr_items if item['box'][0][1] < 100]
    top_items.sort(key=lambda x: x['box'][0][1])
    
    # RegEx-Muster für Schlüssel-Werte
    for idx, line in enumerate(lines):
        line_l = line.lower()
        
        if line_l.startswith("heim:") or line_l == "heim":
            if idx + 1 < len(lines) and ":" not in lines[idx + 1]:
                info['home_player'] = lines[idx + 1]
            elif ":" in line:
                info['home_player'] = line.split(":", 1)[1].strip()
                
        elif line_l.startswith("gast:") or line_l == "gast":
            if idx + 1 < len(lines) and ":" not in lines[idx + 1]:
                info['away_player'] = lines[idx + 1]
            elif ":" in line:
                info['away_player'] = line.split(":", 1)[1].strip()
                
        elif "ergebnis:" in line_l or line_l == "ergebnis":
            res_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', full_text[full_text.lower().find("ergebnis"):])
            if res_match:
                info['result_str'] = f"{res_match.group(1)}-{res_match.group(2)}"
                
        elif "dauer:" in line_l:
            dur = clean_num(line)
            if dur: info['duration_min'] = dur
            
        elif "spielstart:" in line_l:
            m = re.search(r'\d{2}\.\d{2}\.\d{2,4}\s+\d{2}:\d{2}', line)
            if m: info['start_datetime'] = m.group(0)
            
        elif "spielende:" in line_l:
            m = re.search(r'\d{2}\.\d{2}\.\d{2,4}\s+\d{2}:\d{2}', line)
            if m: info['end_datetime'] = m.group(0)
            
        elif "board:" in line_l:
            b = clean_num(line)
            if b: info['board'] = b
            
        elif "spielnummer:" in line_l:
            sn = clean_num(line)
            if sn: info['match_number'] = sn
            
        elif "in runde:" in line_l or "runde:" in line_l:
            r = clean_num(line)
            if r: info['round'] = r

    return info

def extract_scoreboard(ocr_items: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Extrahiert Aufnahmen und Scores aus dem Screen-Typ 'SCOREBOARD'.
    Verwendet feste 2K Darts Spalten-Begrenzungen und mathematische 501-Abgleichung.
    """
    # 1. Leg-Nummer ermitteln
    fn_lower = filename.lower()
    leg_num = 1
    if "leg" in fn_lower:
        m = re.search(r'leg\s*([1-9])', fn_lower)
        if m: leg_num = int(m.group(1))
    else:
        for item in ocr_items:
            m = re.search(r'leg\s*([1-9])', item['text'], re.IGNORECASE)
            if m:
                leg_num = int(m.group(1))
                break
                
    # 2. Darts & Checkouts aus dem Header (y < 250) extrahieren
    darts_summary_a = []
    darts_summary_b = []
    for item in ocr_items:
        y = item['box'][0][1]
        t = item['text'].strip()
        if 160 <= y <= 240:
            if "(" in t and ")" in t:
                clean_d = clean_num(t)
                if clean_d: darts_summary_b.append(clean_d)
            else:
                clean_d = clean_num(t)
                if clean_d and clean_d >= 9: darts_summary_a.append(clean_d)
                
    # 3. Tabellenzellen filtern (y zwischen 330 und 780)
    table_boxes = [item for item in ocr_items if 330 <= item['box'][0][1] <= 780]
    
    # Zeilen-Gruppierung (Binning nach Y-Koordinate, Zeilenabstand ca. 40px)
    row_bins = {}
    for item in table_boxes:
        y = item['box'][0][1]
        x = (item['box'][0][0] + item['box'][1][0]) / 2.0
        text = item['text'].replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1').replace('B', '8')
        digits = ''.join(c for c in text if c.isdigit())
        if digits:
            val = int(digits)
            r_idx = int(round((y - 350) / 40.0)) + 1
            if r_idx not in row_bins:
                row_bins[r_idx] = {'darts': r_idx * 3, 'score_a': None, 'rest_a': None, 'score_b': None, 'rest_b': None, 'conf_a': 1.0, 'conf_b': 1.0}
                
            if 25 <= x < 125:
                row_bins[r_idx]['score_a'] = val
                row_bins[r_idx]['conf_a'] = item['confidence']
            elif 125 <= x < 235:
                row_bins[r_idx]['rest_a'] = val
            elif 235 <= x < 325:
                row_bins[r_idx]['darts'] = val
            elif 325 <= x < 435:
                row_bins[r_idx]['score_b'] = val
                row_bins[r_idx]['conf_b'] = item['confidence']
            elif 435 <= x < 560:
                row_bins[r_idx]['rest_b'] = val
                
    # 4. Mathematische 501-Rekonstruktion für 100% fehlerfreie Werte
    visits_a = []
    visits_b = []
    
    cur_rest_a = 501
    cur_rest_b = 501
    
    sorted_r_indices = sorted(row_bins.keys())
    
    for r_idx in sorted_r_indices:
        r = row_bins[r_idx]
        
        # Spieler A
        if r['score_a'] is not None or r['rest_a'] is not None:
            sc_a = r['score_a']
            rst_a = r['rest_a']
            
            # Mathe-Korrektur falls einer der Werte fehlt
            if sc_a is not None and rst_a is not None:
                if cur_rest_a - sc_a != rst_a:
                    # Wenn Restscore plausibler ist
                    sc_a = max(cur_rest_a - rst_a, 0)
            elif sc_a is not None and rst_a is None:
                rst_a = max(cur_rest_a - sc_a, 0)
            elif sc_a is None and rst_a is not None:
                sc_a = max(cur_rest_a - rst_a, 0)
                
            visits_a.append({
                'visit_num': len(visits_a) + 1,
                'score': sc_a,
                'start_score': cur_rest_a,
                'remaining_score': rst_a,
                'confidence': r['conf_a']
            })
            cur_rest_a = rst_a
            
        # Spieler B
        if r['score_b'] is not None or r['rest_b'] is not None:
            sc_b = r['score_b']
            rst_b = r['rest_b']
            
            if sc_b is not None and rst_b is not None:
                if cur_rest_b - sc_b != rst_b:
                    sc_b = max(cur_rest_b - rst_b, 0)
            elif sc_b is not None and rst_b is None:
                rst_b = max(cur_rest_b - sc_b, 0)
            elif sc_b is None and rst_b is not None:
                sc_b = max(cur_rest_b - rst_b, 0)
                
            visits_b.append({
                'visit_num': len(visits_b) + 1,
                'score': sc_b,
                'start_score': cur_rest_b,
                'remaining_score': rst_b,
                'confidence': r['conf_b']
            })
            cur_rest_b = rst_b

    return {
        'leg_number': leg_num,
        'visits_a': visits_a,
        'visits_b': visits_b,
        'darts_summary_a': darts_summary_a,
        'darts_summary_b': darts_summary_b,
        'source_image': filename
    }

def extract_statistiken(ocr_items: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Extrahiert Scoring-Werte (60+ bis 180), Averages und Darts/Leg aus dem Screen-Typ 'STATISTIKEN'.
    """
    lines = [item['text'].strip() for item in ocr_items if item['text'].strip()]
    
    stats_a = {'player': '', 'overall_avg': None, 'first_9_avg': None, 's60': 0, 's80': 0, 's100': 0, 's140': 0, 's180': 0}
    stats_b = {'player': '', 'overall_avg': None, 'first_9_avg': None, 's60': 0, 's80': 0, 's100': 0, 's140': 0, 's180': 0}
    
    for idx, line in enumerate(lines):
        line_l = line.lower()
        if "avg" in line_l and idx + 1 < len(lines):
            val = clean_float(lines[idx + 1])
            if val and stats_a['overall_avg'] is None:
                stats_a['overall_avg'] = val
        elif "first 9" in line_l and idx + 1 < len(lines):
            val = clean_float(lines[idx + 1])
            if val and stats_a['first_9_avg'] is None:
                stats_a['first_9_avg'] = val

    return {
        'stats_a': stats_a,
        'stats_b': stats_b,
        'source_image': filename
    }

