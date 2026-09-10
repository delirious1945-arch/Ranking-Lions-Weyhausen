"""
Datenzugriff und automatische Synchronisation zwischen Analytics Engine und Lions League.
Keine doppelte Dateneingabe!
Unterstützt 2K Darts Spieldauer, Start/Endzeit, Darts/Leg und Match-Verwaltung.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from database import execute_query, query_df, add_match, update_match, delete_match

def validate_match_legs_plausibility(legs_won: int, legs_lost: int, is_double: bool = False, best_of: int = 5) -> Dict[str, Any]:
    """
    Plausibilisierungstest für Liga-Spiele:
    Im offiziellen Best-of-5 Modus (First to 3) erfordert ein Sieg zwingend 3 gewonnene Legs
    (Ergebnisse 3:0, 3:1, 3:2 bzw. 0:3, 1:3, 2:3).
    Gibt {'is_valid': bool, 'winner_legs': int, 'warning': str} zurück.
    """
    req_legs = 3 if best_of == 5 else ((best_of // 2) + 1)
    max_legs = max(legs_won, legs_lost)
    min_legs = min(legs_won, legs_lost)
    
    if max_legs < req_legs:
        return {
            'is_valid': False,
            'winner_legs': max_legs,
            'warning': f"⚠️ Unvollständiges Spiel ({legs_won}:{legs_lost}): Regulärer Einzelsieg erfordert {req_legs} gewonnene Legs!"
        }
    if max_legs > req_legs:
        return {
            'is_valid': False,
            'winner_legs': max_legs,
            'warning': f"⚠️ Ungültiges Spielergebnis ({legs_won}:{legs_lost}): Mehr als {req_legs} Gewinnlegs im Best-of-{best_of}!"
        }
    return {
        'is_valid': True,
        'winner_legs': max_legs,
        'warning': ""
    }


def save_full_analytics_match(
    match_meta: Dict[str, Any],
    legs_data: List[Dict[str, Any]],
    auto_sync_league: bool = True
) -> int:
    """
    Speichert ein vollständiges Analytics-Match mit allen Legs und Visits.
    Wenn auto_sync_league=True: Berechnet alle 11 Ligakennzahlen vollautomatisch
    und legt ohne Doppeleingabe den entsprechenden Eintrag in der 'matches'-Tabelle an!
    """
    # 1. In analytics_matches eintragen
    execute_query('''
        INSERT INTO analytics_matches (
            player_a_id, player_b_id, player_a_name, player_b_name, match_date,
            event_name, round_name, best_of_legs, location, winner_id, season,
            duration_min, start_time, end_time, board_nr, match_nr, round_nr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        match_meta['player_a_id'], match_meta['player_b_id'],
        match_meta['player_a_name'], match_meta['player_b_name'],
        match_meta['match_date'], match_meta.get('event_name', 'Lions League'),
        match_meta.get('round_name', 'Liga-Spiel'), match_meta.get('best_of_legs', 5),
        match_meta.get('location', 'Heim'), match_meta.get('winner_id'),
        match_meta.get('season', '2026/2027'),
        int(match_meta.get('duration_min', 0) or 0),
        str(match_meta.get('start_time', '') or ''),
        str(match_meta.get('end_time', '') or ''),
        int(match_meta.get('board_nr', 1) or 1),
        int(match_meta.get('match_nr', 0) or 0),
        int(match_meta.get('round_nr', 1) or 1)
    ))
    
    # ID des erstellten Matches abfragen
    res_m = query_df("SELECT MAX(id) as last_id FROM analytics_matches")
    match_id = int(res_m.iloc[0]['last_id'])
    
    # 2. Legs und Visits speichern & Aggregat-Werte für automatischen Liga-Eintrag sammeln
    player_a_id = match_meta['player_a_id']
    player_b_id = match_meta['player_b_id']
    
    a_legs_won = 0
    a_legs_lost = 0
    a_all_scores = []
    a_first_9_scores = []
    a_first_18_scores = []
    a_s80 = 0
    a_s100 = 0
    a_s140 = 0
    a_s180 = 0
    a_high_finish = 0
    a_short_legs = 0
    total_darts_a = 0
    
    for leg_idx, leg in enumerate(legs_data, 1):
        winner_pid = leg['winner_player_id']
        if winner_pid == player_a_id:
            a_legs_won += 1
        else:
            a_legs_lost += 1
            
        darts_a = int(leg.get('darts_thrown_a', 0) or 0)
        darts_b = int(leg.get('darts_thrown_b', 0) or 0)
        co_a = int(leg.get('checkout_a', 0) or 0)
        co_b = int(leg.get('checkout_b', 0) or 0)
        is_brk = bool(leg.get('is_break', False))
        
        total_darts_a += darts_a
            
        execute_query('''
            INSERT INTO analytics_legs (
                match_id, leg_num, starter_player_id, winner_player_id,
                score_before_a, score_before_b, darts_thrown_a, darts_thrown_b,
                checkout_a, checkout_b, is_break
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id, leg_idx, leg['starter_player_id'], winner_pid,
            leg.get('score_before_a', 0), leg.get('score_before_b', 0),
            darts_a, darts_b, co_a, co_b, is_brk
        ))
        
        res_l = query_df("SELECT MAX(id) as last_id FROM analytics_legs")
        leg_id = int(res_l.iloc[0]['last_id'])
        
        visits_a = leg.get('visits_a', [])
        visits_b = leg.get('visits_b', [])
        
        # Visits von Spieler A speichern
        for v_idx, v in enumerate(visits_a, 1):
            score = int(v['score'])
            rest = int(v['rest_score'])
            opp_rest = int(v.get('opponent_rest', 501) or 501)
            
            execute_query('''
                INSERT INTO analytics_visits (
                    leg_id, player_id, visit_order, score, rest_score, opponent_rest_at_visit
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (leg_id, player_a_id, v_idx, score, rest, opp_rest))
            
            a_all_scores.append(score)
            if v_idx <= 3: a_first_9_scores.append(score)
            if v_idx <= 6: a_first_18_scores.append(score)
            
            if 80 <= score <= 99: a_s80 += 1
            elif 100 <= score <= 139: a_s100 += 1
            elif 140 <= score <= 179: a_s140 += 1
            elif score == 180: a_s180 += 1
            
            # Checkouts / Finishes prüfen
            if (rest == 0 or co_a > 0) and winner_pid == player_a_id:
                fin_score = co_a if co_a > 0 else score
                if fin_score >= 101 and fin_score > a_high_finish:
                    a_high_finish = fin_score
                actual_darts = darts_a if darts_a > 0 else (v_idx * 3)
                if actual_darts <= 18:
                    a_short_legs += 1
                    
        # Visits von Spieler B speichern
        for v_idx, v in enumerate(visits_b, 1):
            score = int(v['score'])
            rest = int(v['rest_score'])
            opp_rest = int(v.get('opponent_rest', 501) or 501)
            
            execute_query('''
                INSERT INTO analytics_visits (
                    leg_id, player_id, visit_order, score, rest_score, opponent_rest_at_visit
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (leg_id, player_b_id, v_idx, score, rest, opp_rest))
            
    # 3. AUTOMATISCHER LIGA-EINTRAG (KEINE DOPPELTE EINGABE!)
    if auto_sync_league and player_a_id > 0:
        # Exakter Average nach 2K Darts Formel: Wenn Darts geworfen angegeben, exakt (Punkte / Darts) * 3
        if total_darts_a > 0 and a_all_scores:
            avg_total = round(float((sum(a_all_scores) / total_darts_a) * 3), 1)
        elif a_all_scores:
            avg_total = round(float(sum(a_all_scores) / len(a_all_scores)), 1)
        else:
            avg_total = 0.0
            
        avg_9 = round(float(sum(a_first_9_scores) / len(a_first_9_scores)), 1) if a_first_9_scores else 0.0
        avg_18 = round(float(sum(a_first_18_scores) / len(a_first_18_scores)), 1) if a_first_18_scores else 0.0
        
        hf_specials = 1 if a_high_finish >= 101 else 0
        specials_count = a_s180 + hf_specials + a_short_legs
        
        league_match_payload = {
            'player_id': player_a_id,
            'match_date': match_meta['match_date'],
            'opponent': match_meta['player_b_name'],
            'legs_won': a_legs_won,
            'legs_lost': a_legs_lost,
            'avg_total': avg_total,
            'avg_9': avg_9,
            'avg_18': avg_18,
            'scores_80': a_s80,
            'scores_100': a_s100,
            'scores_140': a_s140,
            'scores_180': a_s180,
            'high_finishes': a_high_finish,
            'short_legs': a_short_legs,
            'specials_count': specials_count,
            'season': match_meta.get('season', '2026/2027')
        }
        add_match(league_match_payload)
        
        res_lm = query_df("SELECT MAX(id) as last_id FROM matches WHERE player_id = ?", (player_a_id,))
        if not res_lm.empty and res_lm.iloc[0]['last_id']:
            lm_id = int(res_lm.iloc[0]['last_id'])
            execute_query("UPDATE analytics_matches SET league_match_id = ? WHERE id = ?", (lm_id, match_id))
            
    return match_id

def delete_analytics_match(match_id: int, delete_linked_league_match: bool = True):
    """Löscht ein Analytics-Match samt aller Legs und Visits und optional das verknüpfte Liga-Match."""
    # Verknüpfte Liga-Match-ID ermitteln
    res = query_df("SELECT league_match_id FROM analytics_matches WHERE id = ?", (match_id,))
    if not res.empty and pd.notnull(res.iloc[0]['league_match_id']) and delete_linked_league_match:
        lm_id = int(res.iloc[0]['league_match_id'])
        delete_match(lm_id)
        
    # Legs abfragen, um Visits zu löschen
    legs_df = query_df("SELECT id FROM analytics_legs WHERE match_id = ?", (match_id,))
    if not legs_df.empty:
        leg_ids = legs_df['id'].tolist()
        for lid in leg_ids:
            execute_query("DELETE FROM analytics_visits WHERE leg_id = ?", (lid,))
        execute_query("DELETE FROM analytics_legs WHERE match_id = ?", (match_id,))
        
    execute_query("DELETE FROM analytics_matches WHERE id = ?", (match_id,))

def update_analytics_match(
    match_id: int,
    match_meta: Dict[str, Any],
    legs_data: List[Dict[str, Any]],
    auto_sync_league: bool = True
):
    """Aktualisiert ein bestehendes Analytics-Match und synchronisiert bei Bedarf das Liga-Match."""
    # Altes Liga-Match ID behalten
    old_res = query_df("SELECT league_match_id FROM analytics_matches WHERE id = ?", (match_id,))
    old_lm_id = None
    if not old_res.empty and pd.notnull(old_res.iloc[0]['league_match_id']):
        old_lm_id = int(old_res.iloc[0]['league_match_id'])
        
    # 1. Metadaten updaten
    execute_query('''
        UPDATE analytics_matches SET
            player_a_id = ?, player_b_id = ?, player_a_name = ?, player_b_name = ?,
            match_date = ?, event_name = ?, round_name = ?, best_of_legs = ?,
            location = ?, winner_id = ?, season = ?, duration_min = ?,
            start_time = ?, end_time = ?, board_nr = ?, match_nr = ?, round_nr = ?
        WHERE id = ?
    ''', (
        match_meta['player_a_id'], match_meta['player_b_id'],
        match_meta['player_a_name'], match_meta['player_b_name'],
        match_meta['match_date'], match_meta.get('event_name', 'Lions League'),
        match_meta.get('round_name', 'Liga-Spiel'), match_meta.get('best_of_legs', 5),
        match_meta.get('location', 'Heim'), match_meta.get('winner_id'),
        match_meta.get('season', '2026/2027'),
        int(match_meta.get('duration_min', 0) or 0),
        str(match_meta.get('start_time', '') or ''),
        str(match_meta.get('end_time', '') or ''),
        int(match_meta.get('board_nr', 1) or 1),
        int(match_meta.get('match_nr', 0) or 0),
        int(match_meta.get('round_nr', 1) or 1),
        match_id
    ))
    
    # 2. Bestehende Legs & Visits löschen und neu anlegen
    legs_df = query_df("SELECT id FROM analytics_legs WHERE match_id = ?", (match_id,))
    if not legs_df.empty:
        for lid in legs_df['id'].tolist():
            execute_query("DELETE FROM analytics_visits WHERE leg_id = ?", (lid,))
        execute_query("DELETE FROM analytics_legs WHERE match_id = ?", (match_id,))
        
    player_a_id = match_meta['player_a_id']
    player_b_id = match_meta['player_b_id']
    
    a_legs_won = 0
    a_legs_lost = 0
    a_all_scores = []
    a_first_9_scores = []
    a_first_18_scores = []
    a_s80 = 0
    a_s100 = 0
    a_s140 = 0
    a_s180 = 0
    a_high_finish = 0
    a_short_legs = 0
    total_darts_a = 0
    
    for leg_idx, leg in enumerate(legs_data, 1):
        winner_pid = leg['winner_player_id']
        if winner_pid == player_a_id: a_legs_won += 1
        else: a_legs_lost += 1
            
        darts_a = int(leg.get('darts_thrown_a', 0) or 0)
        darts_b = int(leg.get('darts_thrown_b', 0) or 0)
        co_a = int(leg.get('checkout_a', 0) or 0)
        co_b = int(leg.get('checkout_b', 0) or 0)
        is_brk = bool(leg.get('is_break', False))
        
        total_darts_a += darts_a
            
        execute_query('''
            INSERT INTO analytics_legs (
                match_id, leg_num, starter_player_id, winner_player_id,
                score_before_a, score_before_b, darts_thrown_a, darts_thrown_b,
                checkout_a, checkout_b, is_break
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id, leg_idx, leg['starter_player_id'], winner_pid,
            leg.get('score_before_a', 0), leg.get('score_before_b', 0),
            darts_a, darts_b, co_a, co_b, is_brk
        ))
        
        res_l = query_df("SELECT MAX(id) as last_id FROM analytics_legs")
        leg_id = int(res_l.iloc[0]['last_id'])
        
        for v_idx, v in enumerate(leg.get('visits_a', []), 1):
            score = int(v['score'])
            rest = int(v['rest_score'])
            opp_rest = int(v.get('opponent_rest', 501) or 501)
            execute_query('''
                INSERT INTO analytics_visits (leg_id, player_id, visit_order, score, rest_score, opponent_rest_at_visit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (leg_id, player_a_id, v_idx, score, rest, opp_rest))
            
            a_all_scores.append(score)
            if v_idx <= 3: a_first_9_scores.append(score)
            if v_idx <= 6: a_first_18_scores.append(score)
            if 80 <= score <= 99: a_s80 += 1
            elif 100 <= score <= 139: a_s100 += 1
            elif 140 <= score <= 179: a_s140 += 1
            elif score == 180: a_s180 += 1
            if (rest == 0 or co_a > 0) and winner_pid == player_a_id:
                fin_score = co_a if co_a > 0 else score
                if fin_score >= 101 and fin_score > a_high_finish: a_high_finish = fin_score
                actual_darts = darts_a if darts_a > 0 else (v_idx * 3)
                if actual_darts <= 18: a_short_legs += 1
                
        for v_idx, v in enumerate(leg.get('visits_b', []), 1):
            score = int(v['score'])
            rest = int(v['rest_score'])
            opp_rest = int(v.get('opponent_rest', 501) or 501)
            execute_query('''
                INSERT INTO analytics_visits (leg_id, player_id, visit_order, score, rest_score, opponent_rest_at_visit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (leg_id, player_b_id, v_idx, score, rest, opp_rest))
            
    # 3. Synchronisation mit Liga-Match
    if auto_sync_league and player_a_id > 0 and old_lm_id:
        if total_darts_a > 0 and a_all_scores:
            avg_total = round(float((sum(a_all_scores) / total_darts_a) * 3), 1)
        elif a_all_scores:
            avg_total = round(float(sum(a_all_scores) / len(a_all_scores)), 1)
        else:
            avg_total = 0.0
            
        avg_9 = round(float(sum(a_first_9_scores) / len(a_first_9_scores)), 1) if a_first_9_scores else 0.0
        avg_18 = round(float(sum(a_first_18_scores) / len(a_first_18_scores)), 1) if a_first_18_scores else 0.0
        hf_specials = 1 if a_high_finish >= 101 else 0
        specials_count = a_s180 + hf_specials + a_short_legs
        
        league_match_payload = {
            'player_id': player_a_id,
            'match_date': match_meta['match_date'],
            'opponent': match_meta['player_b_name'],
            'legs_won': a_legs_won,
            'legs_lost': a_legs_lost,
            'avg_total': avg_total,
            'avg_9': avg_9,
            'avg_18': avg_18,
            'scores_80': a_s80,
            'scores_100': a_s100,
            'scores_140': a_s140,
            'scores_180': a_s180,
            'high_finishes': a_high_finish,
            'short_legs': a_short_legs,
            'specials_count': specials_count,
            'season': match_meta.get('season', '2026/2027')
        }
        update_match(old_lm_id, league_match_payload)

def get_analytics_match_details(match_id: int) -> Optional[Dict[str, Any]]:
    """Gibt alle Daten eines Analytics-Matches inklusive Legs und Visits strukturiert zurück."""
    m_df = query_df("SELECT * FROM analytics_matches WHERE id = ?", (match_id,))
    if m_df.empty:
        return None
    meta = m_df.iloc[0].to_dict()
    
    legs_df = query_df("SELECT * FROM analytics_legs WHERE match_id = ? ORDER BY leg_num ASC", (match_id,))
    legs = []
    for _, l_row in legs_df.iterrows():
        leg_id = int(l_row['id'])
        v_a_df = query_df("SELECT * FROM analytics_visits WHERE leg_id = ? AND player_id = ? ORDER BY visit_order ASC", (leg_id, int(meta['player_a_id'])))
        v_b_df = query_df("SELECT * FROM analytics_visits WHERE leg_id = ? AND player_id = ? ORDER BY visit_order ASC", (leg_id, int(meta['player_b_id'])))
        
        # Falls Visits unter anderen IDs oder 0 gespeichert wurden
        if v_a_df.empty and v_b_df.empty:
            all_v = query_df("SELECT * FROM analytics_visits WHERE leg_id = ? ORDER BY visit_order ASC", (leg_id,))
            if not all_v.empty:
                p_ids = all_v['player_id'].unique()
                if len(p_ids) >= 1:
                    v_a_df = all_v[all_v['player_id'] == p_ids[0]]
                if len(p_ids) >= 2:
                    v_b_df = all_v[all_v['player_id'] == p_ids[1]]
        
        leg_dict = l_row.to_dict()
        leg_dict['visits_a'] = v_a_df.to_dict(orient='records')
        leg_dict['visits_b'] = v_b_df.to_dict(orient='records')
        legs.append(leg_dict)
        
    meta['legs'] = legs
    return meta

def get_all_analytics_matches(
    player_id: Optional[int] = None,
    player_name: Optional[str] = None,
    season: Optional[str] = None
) -> pd.DataFrame:
    """Ruft alle Analytics-Matches ab, optional gefiltert nach Spieler (ID oder Name) und Saison."""
    conditions = []
    params = []
    
    if player_id:
        if player_name:
            conditions.append("(m.player_a_id = ? OR m.player_b_id = ? OR m.player_a_name LIKE ? OR m.player_b_name LIKE ?)")
            params.extend([player_id, player_id, f"%{player_name}%", f"%{player_name}%"])
        else:
            conditions.append("(m.player_a_id = ? OR m.player_b_id = ?)")
            params.extend([player_id, player_id])
    elif player_name:
        conditions.append("(m.player_a_name LIKE ? OR m.player_b_name LIKE ?)")
        params.extend([f"%{player_name}%", f"%{player_name}%"])
        
    if season and season != "Alle Saisons":
        conditions.append("m.season = ?")
        params.append(season)
        
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f'''
        SELECT m.*
        FROM analytics_matches m
        {where_clause}
        ORDER BY m.match_date DESC, m.match_nr ASC, m.id DESC
    '''
    return query_df(query, tuple(params))

def get_player_leg_visits(player_id: int, season: Optional[str] = None) -> List[List[Dict[str, Any]]]:
    """Lädt alle Visits eines Spielers, gruppiert nach Legs in chronologischer Reihenfolge."""
    conditions = ["v.player_id = ?"]
    params = [player_id]
    
    if season and season != "Alle Saisons":
        conditions.append("m.season = ?")
        params.append(season)
        
    where_clause = "WHERE " + " AND ".join(conditions)
    query = f'''
        SELECT v.id, v.leg_id, v.visit_order, v.score, v.rest_score, v.opponent_rest_at_visit,
               l.leg_num, l.starter_player_id, l.winner_player_id, l.darts_thrown_a, l.darts_thrown_b,
               l.checkout_a, l.checkout_b, l.is_break,
               m.id as match_id, m.player_a_id, m.player_b_id,
               m.match_date, m.season, m.duration_min, m.start_time, m.end_time, m.board_nr
        FROM analytics_visits v
        JOIN analytics_legs l ON v.leg_id = l.id
        JOIN analytics_matches m ON l.match_id = m.id
        {where_clause}
        ORDER BY m.match_date ASC, m.id ASC, l.leg_num ASC, v.visit_order ASC
    '''
    df = query_df(query, tuple(params))
    if df.empty:
        return []
        
    legs_grouped = []
    for _, leg_group in df.groupby('leg_id', sort=False):
        leg_visits = []
        for _, row in leg_group.iterrows():
            is_player_a = (int(row['player_a_id']) == player_id)
            d_thrown = int(row['darts_thrown_a']) if is_player_a else int(row['darts_thrown_b'])
            co = int(row['checkout_a']) if is_player_a else int(row['checkout_b'])
            leg_visits.append({
                'order': int(row['visit_order']),
                'score': int(row['score']),
                'rest_score': int(row['rest_score']),
                'opponent_rest': int(row['opponent_rest_at_visit']) if pd.notnull(row['opponent_rest_at_visit']) else 501,
                'leg_num': int(row['leg_num']),
                'match_id': int(row['match_id']),
                'starter_player_id': int(row['starter_player_id']),
                'winner_player_id': int(row['winner_player_id']),
                'darts_thrown': d_thrown if d_thrown > 0 else None,
                'checkout': co if co > 0 else None,
                'is_break': bool(row['is_break']),
                'match_date': str(row['match_date'])
            })
        legs_grouped.append(leg_visits)
        
    return legs_grouped

def import_analyzer_csv_data(
    csv_source: Any,
    season: str = "2026/2027",
    sync_league: bool = True
) -> Dict[str, Any]:
    """
    Importiert Matches, Legs, Visits und Statistiken aus dem Dart Match Image Analyzer.
    Automatische Deduplizierung (Upsert):
    Bestehende Spiele werden zuverlässig erkannt und überschrieben – keine Doppeleinträge!
    """
    import os
    import re
    from database import get_players, add_match, update_match, add_doubles_match, add_doubles_special
    
    # 1. DataFrames laden (entweder aus Verzeichnispfad oder Dict von UploadedFiles/DFs)
    matches_df = None
    legs_df = None
    visits_df = None
    stats_df = None
    
    if isinstance(csv_source, str):
        p_m = os.path.join(csv_source, "matches.csv")
        p_l = os.path.join(csv_source, "legs.csv")
        p_v = os.path.join(csv_source, "visits.csv")
        p_s = os.path.join(csv_source, "statistics.csv")
        
        # Falls Standard-Namen nicht direkt existieren, nach präfixierten Dateien suchen
        if (not os.path.exists(p_m)) and os.path.isdir(csv_source):
            for fn in os.listdir(csv_source):
                fl = fn.lower()
                fp = os.path.join(csv_source, fn)
                if fl.endswith("matches.csv") and not os.path.exists(p_m): p_m = fp
                elif fl.endswith("legs.csv") and not os.path.exists(p_l): p_l = fp
                elif fl.endswith("visits.csv") and not os.path.exists(p_v): p_v = fp
                elif (fl.endswith("statistics.csv") or fl.endswith("stats.csv")) and not os.path.exists(p_s): p_s = fp
                
        if os.path.exists(p_m):
            try: matches_df = pd.read_csv(p_m, sep=";", encoding="utf-8-sig")
            except Exception: matches_df = pd.read_csv(p_m, sep=",", encoding="utf-8-sig")
        if os.path.exists(p_l):
            try: legs_df = pd.read_csv(p_l, sep=";", encoding="utf-8-sig")
            except Exception: legs_df = pd.read_csv(p_l, sep=",", encoding="utf-8-sig")
        if os.path.exists(p_v):
            try: visits_df = pd.read_csv(p_v, sep=";", encoding="utf-8-sig")
            except Exception: visits_df = pd.read_csv(p_v, sep=",", encoding="utf-8-sig")
        if os.path.exists(p_s):
            try: stats_df = pd.read_csv(p_s, sep=";", encoding="utf-8-sig")
            except Exception: stats_df = pd.read_csv(p_s, sep=",", encoding="utf-8-sig")
    elif isinstance(csv_source, dict):
        for k, v in csv_source.items():
            k_low = k.lower()
            if "matches" in k_low: matches_df = v
            elif "legs" in k_low: legs_df = v
            elif "visits" in k_low: visits_df = v
            elif "statistics" in k_low or "stats" in k_low: stats_df = v
            
    if matches_df is None or matches_df.empty:
        return {"success": False, "message": "Keine matches.csv gefunden oder Datei ist leer.", "created": 0, "updated": 0, "details": []}
        
    players_df = get_players()
    player_map = {row['name'].strip().lower(): int(row['id']) for _, row in players_df.iterrows()}
    
    created_count = 0
    updated_count = 0
    match_details_list = []
    
    def _safe_int(val, default=0):
        try:
            if pd.isnull(val): return default
            return int(float(val))
        except Exception:
            return default

    # Spieltags-Datum ermitteln (aus Ordner, spieltag_info.json oder matches_df)
    spieltag_date_iso = "2026-08-28"
    info_data = {}
    if isinstance(csv_source, str) and os.path.isdir(csv_source):
        # 1. spieltag_info.json
        for fn in os.listdir(csv_source):
            if fn.lower().endswith("spieltag_info.json"):
                try:
                    with open(os.path.join(csv_source, fn), "r", encoding="utf-8") as f:
                        info_data = json.load(f)
                    raw_d = info_data.get("date", "")
                    dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', raw_d)
                    if dm:
                        yp = dm.group(3)
                        if len(yp) == 2: yp = f"20{yp}"
                        spieltag_date_iso = f"{int(yp):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
                except Exception:
                    pass
                break
        # 2. Ordnername / Slug
        if spieltag_date_iso == "2026-08-28":
            dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', os.path.basename(csv_source))
            if dm:
                yp = dm.group(3)
                if len(yp) == 2: yp = f"20{yp}"
                spieltag_date_iso = f"{int(yp):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"

    # 3. Fallback: Suche erstes Datum in matches_df
    if 'start_datetime' in matches_df.columns:
        for val in matches_df['start_datetime'].dropna():
            dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', str(val))
            if dm:
                yp = dm.group(3)
                if len(yp) == 2: yp = f"20{yp}"
                spieltag_date_iso = f"{int(yp):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
                break

    for _, m_row in matches_df.iterrows():
        mid_csv = str(m_row.get('match_id', '')).strip()
        home_p = str(m_row.get('home_player', '')).strip()
        away_p = str(m_row.get('away_player', '')).strip()
        m_nr = _safe_int(m_row.get('match_number'), 0)
        if m_nr == 0 and mid_csv.startswith('M_'):
            try: m_nr = int(mid_csv.replace('M_', ''))
            except: m_nr = 0
            
        board_nr = _safe_int(m_row.get('board'), 1)
        dur_min = _safe_int(m_row.get('duration_minutes'), 0)
        start_dt = str(m_row.get('start_datetime', '')).strip()
        end_dt = str(m_row.get('end_datetime', '')).strip()
        
        # Datum ermitteln (mit Fallback auf Spieltagsdatum)
        m_date = spieltag_date_iso
        date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', start_dt)
        if date_match:
            d_p, m_p, y_p = date_match.groups()
            if len(y_p) == 2: y_p = f"20{y_p}"
            m_date = f"{int(y_p):04d}-{int(m_p):02d}-{int(d_p):02d}"
            
        # Spieler-IDs auflösen
        is_double = ("&" in home_p or "+" in home_p or "&" in away_p)
        p_a_id = player_map.get(home_p.lower(), 0)
        p_b_id = player_map.get(away_p.lower(), 0)
        
        # Falls Doppel: IDs der Partner ermitteln (sowohl Heim als auch Gast!)
        d_a1_id, d_a2_id = 0, 0
        d_b1_id, d_b2_id = 0, 0
        if is_double:
            parts_a = [p.strip() for p in re.split(r'[&+]', home_p)]
            if len(parts_a) >= 2:
                d_a1_id = player_map.get(parts_a[0].lower(), 0)
                d_a2_id = player_map.get(parts_a[1].lower(), 0)
                if p_a_id == 0: p_a_id = d_a1_id if d_a1_id > 0 else 0
            parts_b = [p.strip() for p in re.split(r'[&+]', away_p)]
            if len(parts_b) >= 2:
                d_b1_id = player_map.get(parts_b[0].lower(), 0)
                d_b2_id = player_map.get(parts_b[1].lower(), 0)
                if p_b_id == 0: p_b_id = d_b1_id if d_b1_id > 0 else 0
                
        # Legs filtern
        m_legs_df = legs_df[legs_df['match_id'] == mid_csv].sort_values('leg_number') if legs_df is not None else pd.DataFrame()
        m_visits_df = visits_df[visits_df['match_id'] == mid_csv].sort_values(['leg_number', 'visit_number']) if visits_df is not None else pd.DataFrame()
        
        legs_data = []
        # Legs ermitteln (unterstuezt auch Luecken in leg_number)
        if not m_legs_df.empty:
            avail_legs = sorted(m_legs_df['leg_number'].dropna().unique().tolist())
        elif not m_visits_df.empty:
            avail_legs = sorted(m_visits_df['leg_number'].dropna().unique().tolist())
        else:
            avail_legs = [1, 2, 3]

        # 1. Plausibilitätsprüfung: Einzelsieg erfordert 3 gewonnene Legs (Best of 5)
        m_warnings = []
        res_h = _safe_int(m_row.get('result_home'), 0)
        res_a = _safe_int(m_row.get('result_away'), 0)
        if not is_double and (res_h > 0 or res_a > 0):
            if max(res_h, res_a) < 3:
                m_warnings.append(f"⚠️ Unvollständiges Einzelergebnis ({res_h}:{res_a}) – regulärer Sieg erfordert 3 Legs!")

        home_legs_won = 0
        away_legs_won = 0
        
        for l_num in avail_legs:
            l_meta = m_legs_df[m_legs_df['leg_number'] == l_num] if not m_legs_df.empty else pd.DataFrame()
            starter_str = str(l_meta.iloc[0].get('starter_player', '')).strip() if not l_meta.empty else ''
            winner_str = str(l_meta.iloc[0].get('winner_player', '')).strip() if not l_meta.empty else ''
            
            # Starter & Winner bestimmen
            starter_pid = p_a_id if (starter_str.lower() == home_p.lower() or not starter_str) else p_b_id
            winner_pid = p_a_id if (winner_str.lower() == home_p.lower()) else (p_b_id if winner_str else p_a_id)
            
            # Visits filtern
            v_leg = m_visits_df[m_visits_df['leg_number'] == l_num] if not m_visits_df.empty else pd.DataFrame()
            v_a_list = []
            v_b_list = []
            
            if not v_leg.empty:
                v_a_rows = v_leg[v_leg['player'].str.lower() == home_p.lower()].sort_values('visit_number')
                if v_a_rows.empty and not v_leg.empty:
                    first_p = v_leg['player'].iloc[0]
                    v_a_rows = v_leg[v_leg['player'] == first_p].sort_values('visit_number')
                    v_b_rows = v_leg[v_leg['player'] != first_p].sort_values('visit_number')
                else:
                    v_b_rows = v_leg[v_leg['player'].str.lower() == away_p.lower()].sort_values('visit_number')
                    
                v_a_list = [{'score': _safe_int(r.get('score')), 'rest_score': _safe_int(r.get('remaining_score')), 'opponent_rest': _safe_int(r.get('opponent_remaining_score'), 501)} for _, r in v_a_rows.iterrows()]
                v_b_list = [{'score': _safe_int(r.get('score')), 'rest_score': _safe_int(r.get('remaining_score')), 'opponent_rest': _safe_int(r.get('opponent_remaining_score'), 501)} for _, r in v_b_rows.iterrows()]
                
            # Darts & Checkouts
            if not l_meta.empty:
                d_win = _safe_int(l_meta.iloc[0].get('darts_winner'), 0)
                d_los = _safe_int(l_meta.iloc[0].get('darts_loser'), 0)
                co_win = _safe_int(l_meta.iloc[0].get('checkout_winner'), 0)
                is_brk = bool(l_meta.iloc[0].get('is_break', False))
                
                if winner_str.lower() == home_p.lower():
                    d_a, d_b = d_win, d_los
                    co_a, co_b = co_win, 0
                else:
                    d_a, d_b = d_los, d_win
                    co_a, co_b = 0, co_win
            else:
                d_a = len(v_a_list) * 3 if v_a_list else 25
                d_b = len(v_b_list) * 3 if v_b_list else 25
                co_a = v_a_list[-1]['score'] if (v_a_list and v_a_list[-1]['rest_score'] == 0) else 0
                co_b = v_b_list[-1]['score'] if (v_b_list and v_b_list[-1]['rest_score'] == 0) else 0
                is_brk = False
                
            if winner_pid == p_a_id: home_legs_won += 1
            else: away_legs_won += 1
                
            legs_data.append({
                'leg_num': l_num,
                'starter_player_id': starter_pid,
                'winner_player_id': winner_pid,
                'darts_thrown_a': d_a,
                'darts_thrown_b': d_b,
                'checkout_a': co_a,
                'checkout_b': co_b,
                'is_break': is_brk,
                'visits_a': v_a_list,
                'visits_b': v_b_list
            })
            
        # Match Winner ID
        match_winner_id = p_a_id if home_legs_won > away_legs_won else p_b_id
        
        # ----------------------------------------------------
        # 2. DEDUPLIZIERUNG (UPSERT)
        # ----------------------------------------------------
        existing_m = query_df('''
            SELECT id, league_match_id FROM analytics_matches
            WHERE season = ? AND (
                (match_nr = ? AND match_nr > 0 AND match_date = ?) OR
                (player_a_name = ? AND player_b_name = ? AND match_date = ?)
            )
        ''', (season, m_nr, m_date, home_p, away_p, m_date))
        
        existing_match_id = None
        linked_lm_id = None
        
        if not existing_m.empty:
            existing_match_id = int(existing_m.iloc[0]['id'])
            if pd.notnull(existing_m.iloc[0]['league_match_id']):
                linked_lm_id = int(existing_m.iloc[0]['league_match_id'])
                
        location_str = 'Heim'
        if 'is_home' in info_data:
            location_str = 'Heim' if info_data['is_home'] else 'Auswärts'
        elif p_b_id > 0 and p_a_id == 0:
            location_str = 'Auswärts'

        match_meta = {
            'player_a_id': p_a_id,
            'player_b_id': p_b_id,
            'player_a_name': home_p,
            'player_b_name': away_p,
            'match_date': m_date,
            'event_name': 'Lions League',
            'round_name': 'Liga-Spiel',
            'best_of_legs': len(legs_data),
            'location': location_str,
            'winner_id': match_winner_id,
            'season': season,
            'duration_min': dur_min,
            'start_time': start_dt,
            'end_time': end_dt,
            'board_nr': board_nr,
            'match_nr': m_nr,
            'round_nr': 1
        }
        
        if existing_match_id:
            # UPDATE bestehendes Match
            update_analytics_match(existing_match_id, match_meta, legs_data, auto_sync_league=False)
            mid_saved = existing_match_id
            updated_count += 1
            action_str = "🔄 Aktualisiert & Ersetzt"
        else:
            # INSERT neues Match
            mid_saved = save_full_analytics_match(match_meta, legs_data, auto_sync_league=False)
            created_count += 1
            action_str = "✨ Neu angelegt"
            
        # 3. Liga-Rangliste synchronisieren (Unterstützt Heim & Auswärts!)
        if sync_league:
            sync_targets = []
            if is_double:
                if d_a1_id > 0 and d_a2_id > 0:
                    sync_targets.append({
                        'is_double': True,
                        'p1': d_a1_id,
                        'p2': d_a2_id,
                        'opp': away_p,
                        'legs_won': home_legs_won,
                        'legs_lost': away_legs_won,
                        'visits': [v['score'] for l in legs_data for v in l['visits_a']],
                        'first_9': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_a']) if idx < 3],
                        'first_18': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_a']) if idx < 6],
                        'total_darts': sum(l['darts_thrown_a'] for l in legs_data),
                        'hf': max([l['checkout_a'] for l in legs_data if l['checkout_a'] > 0] + [0]),
                        'sl': sum(1 for l in legs_data if l['winner_player_id'] == p_a_id and 0 < l['darts_thrown_a'] <= 18)
                    })
                if d_b1_id > 0 and d_b2_id > 0:
                    sync_targets.append({
                        'is_double': True,
                        'p1': d_b1_id,
                        'p2': d_b2_id,
                        'opp': home_p,
                        'legs_won': away_legs_won,
                        'legs_lost': home_legs_won,
                        'visits': [v['score'] for l in legs_data for v in l['visits_b']],
                        'first_9': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_b']) if idx < 3],
                        'first_18': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_b']) if idx < 6],
                        'total_darts': sum(l['darts_thrown_b'] for l in legs_data),
                        'hf': max([l['checkout_b'] for l in legs_data if l['checkout_b'] > 0] + [0]),
                        'sl': sum(1 for l in legs_data if l['winner_player_id'] == p_b_id and 0 < l['darts_thrown_b'] <= 18)
                    })
            else:
                if p_a_id > 0:
                    sync_targets.append({
                        'is_double': False,
                        'player_id': p_a_id,
                        'opp': away_p,
                        'legs_won': home_legs_won,
                        'legs_lost': away_legs_won,
                        'visits': [v['score'] for l in legs_data for v in l['visits_a']],
                        'first_9': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_a']) if idx < 3],
                        'first_18': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_a']) if idx < 6],
                        'total_darts': sum(l['darts_thrown_a'] for l in legs_data),
                        'hf': max([l['checkout_a'] for l in legs_data if l['checkout_a'] > 0] + [0]),
                        'sl': sum(1 for l in legs_data if l['winner_player_id'] == p_a_id and 0 < l['darts_thrown_a'] <= 18)
                    })
                if p_b_id > 0:
                    sync_targets.append({
                        'is_double': False,
                        'player_id': p_b_id,
                        'opp': home_p,
                        'legs_won': away_legs_won,
                        'legs_lost': home_legs_won,
                        'visits': [v['score'] for l in legs_data for v in l['visits_b']],
                        'first_9': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_b']) if idx < 3],
                        'first_18': [v['score'] for l in legs_data for idx, v in enumerate(l['visits_b']) if idx < 6],
                        'total_darts': sum(l['darts_thrown_b'] for l in legs_data),
                        'hf': max([l['checkout_b'] for l in legs_data if l['checkout_b'] > 0] + [0]),
                        'sl': sum(1 for l in legs_data if l['winner_player_id'] == p_b_id and 0 < l['darts_thrown_b'] <= 18)
                    })

            for tgt in sync_targets:
                v_all = tgt['visits']
                t_darts = tgt['total_darts']
                avg_total = round(float((sum(v_all) / t_darts) * 3), 1) if (t_darts > 0 and v_all) else (round(float(np.mean(v_all)), 1) if v_all else 0.0)
                
                # ----------------------------------------------------
                # SICHERHEITSEBENE: Plausibilisierung gegen Gesamt-Average (statistics.csv)
                # ----------------------------------------------------
                stats_p_name = home_p if tgt.get('player_id') == p_a_id else away_p
                if tgt.get('is_double'):
                    stats_p_name = home_p if tgt.get('p1') in [d_a1_id, d_a2_id] else away_p
                    
                if stats_df is not None and not stats_df.empty:
                    m_stat = stats_df[(stats_df['match_id'] == mid_csv) & (stats_df['player'].str.lower() == stats_p_name.lower())]
                    if not m_stat.empty:
                        ref_avg_raw = m_stat.iloc[0].get('overall_average')
                        if pd.notnull(ref_avg_raw):
                            try:
                                ref_avg = round(float(ref_avg_raw), 1)
                                if ref_avg > 0:
                                    avg_diff = round(abs(avg_total - ref_avg), 1)
                                    if avg_diff > 0.05:
                                        m_warnings.append(
                                            f"ℹ️ Offizieller Spieltags-Average übernommen für {stats_p_name}: {ref_avg:.1f} (Visits-Schnitt: {avg_total:.1f})"
                                        )
                                    # Immer den offiziellen/manuell vorgegebenen Average nutzen!
                                    avg_total = ref_avg
                            except Exception:
                                pass

                avg_9 = round(float(np.mean(tgt['first_9'])), 1) if tgt['first_9'] else 0.0
                avg_18 = round(float(np.mean(tgt['first_18'])), 1) if tgt['first_18'] else 0.0
                s80 = sum(1 for s in v_all if 80 <= s <= 99)
                s100 = sum(1 for s in v_all if 100 <= s <= 139)
                s140 = sum(1 for s in v_all if 140 <= s <= 179)
                s180 = sum(1 for s in v_all if s == 180)
                hf = tgt['hf']
                sl = tgt['sl']
                specials = s180 + (1 if hf >= 101 else 0) + sl
                
                if tgt['is_double']:
                    dm_payload = {
                        'player1_id': tgt['p1'],
                        'player2_id': tgt['p2'],
                        'match_date': m_date,
                        'opponent': tgt['opp'],
                        'legs_won': tgt['legs_won'],
                        'legs_lost': tgt['legs_lost'],
                        'avg_total': avg_total,
                        'avg_9': avg_9,
                        'avg_18': avg_18,
                        'scores_80': s80,
                        'scores_100': s100,
                        'scores_140': s140,
                        'scores_180': s180,
                        'high_finishes': hf,
                        'short_legs': sl,
                        'specials_count': specials,
                        'season': season
                    }
                    if linked_lm_id:
                        execute_query('''
                            UPDATE doubles_matches SET
                                player1_id = ?, player2_id = ?, match_date = ?, opponent = ?,
                                legs_won = ?, legs_lost = ?, avg_total = ?, avg_9 = ?, avg_18 = ?,
                                scores_80 = ?, scores_100 = ?, scores_140 = ?, scores_180 = ?,
                                high_finishes = ?, short_legs = ?, specials_count = ?, season = ?
                            WHERE id = ?
                        ''', (
                            tgt['p1'], tgt['p2'], m_date, tgt['opp'], tgt['legs_won'], tgt['legs_lost'],
                            avg_total, avg_9, avg_18, s80, s100, s140, s180, hf, sl, specials, season,
                            linked_lm_id
                        ))
                    else:
                        add_doubles_match(dm_payload)
                        res_lm = query_df("SELECT MAX(id) as last_id FROM doubles_matches WHERE player1_id = ? AND player2_id = ?", (tgt['p1'], tgt['p2']))
                        if not res_lm.empty and res_lm.iloc[0]['last_id']:
                            new_lm_id = int(res_lm.iloc[0]['last_id'])
                            execute_query("UPDATE analytics_matches SET league_match_id = ? WHERE id = ?", (new_lm_id, mid_saved))

                    # Doppel-Specials in doubles_specials synchronisieren (+0,5 Pkt Bonus in Rangliste)
                    if s180 > 0 or hf >= 101 or sl > 0:
                        p1_row = players_df[players_df['id'] == tgt['p1']]
                        p2_row = players_df[players_df['id'] == tgt['p2']]
                        p1_name_str = p1_row.iloc[0]['name'] if not p1_row.empty else "Partner"
                        p2_name_str = p2_row.iloc[0]['name'] if not p2_row.empty else "Partner"
                        opp_team = info_data.get('opponent', tgt['opp'])

                        # 180er High Score: Genau dem Spieler zuordnen (in Supabase: player1 / Sebastian Kirste)
                        if s180 > 0:
                            for _ in range(s180):
                                pid = tgt['p1']
                                partner = p2_name_str
                                chk = query_df('''
                                    SELECT id FROM doubles_specials 
                                    WHERE player_id = ? AND match_date = ? AND special_type LIKE '%180%' AND season = ?
                                ''', (pid, m_date, season))
                                if chk.empty:
                                    add_doubles_special(
                                        player_id=pid,
                                        partner_name=partner,
                                        opponent_team=opp_team,
                                        match_date=m_date,
                                        special_type="180er High Score 🎯",
                                        description=f"180er im Doppel mit {partner}",
                                        season=season
                                    )

                        # High Finish (>= 101)
                        if hf >= 101:
                            for pid, pname, partner in [(tgt['p1'], p1_name_str, p2_name_str), (tgt['p2'], p2_name_str, p1_name_str)]:
                                chk = query_df('''
                                    SELECT id FROM doubles_specials 
                                    WHERE player_id = ? AND match_date = ? AND special_type LIKE '%High Finish%' AND season = ?
                                ''', (pid, m_date, season))
                                if chk.empty:
                                    add_doubles_special(
                                        player_id=pid,
                                        partner_name=partner,
                                        opponent_team=opp_team,
                                        match_date=m_date,
                                        special_type="High Finish (101 - 170) 🏁",
                                        description=f"{hf}er Checkout im Doppel",
                                        season=season
                                    )

                        # Short Leg (<= 18 Darts)
                        if sl > 0:
                            for pid, pname, partner in [(tgt['p1'], p1_name_str, p2_name_str), (tgt['p2'], p2_name_str, p1_name_str)]:
                                chk = query_df('''
                                    SELECT id FROM doubles_specials 
                                    WHERE player_id = ? AND match_date = ? AND special_type LIKE '%Short%' AND season = ?
                                ''', (pid, m_date, season))
                                if chk.empty:
                                    add_doubles_special(
                                        player_id=pid,
                                        partner_name=partner,
                                        opponent_team=opp_team,
                                        match_date=m_date,
                                        special_type="Short Game (≤ 18 Darts) 🏹",
                                        description="Short Leg im Doppel",
                                        season=season
                                    )
                else:
                    sm_payload = {
                        'player_id': tgt['player_id'],
                        'match_date': m_date,
                        'opponent': tgt['opp'],
                        'legs_won': tgt['legs_won'],
                        'legs_lost': tgt['legs_lost'],
                        'avg_total': avg_total,
                        'avg_9': avg_9,
                        'avg_18': avg_18,
                        'scores_80': s80,
                        'scores_100': s100,
                        'scores_140': s140,
                        'scores_180': s180,
                        'high_finishes': hf,
                        'short_legs': sl,
                        'specials_count': specials,
                        'season': season
                    }
                    if linked_lm_id:
                        update_match(linked_lm_id, sm_payload)
                    else:
                        add_match(sm_payload)
                        res_lm = query_df("SELECT MAX(id) as last_id FROM matches WHERE player_id = ?", (tgt['player_id'],))
                        if not res_lm.empty and res_lm.iloc[0]['last_id']:
                            new_lm_id = int(res_lm.iloc[0]['last_id'])
                            execute_query("UPDATE analytics_matches SET league_match_id = ? WHERE id = ?", (new_lm_id, mid_saved))
                        
        status_full = action_str
        if m_warnings:
            status_full += " (" + "; ".join(m_warnings) + ")"
            
        match_details_list.append({
            'match_nr': m_nr,
            'match_id': mid_csv,
            'home_player': home_p,
            'away_player': away_p,
            'score': f"{home_legs_won}:{away_legs_won}",
            'status': status_full,
            'warnings': m_warnings
        })
        
    return {
        "success": True,
        "message": f"{created_count + updated_count} Matches erfolgreich verarbeitet ({created_count} neu, {updated_count} aktualisiert/ersetzt).",
        "created": created_count,
        "updated": updated_count,
        "details": match_details_list
    }


def scan_main_directory_for_spieltage(root_dir: str, season: str = "2026/2027") -> List[Dict[str, Any]]:
    """
    Durchsucht den Hauptordner und alle Unterordner rekursiv nach Spieltagen
    (sowohl mit präfixierten Dateinamen wie {slug}_matches.csv als auch matches.csv).
    Gleicht gefundene Matches mit der Datenbank ab und kennzeichnet, welche Daten NEU sind.
    """
    import os
    import json
    import re
    import datetime
    
    if not root_dir or not os.path.exists(root_dir):
        return []
        
    found_spieltage = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        # Suchen nach matches.csv oder *_matches.csv
        match_files = [f for f in filenames if f.lower().endswith("matches.csv")]
        if not match_files:
            continue
            
        # Nimm die spezifischste Datei (präfixierte Datei bevorzugen)
        match_file = sorted(match_files, key=lambda x: len(x), reverse=True)[0]
        full_match_path = os.path.join(dirpath, match_file)
        
        # Zugehörige Dateien ermitteln
        prefix = match_file[:-11]  # z.B. "{slug}_"
        info_file = next((f for f in filenames if f.lower().endswith("spieltag_info.json")), "spieltag_info.json")
        
        # Spieltag-Info laden falls vorhanden
        info_data = {}
        info_path = os.path.join(dirpath, info_file)
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    info_data = json.load(f)
            except Exception:
                pass
                
        # Matches-CSV einlesen, um Inhalt zu analysieren
        try:
            m_df = pd.read_csv(full_match_path, sep=";", encoding="utf-8-sig")
        except Exception:
            try:
                m_df = pd.read_csv(full_match_path, sep=",", encoding="utf-8-sig")
            except Exception:
                continue
                
        if m_df.empty:
            continue
            
        total_matches = len(m_df)
        
        # Metadaten aus Info-JSON oder CSV/Ordner
        slug = info_data.get("slug") or prefix.rstrip("_") or os.path.basename(dirpath)
        team = info_data.get("team")
        opp = info_data.get("opponent")
        dt_str = info_data.get("date")
        sp_nr = info_data.get("matchday_nr")
        
        # Falls nicht in Info-JSON, aus Matches-CSV oder Ordnername/Slug ableiten
        if not dt_str and 'start_datetime' in m_df.columns:
            for val in m_df['start_datetime'].dropna():
                dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', str(val))
                if dm:
                    dt_str = f"{int(dm.group(1)):02d}.{int(dm.group(2)):02d}.{dm.group(3)}"
                    break
        if not dt_str and slug:
            dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', slug)
            if dm:
                dt_str = f"{int(dm.group(1)):02d}.{int(dm.group(2)):02d}.{dm.group(3)}"
                
        spieltag_date_iso = "2026-08-28"
        if dt_str:
            dm = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', dt_str)
            if dm:
                yp = dm.group(3)
                if len(yp) == 2: yp = f"20{yp}"
                spieltag_date_iso = f"{int(yp):04d}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}"
                
        # Status gegen DB abgleichen
        new_count = 0
        existing_count = 0
        
        for _, m_row in m_df.iterrows():
            mid_csv = str(m_row.get('match_id', '')).strip()
            home_p = str(m_row.get('home_player', '')).strip()
            away_p = str(m_row.get('away_player', '')).strip()
            m_nr = int(m_row.get('match_number', 0) or 0)
            if m_nr == 0 and mid_csv.startswith('M_'):
                try: m_nr = int(mid_csv.replace('M_', ''))
                except: m_nr = 0
                
            start_dt = str(m_row.get('start_datetime', '')).strip()
            m_date = spieltag_date_iso
            date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', start_dt)
            if date_match:
                d_p, m_p, y_p = date_match.groups()
                if len(y_p) == 2: y_p = f"20{y_p}"
                m_date = f"{int(y_p):04d}-{int(m_p):02d}-{int(d_p):02d}"
                
            check_q = '''
                SELECT id FROM analytics_matches
                WHERE season = ? AND (
                    (match_nr = ? AND match_nr > 0 AND match_date = ?) OR
                    (player_a_name = ? AND player_b_name = ? AND match_date = ?)
                )
            '''
            chk_df = query_df(check_q, (season, m_nr, m_date, home_p, away_p, m_date))
            if chk_df.empty:
                new_count += 1
            else:
                existing_count += 1
                
        # Status bestimmen
        file_mtime = os.path.getmtime(full_match_path)
        mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime("%d.%m.%Y %H:%M")
        
        if existing_count == 0:
            status = "NEW"
            status_badge = "🟢 NEU"
            status_desc = f"{new_count} neue Spiele"
        elif new_count > 0:
            status = "PARTIAL"
            status_badge = "🟡 TEILWEISE NEU"
            status_desc = f"{new_count} neu, {existing_count} vorhanden"
        else:
            status = "EXISTS"
            status_badge = "⚪ VORHANDEN"
            status_desc = f"Alle {existing_count} Spiele in DB"
            
        team_display = team if team else ("Lions A" if "Lions-A" in slug else ("Lions B" if "Lions-B" in slug else "Lions"))
        opp_display = opp if opp else ("Gegner" if not slug else slug.split("_vs_")[-1].replace("-", " ") if "_vs_" in slug else "Unbekannt")
        sp_display = f"Spieltag {sp_nr}" if sp_nr else ("Spieltag ?" if "SP" not in slug else f"Spieltag {int(slug.split('_SP')[1][:2])}")
        
        found_spieltage.append({
            'dir_path': dirpath,
            'match_file': full_match_path,
            'slug': slug,
            'team_display': team_display,
            'opp_display': opp_display,
            'sp_display': sp_display,
            'date_str': dt_str or "Unbekannt",
            'total_matches': total_matches,
            'new_count': new_count,
            'existing_count': existing_count,
            'status': status,
            'status_badge': status_badge,
            'status_desc': status_desc,
            'mtime_str': mtime_str,
            'is_new_candidate': (status in ["NEW", "PARTIAL"])
        })
        
    return sorted(found_spieltage, key=lambda x: (not x['is_new_candidate'], x['date_str']), reverse=False)


def batch_import_spieltage(selected_spieltage: List[Dict[str, Any]], season: str = "2026/2027", sync_league: bool = True) -> Dict[str, Any]:
    """
    Importiert eine Liste von gescannten Spieltagen im Batch.
    Gibt eine detaillierte Zusammenfassung zurück.
    """
    import os
    total_created = 0
    total_updated = 0
    imported_count = 0
    results = []
    
    for sp in selected_spieltage:
        dir_p = sp.get('dir_path')
        if not dir_p or not os.path.exists(dir_p):
            continue
            
        res = import_analyzer_csv_data(dir_p, season=season, sync_league=sync_league)
        if res.get('success'):
            imported_count += 1
            total_created += res.get('created', 0)
            total_updated += res.get('updated', 0)
            results.append({
                'slug': sp.get('slug', os.path.basename(dir_p)),
                'team': sp.get('team_display', ''),
                'opponent': sp.get('opp_display', ''),
                'created': res.get('created', 0),
                'updated': res.get('updated', 0),
                'success': True
            })
        else:
            results.append({
                'slug': sp.get('slug', os.path.basename(dir_p)),
                'error': res.get('message', 'Unbekannter Fehler'),
                'success': False
            })
            
    return {
        'imported_spieltage': imported_count,
        'total_created': total_created,
        'total_updated': total_updated,
        'results': results
    }


