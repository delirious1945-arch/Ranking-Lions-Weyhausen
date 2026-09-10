import sqlite3
import pandas as pd
import os
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dart_data.db")

def get_db_url():
    """Prüft, ob eine Supabase / PostgreSQL Verbindung konfigurert ist."""
    raw_url = None
    # 1. Streamlit Secrets (st.secrets["postgres"]["url"] oder st.secrets["SUPABASE_URL"])
    try:
        import streamlit.runtime
        if streamlit.runtime.exists():
            if "postgres" in st.secrets:
                if st.secrets["postgres"].get("use_local", False):
                    return None
                if "url" in st.secrets["postgres"]:
                    url = st.secrets["postgres"]["url"]
                    if url and "[YOUR-PASSWORD]" not in url:
                        raw_url = url
            elif "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
                if url and "[YOUR-PASSWORD]" not in url:
                    raw_url = url
    except Exception:
        pass
    
    # 2. Umgebungsvariable
    if not raw_url:
        env_url = os.environ.get("SUPABASE_URL") or os.environ.get("DATABASE_URL")
        if env_url and "[YOUR-PASSWORD]" not in env_url:
            raw_url = env_url
            
    if not raw_url:
        return None
        
    # Automatische Pooler-Konvertierung: Streamlit Cloud unterstützt oft nur IPv4.
    # Direkte Verbindungen (db.<ref>.supabase.co) sind rein IPv6.
    # Wir wandeln sie automatisch in den IPv4-kompatiblen Connection Pooler um.
    import re
    m = re.search(r'postgresql://([^:]+):([^@]+)@db\.([a-z0-9]+)\.supabase\.co:(\d+)/(.+)', raw_url)
    if m:
        user, pwd, ref, port, db = m.groups()
        # Falls [ ] noch im Passwort stehen
        pwd = pwd.strip('[]')
        # URL encode ! falls noch nicht kodiert
        if '!' in pwd and '%21' not in pwd:
            pwd = pwd.replace('!', '%21')
        pooler_user = f"{user}.{ref}" if not user.endswith(ref) else user
        return f"postgresql://{pooler_user}:{pwd}@aws-0-eu-central-1.pooler.supabase.com:5432/{db}"
        
    return raw_url

def is_postgres():
    return get_db_url() is not None

_engine = None

def get_engine():
    global _engine
    db_url = get_db_url()
    if db_url and _engine is None:
        from sqlalchemy import create_engine
        _engine = create_engine(db_url, pool_pre_ping=True)
    return _engine

def get_connection():
    db_url = get_db_url()
    if db_url:
        import psycopg2
        return psycopg2.connect(db_url)
    else:
        return sqlite3.connect(DB_PATH)

def execute_query(sql, params=()):
    """Führt eine Schreib-Abfrage aus (CREATE, INSERT, UPDATE, DELETE)."""
    if is_postgres():
        from sqlalchemy import text
        engine = get_engine()
        pg_sql = sql.replace('?', '%s')
        pg_sql = pg_sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        pg_sql = pg_sql.replace('INTEGER PRIMARY KEY CHECK (id = 1)', 'INTEGER PRIMARY KEY')
        conn = get_connection()
        c = conn.cursor()
        c.execute(pg_sql, params)
        conn.commit()
        conn.close()
    else:
        conn = get_connection()
        c = conn.cursor()
        c.execute(sql, params)
        conn.commit()
        conn.close()

def query_df(sql, params=()):
    """Führt eine Lese-Abfrage aus und gibt ein Pandas DataFrame zurück."""
    if is_postgres():
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            if params:
                pg_sql = sql.replace('?', '%s')
                raw_conn = conn.connection
                df = pd.read_sql_query(pg_sql, raw_conn, params=params)
            else:
                df = pd.read_sql_query(text(sql), conn)
        return df
    else:
        conn = get_connection()
        df = pd.read_sql_query(sql, conn, params=params if params else None)
        conn.close()
        return df

