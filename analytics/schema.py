"""
Datenbank-Initialisierung und Schema-Definition für die Dart Analytics Engine.
Funktioniert nahtlos sowohl mit SQLite als auch mit Supabase PostgreSQL.
"""
from database import execute_query, query_df

def init_analytics_db():
    """Erstellt alle notwendigen Tabellen für die Analytics Engine."""
    
    # 1. Tabelle: analytics_matches
    execute_query('''
        CREATE TABLE IF NOT EXISTS analytics_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_a_id INTEGER NOT NULL,
            player_b_id INTEGER NOT NULL,
            player_a_name TEXT NOT NULL,
            player_b_name TEXT NOT NULL,
            match_date TEXT NOT NULL,
            event_name TEXT DEFAULT 'Lions League',
            round_name TEXT DEFAULT 'Liga-Spiel',
            best_of_legs INTEGER DEFAULT 5,
            location TEXT DEFAULT 'Heim',
            winner_id INTEGER,
            season TEXT DEFAULT '2026/2027',
            league_match_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Tabelle: analytics_legs
    execute_query('''
        CREATE TABLE IF NOT EXISTS analytics_legs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            leg_num INTEGER NOT NULL,
            starter_player_id INTEGER NOT NULL,
            winner_player_id INTEGER NOT NULL,
            score_before_a INTEGER DEFAULT 0,
            score_before_b INTEGER DEFAULT 0,
            FOREIGN KEY (match_id) REFERENCES analytics_matches(id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Tabelle: analytics_visits
    execute_query('''
        CREATE TABLE IF NOT EXISTS analytics_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leg_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            visit_order INTEGER NOT NULL,
            score INTEGER NOT NULL,
            rest_score INTEGER NOT NULL,
            opponent_rest_at_visit INTEGER,
            FOREIGN KEY (leg_id) REFERENCES analytics_legs(id) ON DELETE CASCADE
        )
    ''')

    # Migrationen / Spaltenerweiterungen für 2K Darts Daten (Dauer, Startzeit, Endzeit, Darts/Leg)
    for col_def in [
        ("analytics_matches", "duration_min INTEGER DEFAULT 0"),
        ("analytics_matches", "start_time TEXT DEFAULT ''"),
        ("analytics_matches", "end_time TEXT DEFAULT ''"),
        ("analytics_matches", "board_nr INTEGER DEFAULT 1"),
        ("analytics_matches", "match_nr INTEGER DEFAULT 0"),
        ("analytics_matches", "round_nr INTEGER DEFAULT 1"),
        ("analytics_legs", "darts_thrown_a INTEGER DEFAULT 0"),
        ("analytics_legs", "darts_thrown_b INTEGER DEFAULT 0"),
        ("analytics_legs", "checkout_a INTEGER DEFAULT 0"),
        ("analytics_legs", "checkout_b INTEGER DEFAULT 0"),
        ("analytics_legs", "is_break BOOLEAN DEFAULT FALSE")
    ]:
        table, col = col_def
        try:
            execute_query(f"ALTER TABLE {table} ADD COLUMN {col}")
        except Exception:
            pass

