"""
Datenbank-Loader für die Testumgebung.
Schreibt validierte Spieldaten sicher und atomar in test_dart_data.db.
"""
import os
import sqlite3
from typing import Dict, List, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "test_dart_data.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_player_id_by_name(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Sucht die Spieler-ID in der players Tabelle."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE name = ?", (name.strip(),))
    row = cur.fetchone()
    if row:
        return row[0]
    return None

def write_single_match(conn: sqlite3.Connection, match_data: Dict[str, Any]) -> int:
    """Schreibt ein Einzel-Match in die Tabelle matches."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matches (
            player_id, match_date, opponent, legs_won, legs_lost,
            avg_total, avg_9, avg_18, scores_80, scores_100,
            scores_140, scores_180, high_finishes, short_legs,
            specials_count, season
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_data['player_id'],
        match_data['match_date'],
        match_data['opponent'],
        match_data['legs_won'],
        match_data['legs_lost'],
        match_data['avg_total'],
        match_data['avg_9'],
        match_data.get('avg_18', 0.0),
        match_data.get('scores_80', 0),
        match_data.get('scores_100', 0),
        match_data.get('scores_140', 0),
        match_data.get('scores_180', 0),
        match_data.get('high_finishes', 0),
        match_data.get('short_legs', 0),
        match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027')
    ))
    return cur.lastrowid

def write_doubles_match(conn: sqlite3.Connection, match_data: Dict[str, Any]) -> int:
    """Schreibt ein Doppel-Match in die Tabelle doubles_matches."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO doubles_matches (
            player1_id, player2_id, match_date, opponent, legs_won, legs_lost,
            avg_total, avg_9, avg_18, scores_80, scores_100,
            scores_140, scores_180, high_finishes, short_legs, specials_count, season
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_data['player1_id'],
        match_data['player2_id'],
        match_data['match_date'],
        match_data['opponent'],
        match_data['legs_won'],
        match_data['legs_lost'],
        match_data['avg_total'],
        match_data['avg_9'],
        match_data.get('avg_18', 0.0),
        match_data.get('scores_80', 0),
        match_data.get('scores_100', 0),
        match_data.get('scores_140', 0),
        match_data.get('scores_180', 0),
        match_data.get('high_finishes', 0),
        match_data.get('short_legs', 0),
        match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027')
    ))
    return cur.lastrowid

def write_analytics_match(conn: sqlite3.Connection, meta: Dict[str, Any]) -> int:
    """Schreibt Match-Metadaten in analytics_matches."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analytics_matches (
            player_a_id, player_b_id, player_a_name, player_b_name, match_date,
            event_name, round_name, best_of_legs, location, winner_id, season,
            duration_min, start_time, end_time, board_nr, match_nr, round_nr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meta.get('player_a_id', 0),
        meta.get('player_b_id', 0),
        meta.get('player_a_name', ''),
        meta.get('player_b_name', ''),
        meta.get('match_date', ''),
        meta.get('event_name', 'Lions League'),
        meta.get('round_name', 'Liga-Spiel'),
        meta.get('best_of_legs', 5),
        meta.get('location', 'Heim'),
        meta.get('winner_id', 0),
        meta.get('season', '2026/2027'),
        meta.get('duration_min', 0),
        meta.get('start_time', ''),
        meta.get('end_time', ''),
        meta.get('board_nr', 1),
        meta.get('match_nr', 0),
        meta.get('round_nr', 1)
    ))
    return cur.lastrowid