def init_db():
    # Tabelle: Spieler
    execute_query('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            team TEXT NOT NULL,
            password TEXT DEFAULT 'lions2026',
            must_change_password INTEGER DEFAULT 1,
            role TEXT DEFAULT 'player'
        )
    ''')
    
    # Migration für bestehende DB-Tabellen falls Spalten fehlen
    try: execute_query("ALTER TABLE players ADD COLUMN password TEXT DEFAULT 'lions2026'")
    except: pass
    try: execute_query("ALTER TABLE players ADD COLUMN must_change_password INTEGER DEFAULT 1")
    except: pass
    try: execute_query("ALTER TABLE players ADD COLUMN role TEXT DEFAULT 'player'")
    except: pass
    
    # Tabelle: Einstellungen
    execute_query('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            win_weight REAL NOT NULL,
            avg_weight REAL NOT NULL,
            avg9_weight REAL NOT NULL,
            avg18_weight REAL NOT NULL,
            scores_weight REAL NOT NULL
        )
    ''')
    
    # Standard-Einstellungen einfügen falls leer
    df_set = query_df("SELECT COUNT(*) as cnt FROM settings")
    if df_set.empty or df_set.iloc[0]['cnt'] == 0:
        execute_query('''
            INSERT INTO settings (id, win_weight, avg_weight, avg9_weight, avg18_weight, scores_weight)
            VALUES (1, 20.0, 20.0, 20.0, 20.0, 20.0)
        ''')
        
    # Tabelle: Einzel-Matches
    execute_query('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            opponent TEXT NOT NULL,
            legs_won INTEGER NOT NULL,
            legs_lost INTEGER NOT NULL,
            avg_total REAL NOT NULL,
            avg_9 REAL NOT NULL,
            avg_18 REAL NOT NULL,
            scores_80 INTEGER NOT NULL,
            scores_100 INTEGER NOT NULL,
            scores_140 INTEGER NOT NULL,
            scores_180 INTEGER NOT NULL,
            high_finishes INTEGER NOT NULL,
            short_legs INTEGER NOT NULL,
            specials_count INTEGER DEFAULT 0,
            season TEXT DEFAULT '2026/2027',
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    try: execute_query("ALTER TABLE matches ADD COLUMN specials_count INTEGER DEFAULT 0")
    except: pass
    try: execute_query("ALTER TABLE matches ADD COLUMN season TEXT DEFAULT '2026/2027'")
    except: pass

    # Tabelle: Doppel-Specials (+0,5 Pkt Bonus)
    execute_query('''
        CREATE TABLE IF NOT EXISTS doubles_specials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            partner_name TEXT NOT NULL,
            opponent_team TEXT NOT NULL,
            match_date TEXT NOT NULL,
            special_type TEXT NOT NULL,
            description TEXT,
            season TEXT DEFAULT '2026/2027',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    try: execute_query("ALTER TABLE doubles_specials ADD COLUMN season TEXT DEFAULT '2026/2027'")
    except: pass
    
    # Tabelle: Doppel-Matches
    execute_query('''
        CREATE TABLE IF NOT EXISTS doubles_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            opponent TEXT NOT NULL,
            legs_won INTEGER NOT NULL,
            legs_lost INTEGER NOT NULL,
            avg_total REAL NOT NULL,
            avg_9 REAL NOT NULL,
            avg_18 REAL NOT NULL,
            scores_80 INTEGER NOT NULL,
            scores_100 INTEGER NOT NULL,
            scores_140 INTEGER NOT NULL,
            scores_180 INTEGER NOT NULL,
            high_finishes INTEGER NOT NULL,
            short_legs INTEGER NOT NULL,
            specials_count INTEGER DEFAULT 0,
            season TEXT DEFAULT '2026/2027',
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
        )
    ''')
    
    try: execute_query("ALTER TABLE doubles_matches ADD COLUMN season TEXT DEFAULT '2026/2027'")
    except: pass

    # Analytics Engine Tabellen initialisieren
    try:
        from analytics.schema import init_analytics_db
        init_analytics_db()
    except Exception as e:
        print(f"Hinweis: Analytics DB Initialisierung: {e}")

def get_players():
    return query_df("SELECT * FROM players ORDER BY team, name")

def add_player(name, team, role='player'):
    execute_query(
        "INSERT INTO players (name, team, password, must_change_password, role) VALUES (?, ?, 'lions2026', 1, ?)", 
        (name, team, role)
    )

def update_player_password(player_id, new_password, must_change=False):
    execute_query(
        "UPDATE players SET password = ?, must_change_password = ? WHERE id = ?",
        (new_password, 1 if must_change else 0, player_id)
    )

def update_player_role(player_id, new_role):
    execute_query(
        "UPDATE players SET role = ? WHERE id = ?",
        (new_role, player_id)
    )

def get_settings():
    df = query_df("SELECT win_weight, avg_weight, avg9_weight, avg18_weight, scores_weight FROM settings WHERE id = 1")
    if df.empty:
        return {'win_weight': 20.0, 'avg_weight': 20.0, 'avg9_weight': 20.0, 'avg18_weight': 20.0, 'scores_weight': 20.0}
    row = df.iloc[0]
    return {
        'win_weight': float(row['win_weight']),
        'avg_weight': float(row['avg_weight']),
        'avg9_weight': float(row['avg9_weight']),
        'avg18_weight': float(row['avg18_weight']),
        'scores_weight': float(row['scores_weight'])
    }

def update_settings(win_w, avg_w, avg9_w, avg18_w, scores_w):
    execute_query('''
        UPDATE settings 
        SET win_weight = ?, avg_weight = ?, avg9_weight = ?, avg18_weight = ?, scores_weight = ?
        WHERE id = 1
    ''', (win_w, avg_w, avg9_w, avg18_w, scores_w))

def get_available_seasons():
    """Gibt eine sortierte Liste aller verfügbaren Saisons zurück."""
    q = """
        SELECT DISTINCT season FROM matches WHERE season IS NOT NULL AND season != ''
        UNION
        SELECT DISTINCT season FROM doubles_matches WHERE season IS NOT NULL AND season != ''
        UNION
        SELECT DISTINCT season FROM doubles_specials WHERE season IS NOT NULL AND season != ''
    """
    try:
        df = query_df(q)
        seasons = sorted(df['season'].dropna().tolist(), reverse=True) if not df.empty else []
    except Exception:
        seasons = []
        
    if "2026/2027" not in seasons:
        seasons.insert(0, "2026/2027")
    return seasons

def add_match(match_data):
    execute_query('''
        INSERT INTO matches (
            player_id, match_date, opponent, legs_won, legs_lost,
            avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
            high_finishes, short_legs, specials_count, season
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        match_data['player_id'], match_data['match_date'], match_data['opponent'],
        match_data['legs_won'], match_data['legs_lost'], match_data['avg_total'],
        match_data['avg_9'], match_data['avg_18'], match_data['scores_80'],
        match_data['scores_100'], match_data['scores_140'], match_data['scores_180'],
        match_data['high_finishes'], match_data['short_legs'], match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027')
    ))

