import sys
import os

# Füge das aktuelle Verzeichnis zum Pfad hinzu, um database.py zu importieren
sys.path.append(os.path.dirname(__file__))
from database import add_player, init_db

def seed_players():
    init_db()
    
    players_a = [
        "Nicholas Stedman", "Dirk Ostermann", "Sebastian Kirste",
        "Erik Schremmer", "Jens Goltermann", "Kevin Emde"
    ]

    players_b = [
        "Michael Kranz", "André Rathje", "Maik Feuerhahn",
        "Karsten Kohnert", "Michael Gehrt", "Timo Feuerhahn",
        "Karen Schulz", "Jannik Baier", "Martin Thomas", "Michael Jochen"
    ]

    count = 0
    for p in players_a:
        if add_player(p, "A-Team"): count += 1

    for p in players_b:
        if add_player(p, "B-Team"): count += 1

    print(f"Erfolgreich {count} Spieler in die Datenbank eingetragen.")

if __name__ == "__main__":
    seed_players()
