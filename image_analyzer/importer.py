"""
CSV-Importer für Dart Match Analyzer
Liest zuvor exportierte CSV-Dateien (matches.csv, legs.csv, visits.csv, statistics.csv)
wieder ein und stellt alle Matches, Legs und Scores im State der App wieder her.
"""
import os
import csv
from typing import List, Dict, Any, Optional
from .models import MatchRecord, LegRecord, VisitRecord, StatisticsRecord, ExtractedMatch

def load_matchday_from_csv_files(csv_dir: str) -> List[Dict[str, Any]]:
    """
    Liest matches.csv, legs.csv, visits.csv und statistics.csv ein
    (unterstützt sowohl eindeutige Präfixe wie {slug}_matches.csv als auch unpräfixierte Dateien)
    und gibt eine Liste von 12 Match-Dictionaries für die App zurück.
    """
    if not os.path.exists(csv_dir):
        raise FileNotFoundError(f"Verzeichnis nicht gefunden: {csv_dir}")
        
    filenames = os.listdir(csv_dir)
    matches_files = [f for f in filenames if f.lower().endswith("matches.csv")]
    if not matches_files:
        raise FileNotFoundError(f"Erforderliche CSV-Dateien nicht gefunden in:\n{csv_dir}")
        
    match_file_name = sorted(matches_files, key=lambda x: len(x), reverse=True)[0]
    matches_file = os.path.join(csv_dir, match_file_name)
    prefix = match_file_name[:-11]  # z.B. "{slug}_"
    
    legs_cand = f"{prefix}legs.csv" if prefix else "legs.csv"
    legs_file = os.path.join(csv_dir, legs_cand) if os.path.exists(os.path.join(csv_dir, legs_cand)) else os.path.join(csv_dir, "legs.csv")
    
    visits_cand = f"{prefix}visits.csv" if prefix else "visits.csv"
    visits_file = os.path.join(csv_dir, visits_cand) if os.path.exists(os.path.join(csv_dir, visits_cand)) else os.path.join(csv_dir, "visits.csv")
    
    if not os.path.exists(visits_file):
        v_files = [f for f in filenames if f.lower().endswith("visits.csv")]
        if v_files:
            visits_file = os.path.join(csv_dir, sorted(v_files, key=lambda x: len(x), reverse=True)[0])
        else:
            raise FileNotFoundError(f"Erforderliche Visits-Datei nicht gefunden in:\n{csv_dir}")
        
    # 1. Matches einlesen
    matches_meta = {}
    with open(matches_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            m_id = row.get('match_id', '').strip()
            if m_id:
                matches_meta[m_id] = row
                
    # 2. Legs einlesen
    legs_meta = {}
    if os.path.exists(legs_file):
        with open(legs_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                m_id = row.get('match_id', '').strip()
                l_nr = int(row.get('leg_number', '1') or '1')
                legs_meta.setdefault(m_id, {})[l_nr] = row
                
    # 3. Visits einlesen und nach match_id, leg_number, player gruppieren
    visits_dict: Dict[str, Dict[int, Dict[str, List[Dict[str, Any]]]]] = {}
    with open(visits_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            m_id = row.get('match_id', '').strip()
            l_nr = int(row.get('leg_number', '1') or '1')
            p_name = row.get('player', '').strip()
            sc_val = int(row.get('score', '0') or '0')
            d_accum = int(row.get('darts_accumulated', '0') or '0')
            
            visits_dict.setdefault(m_id, {}).setdefault(l_nr, {}).setdefault(p_name, []).append({
                'score': sc_val,
                'darts_accum': d_accum
            })
            
    # 4. Erstelle die 12 Matches Datenstruktur
    loaded_matches_data = []
    for m_num in range(1, 13):
        m_id = f"M_{m_num:03d}"
        meta = matches_meta.get(m_id)
        
        if meta:
            home_p = meta.get('home_player', f"Spieler {m_num} (Heim)").strip()
            away_p = meta.get('away_player', f"Gegner {m_num} (Gast)").strip()
            board = int(meta.get('board', '1') or '1')
            start_t = meta.get('start_datetime', '').strip()
            end_t = meta.get('end_datetime', '').strip()
            dur = int(meta.get('duration_minutes', '20') or '20')
            writer = meta.get('writer', '').strip()
            mode_str = meta.get('mode', 'Best of 3 Legs')
            
            m_legs_info = legs_meta.get(m_id, {})
            m_visits_info = visits_dict.get(m_id, {})
            detected_legs = max(len(m_legs_info), len(m_visits_info), 1)
            
            legs_list = []
            for l_idx in range(1, 6):
                leg_data = {'scores_a_raw': '', 'scores_b_raw': '', 'starter': '', 'darts_a': '', 'darts_b': ''}
                if l_idx in m_visits_info:
                    p_visits_map = m_visits_info[l_idx]
                    
                    # Fuzzy / Exact Match für Spieler A
                    matching_p_a = next((p for p in p_visits_map if p.lower() == home_p.lower()), None)
                    if not matching_p_a and p_visits_map:
                        matching_p_a = list(p_visits_map.keys())[0]
                    if matching_p_a:
                        sc_a_list = [str(x['score']) for x in p_visits_map[matching_p_a]]
                        leg_data['scores_a_raw'] = "\n".join(sc_a_list)
                        last_d_a = p_visits_map[matching_p_a][-1]['darts_accum']
                        leg_data['darts_a'] = str(last_d_a) if last_d_a > 0 else ""
                    
                    # Fuzzy / Exact Match für Spieler B
                    matching_p_b = next((p for p in p_visits_map if p.lower() == away_p.lower()), None)
                    if not matching_p_b and len(p_visits_map) > 1:
                        matching_p_b = [p for p in p_visits_map if p != matching_p_a][0]
                    if matching_p_b:
                        sc_b_list = [str(x['score']) for x in p_visits_map[matching_p_b]]
                        leg_data['scores_b_raw'] = "\n".join(sc_b_list)
                        last_d_b = p_visits_map[matching_p_b][-1]['darts_accum']
                        leg_data['darts_b'] = str(last_d_b) if last_d_b > 0 else ""
                        
                if l_idx in m_legs_info:
                    starter = m_legs_info[l_idx].get('starter_player', '').strip()
                    if starter:
                        leg_data['starter'] = starter
                        
                legs_list.append(leg_data)
                
            loaded_matches_data.append({
                'match_number': m_num,
                'home_player': home_p,
                'away_player': away_p,
                'board': board,
                'start_time': start_t,
                'end_time': end_t,
                'duration_min': dur,
                'writer': writer,
                'num_legs': min(max(detected_legs, 1), 5),
                'legs': legs_list,
                'calculated_match': None
            })
        else:
            loaded_matches_data.append({
                'match_number': m_num,
                'home_player': f"Spieler {m_num} (Heim)",
                'away_player': f"Gegner {m_num} (Gast)",
                'board': (m_num % 4) + 1,
                'start_time': f"28.08.2026 {19 + (m_num // 6)}:{(m_num % 6)*10:02d}",
                'end_time': f"28.08.2026 {19 + (m_num // 6)}:{(m_num % 6)*10 + 20:02d}",
                'duration_min': 20,
                'writer': f"Schreiber {((m_num % 3) + 1)}",
                'num_legs': 3,
                'legs': [
                    {'scores_a_raw': '', 'scores_b_raw': '', 'starter': '', 'darts_a': '', 'darts_b': ''}
                    for _ in range(5)
                ],
                'calculated_match': None
            })
            
    return loaded_matches_data