def update_match(match_id, match_data):
    execute_query('''
        UPDATE matches SET
            player_id = ?, match_date = ?, opponent = ?, legs_won = ?, legs_lost = ?,
            avg_total = ?, avg_9 = ?, avg_18 = ?, scores_80 = ?, scores_100 = ?,
            scores_140 = ?, scores_180 = ?, high_finishes = ?, short_legs = ?, specials_count = ?, season = ?
        WHERE id = ?
    ''', (
        match_data['player_id'], match_data['match_date'], match_data['opponent'],
        match_data['legs_won'], match_data['legs_lost'], match_data['avg_total'],
        match_data['avg_9'], match_data['avg_18'], match_data['scores_80'],
        match_data['scores_100'], match_data['scores_140'], match_data['scores_180'],
        match_data['high_finishes'], match_data['short_legs'], match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027'),
        match_id
    ))

def get_matches(season=None):
    if season:
        query = '''
            SELECT m.*, p.name as player_name, p.team 
            FROM matches m
            JOIN players p ON m.player_id = p.id
            WHERE m.season = ?
            ORDER BY m.match_date DESC, m.id DESC
        '''
        return query_df(query, (season,))
    else:
        query = '''
            SELECT m.*, p.name as player_name, p.team 
            FROM matches m
            JOIN players p ON m.player_id = p.id
            ORDER BY m.match_date DESC, m.id DESC
        '''
        return query_df(query)

