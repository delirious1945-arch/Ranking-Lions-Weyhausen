import sqlite3
import psycopg2
import sys

def migrate(pg_url):
    print("Verbinde mit SQLite...")
    sqlite_conn = sqlite3.connect(r"C:\Users\sebas\Documents\Lions Weyhausen\02_Liga\Ranking_Website\dart_data.db")
    sqlite_c = sqlite_conn.cursor()
    
    print(f"Verbinde mit Supabase PostgreSQL...")
    pg_conn = psycopg2.connect(pg_url)
    pg_c = pg_conn.cursor()
    
    # 1. Tabellen in Supabase erstellen
    print("Erstelle Tabellen in Supabase...")
    pg_c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            team TEXT NOT NULL,
            password TEXT DEFAULT 'lions2026',
            must_change_password INTEGER DEFAULT 1,
            role TEXT DEFAULT 'player'
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            win_weight REAL NOT NULL,
            avg_weight REAL NOT NULL,
            avg9_weight REAL NOT NULL,
            avg18_weight REAL NOT NULL,
            scores_weight REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
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
            specials_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS doubles_specials (
            id SERIAL PRIMARY KEY,
            player_id INTEGER NOT NULL,
            partner_name TEXT NOT NULL,
            opponent_team TEXT NOT NULL,
            match_date TEXT NOT NULL,
            special_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS doubles_matches (
            id SERIAL PRIMARY KEY,
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
            specials_count INTEGER DEFAULT 0
        );
    ''')
    pg_conn.commit()
    
    # 2. Spieler übertragen
    sqlite_c.execute("SELECT id, name, team, password, must_change_password, role FROM players")
    players = sqlite_c.fetchall()
    print(f"Übertrage {len(players)} Spieler...")
    for p in players:
        pg_c.execute('''
            INSERT INTO players (id, name, team, password, must_change_password, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                team = EXCLUDED.team,
                password = EXCLUDED.password,
                must_change_password = EXCLUDED.must_change_password,
                role = EXCLUDED.role
        ''', p)
    pg_conn.commit()
    
    # Sequence für Players ID auf max setzen
    pg_c.execute("SELECT setval(pg_get_serial_sequence('players', 'id'), coalesce(max(id), 1)) FROM players;")
    pg_conn.commit()

    # 3. Settings übertragen
    sqlite_c.execute("SELECT id, win_weight, avg_weight, avg9_weight, avg18_weight, scores_weight FROM settings WHERE id = 1")
    s = sqlite_c.fetchone()
    if s:
        print("Übertrage Einstellungen...")
        pg_c.execute('''
            INSERT INTO settings (id, win_weight, avg_weight, avg9_weight, avg18_weight, scores_weight)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                win_weight = EXCLUDED.win_weight,
                avg_weight = EXCLUDED.avg_weight,
                avg9_weight = EXCLUDED.avg9_weight,
                avg18_weight = EXCLUDED.avg18_weight,
                scores_weight = EXCLUDED.scores_weight
        ''', s)
        pg_conn.commit()

    # 4. Matches übertragen
    sqlite_c.execute('''
        SELECT id, player_id, match_date, opponent, legs_won, legs_lost,
               avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
               high_finishes, short_legs, specials_count
        FROM matches
    ''')
    matches = sqlite_c.fetchall()
    print(f"Übertrage {len(matches)} Matches...")
    for m in matches:
        pg_c.execute('''
            INSERT INTO matches (id, player_id, match_date, opponent, legs_won, legs_lost,
                                avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
                                high_finishes, short_legs, specials_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', m)
    pg_conn.commit()
    if matches:
        pg_c.execute("SELECT setval(pg_get_serial_sequence('matches', 'id'), coalesce(max(id), 1)) FROM matches;")
        pg_conn.commit()

    # 5. Doppel-Specials übertragen
    sqlite_c.execute('''
        SELECT id, player_id, partner_name, opponent_team, match_date, special_type, description
        FROM doubles_specials
    ''')
    ds = sqlite_c.fetchall()
    print(f"Übertrage {len(ds)} Doppel-Specials...")
    for row in ds:
        pg_c.execute('''
            INSERT INTO doubles_specials (id, player_id, partner_name, opponent_team, match_date, special_type, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', row)
    pg_conn.commit()
    if ds:
        pg_c.execute("SELECT setval(pg_get_serial_sequence('doubles_specials', 'id'), coalesce(max(id), 1)) FROM doubles_specials;")
        pg_conn.commit()

    # 6. Doppel-Matches übertragen
    sqlite_c.execute('''
        SELECT id, player1_id, player2_id, match_date, opponent, legs_won, legs_lost,
               avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
               high_finishes, short_legs, specials_count
        FROM doubles_matches
    ''')
    dm = sqlite_c.fetchall()
    print(f"Übertrage {len(dm)} Doppel-Matches...")
    for row in dm:
        pg_c.execute('''
            INSERT INTO doubles_matches (id, player1_id, player2_id, match_date, opponent, legs_won, legs_lost,
                                        avg_total, avg_9, avg_18, scores_80, scores_100, scores_140, scores_180,
                                        high_finishes, short_legs, specials_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', row)
    pg_conn.commit()
    if dm:
        pg_c.execute("SELECT setval(pg_get_serial_sequence('doubles_matches', 'id'), coalesce(max(id), 1)) FROM doubles_matches;")
        pg_conn.commit()

    sqlite_conn.close()
    pg_conn.close()
    print("Erfolgreich: Alle Daten wurden vollständig nach Supabase migriert!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        migrate(sys.argv[1])
    else:
        print("Bitte Supabase Connection String übergeben!")
