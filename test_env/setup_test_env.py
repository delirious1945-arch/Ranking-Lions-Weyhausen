import os
import sys
import sqlite3

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
PROD_DB = os.path.join(ROOT_DIR, "dart_data.db")
TEST_DB = os.path.join(BASE_DIR, "test_dart_data.db")

def setup_test_database():
    os.makedirs(os.path.join(BASE_DIR, "transmission_agent"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "audit"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "audit_reports"), exist_ok=True)
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    src_conn = sqlite3.connect(PROD_DB)
    dst_conn = sqlite3.connect(TEST_DB)
    
    # 1. Erstelle alle Tabellen mit dem gleichen Schema
    cursor = src_conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    for tbl_name, create_sql in tables:
        if create_sql:
            dst_conn.execute(create_sql)
            
    # 2. Kopiere Stammdaten (Spieler & Settings)
    for tbl in ["players", "settings"]:
        try:
            cursor.execute(f"SELECT * FROM {tbl}")
            rows = cursor.fetchall()
            if rows:
                col_names = [description[0] for description in cursor.description]
                placeholders = ", ".join(["?"] * len(col_names))
                cols = ", ".join(col_names)
                dst_conn.executemany(f"INSERT INTO {tbl} ({cols}) VALUES ({placeholders})", rows)
        except Exception as e:
            print(f"Hinweis beim Kopieren von {tbl}: {e}")
            
    dst_conn.commit()
    
    # Prüfe Ergebnis
    dst_cursor = dst_conn.cursor()
    dst_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    created_tables = [r[0] for r in dst_cursor.fetchall()]
    
    player_count = dst_cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    
    print(f"✅ Test-Datenbank erfolgreich aufgesetzt: {len(created_tables)} Tabellen vorhanden.")
    print(f"✅ Stammdaten geklont: {player_count} Spieler in 'test_dart_data.db'.")
    
    src_conn.close()
    dst_conn.close()

if __name__ == "__main__":
    setup_test_database()