def delete_match(match_id):
    execute_query("DELETE FROM matches WHERE id = ?", (match_id,))

def add_doubles_match(match_data):
    execute_query('''
        INSERT INTO doubles_matches (
            player1_id, player2_id, match_date, opponent, legs_won, legs_lost,
            avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
            high_finishes, short_legs, specials_count, season
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        match_data['player1_id'], match_data['player2_id'], match_data['match_date'], match_data['opponent'],
        match_data['legs_won'], match_data['legs_lost'], match_data['avg_total'],
        match_data['avg_9'], match_data['avg_18'], match_data['scores_80'],
        match_data['scores_100'], match_data['scores_140'], match_data['scores_180'],
        match_data['high_finishes'], match_data['short_legs'], match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027')
    ))

def get_doubles_matches(season=None):
    if season:
        query = '''
            SELECT m.*, p1.name as p1_name, p1.team as team, p2.name as p2_name
            FROM doubles_matches m
            JOIN players p1 ON m.player1_id = p1.id
            JOIN players p2 ON m.player2_id = p2.id
            WHERE m.season = ?
            ORDER BY m.match_date DESC, m.id DESC
        '''
        return query_df(query, (season,))
    else:
        query = '''
            SELECT m.*, p1.name as p1_name, p1.team as team, p2.name as p2_name
            FROM doubles_matches m
            JOIN players p1 ON m.player1_id = p1.id
            JOIN players p2 ON m.player2_id = p2.id
            ORDER BY m.match_date DESC, m.id DESC
        '''
        return query_df(query)

def update_doubles_match(match_id, match_data):
    execute_query('''
        UPDATE doubles_matches SET
            player1_id = ?, player2_id = ?, match_date = ?, opponent = ?,
            legs_won = ?, legs_lost = ?, avg_total = ?, avg_9 = ?, avg_18 = ?,
            scores_80 = ?, scores_100 = ?, scores_140 = ?, scores_180 = ?,
            high_finishes = ?, short_legs = ?, specials_count = ?, season = ?
        WHERE id = ?
    ''', (
        match_data['player1_id'], match_data['player2_id'], match_data['match_date'], match_data['opponent'],
        match_data['legs_won'], match_data['legs_lost'], match_data['avg_total'],
        match_data['avg_9'], match_data['avg_18'], match_data['scores_80'],
        match_data['scores_100'], match_data['scores_140'], match_data['scores_180'],
        match_data['high_finishes'], match_data['short_legs'], match_data.get('specials_count', 0),
        match_data.get('season', '2026/2027'),
        match_id
    ))

def delete_doubles_match(match_id):
    execute_query("DELETE FROM doubles_matches WHERE id = ?", (match_id,))

def add_doubles_special(player_id, partner_name, opponent_team, match_date, special_type, description="", season="2026/2027"):
    execute_query('''
        INSERT INTO doubles_specials (player_id, partner_name, opponent_team, match_date, special_type, description, season)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (player_id, partner_name, opponent_team, match_date, special_type, description, season))

def update_doubles_special(special_id, player_id, partner_name, opponent_team, match_date, special_type, description="", season="2026/2027"):
    execute_query('''
        UPDATE doubles_specials SET
            player_id = ?, partner_name = ?, opponent_team = ?, match_date = ?,
            special_type = ?, description = ?, season = ?
        WHERE id = ?
    ''', (player_id, partner_name, opponent_team, match_date, special_type, description, season, special_id))

def get_doubles_specials(season=None):
    if season:
        query = '''
            SELECT d.*, p.name as player_name, p.team
            FROM doubles_specials d
            JOIN players p ON d.player_id = p.id
            WHERE d.season = ?
            ORDER BY d.match_date DESC, d.id DESC
        '''
        return query_df(query, (season,))
    else:
        query = '''
            SELECT d.*, p.name as player_name, p.team
            FROM doubles_specials d
            JOIN players p ON d.player_id = p.id
            ORDER BY d.match_date DESC, d.id DESC
        '''
        return query_df(query)

def delete_doubles_special(special_id):
    execute_query("DELETE FROM doubles_specials WHERE id = ?", (special_id,))
