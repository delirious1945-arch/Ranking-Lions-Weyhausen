"""
Export-Modul für den Dart Match Image Analyzer (CSV & JSON).
Garantiert verlustfreien UTF-8 Export.
"""
import os
import json
import csv
import pandas as pd
from typing import List, Dict, Any
from .models import ExtractedMatch

def export_matches_to_csv_files(matches: List[ExtractedMatch], output_dir: str, file_prefix: str = "") -> Dict[str, str]:
    """
    Exportiert Matches in ein relationales Set aus 4 CSV-Dateien:
    - {prefix}_matches.csv (und matches.csv)
    - {prefix}_legs.csv (und legs.csv)
    - {prefix}_visits.csv (und visits.csv)
    - {prefix}_statistics.csv (und statistics.csv)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    matches_list = []
    legs_list = []
    visits_list = []
    stats_list = []
    
    for em in matches:
        matches_list.append(em.match.to_dict())
        for l in em.legs:
            legs_list.append(l.to_dict())
        for v in em.visits:
            visits_list.append(v.to_dict())
        for s in em.statistics:
            stats_list.append(s.to_dict())
            
    files = {}
    clean_prefix = f"{file_prefix}_" if file_prefix else ""
    
    df_matches = pd.DataFrame(matches_list)
    df_legs = pd.DataFrame(legs_list)
    df_visits = pd.DataFrame(visits_list)
    df_stats = pd.DataFrame(stats_list)
    
    # 1. matches.csv
    filename_matches = f"{clean_prefix}matches.csv" if clean_prefix else "matches.csv"
    p_matches = os.path.join(output_dir, filename_matches)
    df_matches.to_csv(p_matches, sep=";", index=False, encoding="utf-8-sig")
    files['matches'] = p_matches
        
    # 2. legs.csv
    filename_legs = f"{clean_prefix}legs.csv" if clean_prefix else "legs.csv"
    p_legs = os.path.join(output_dir, filename_legs)
    df_legs.to_csv(p_legs, sep=";", index=False, encoding="utf-8-sig")
    files['legs'] = p_legs
        
    # 3. visits.csv
    filename_visits = f"{clean_prefix}visits.csv" if clean_prefix else "visits.csv"
    p_visits = os.path.join(output_dir, filename_visits)
    df_visits.to_csv(p_visits, sep=";", index=False, encoding="utf-8-sig")
    files['visits'] = p_visits
        
    # 4. statistics.csv
    filename_stats = f"{clean_prefix}statistics.csv" if clean_prefix else "statistics.csv"
    p_stats = os.path.join(output_dir, filename_stats)
    df_stats.to_csv(p_stats, sep=";", index=False, encoding="utf-8-sig")
    files['statistics'] = p_stats
        
    return files

def export_matches_to_json(matches: List[ExtractedMatch], output_file: str) -> str:
    """Exportiert alle Matches samt Erkennungsdetails und Rohdaten in eine JSON-Datei."""
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    data = [m.to_dict() for m in matches]
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return output_file
