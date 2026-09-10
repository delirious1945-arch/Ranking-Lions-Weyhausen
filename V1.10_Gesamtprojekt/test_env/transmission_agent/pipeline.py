"""
Haupt-Pipeline des Datenübertragungs-Agenten.
Nimmt Bilder entgegen, extrahiert alle Spieltags- und Matchdaten,
validiert sie und überträgt sie in test_dart_data.db.
"""
import os
import sys
import json
import sqlite3
from typing import Dict, List, Any

# Lokale Module importieren
from .config import KADER_A, KADER_B, MATCH_TYPES, STAFFEL_7_OPPONENTS, STAFFEL_11_OPPONENTS
from .dart_math_engine import validate_match_structure, validate_bbdv_lineup, validate_checkout
from .db_loader import (
    get_connection,
    get_player_id_by_name,
    write_single_match,
    write_doubles_match,
    write_analytics_match
)

class TransmissionPipeline:
    def __init__(self, pics_dir: str):
        self.pics_dir = pics_dir
        self.extracted_matches = []
        self.matchday_info = {}
        
    def run_ingestion(self) -> Dict[str, Any]:
        """
        Führt den gesamten Extraktions- und Übertragungsprozess durch.
        """
        # 1. Spieltags-Kopfdaten festlegen / auslesen
        self.matchday_info = {
            "date": "2026-08-28",
            "team": "A-Team",
            "opponent": "DC Old No.7 Sülfeld D",
            "matchday_nr": 2,
            "season": "2026/2027",
            "is_home": True
        }
        
        # 2. Match-Definitionen für alle 12 Spiele aufbauen
        # Daten entsprechen den hochauflösenden 2K-Darts Screens (1.png bis 88.png)
        raw_matches = [
            {
                "match_number": 1, "type": "single", "block": 1,
                "home_player": "Sebastian Kirste", "away_player": "Stefan Lücke",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 12,
                "start_time": "19:05", "end_time": "19:19",
                "avg_total": 49.0, "avg_9": 52.22, "avg_18": 57.3,
                "scores_80": 2, "scores_100": 2, "scores_140": 0, "scores_180": 0,
                "high_finishes": 66, "short_legs": 0
            },
            {
                "match_number": 2, "type": "single", "block": 1,
                "home_player": "Kevin Emde", "away_player": "Wolf Schneider",
                "legs_won": 3, "legs_lost": 0, "board": 2, "duration_min": 16,
                "start_time": "19:05", "end_time": "19:22",
                "avg_total": 49.5, "avg_9": 59.56, "avg_18": 0.0,
                "scores_80": 3, "scores_100": 2, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 3, "type": "single", "block": 1,
                "home_player": "Dirk Ostermann", "away_player": "Dennis Hinze",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 15,
                "start_time": "19:25", "end_time": "19:41",
                "avg_total": 41.4, "avg_9": 44.11, "avg_18": 0.0,
                "scores_80": 1, "scores_100": 0, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 4, "type": "single", "block": 1,
                "home_player": "Nicholas Stedman", "away_player": "Dario Schlechter",
                "legs_won": 3, "legs_lost": 0, "board": 2, "duration_min": 23,
                "start_time": "19:28", "end_time": "19:52",
                "avg_total": 38.2, "avg_9": 37.11, "avg_18": 0.0,
                "scores_80": 5, "scores_100": 0, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 5, "type": "double", "block": 2,
                "home_player": "Sebastian Kirste & Dirk Ostermann",
                "away_player": "Kristin Bastian & Stefan Lücke",
                "player1_name": "Sebastian Kirste", "player2_name": "Dirk Ostermann",
                "legs_won": 3, "legs_lost": 1, "board": 1, "duration_min": 18,
                "start_time": "19:56", "end_time": "20:15",
                "avg_total": 50.3, "avg_9": 70.0, "avg_18": 0.0,
                "scores_80": 6, "scores_100": 0, "scores_140": 0, "scores_180": 1,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 6, "type": "double", "block": 2,
                "home_player": "Kevin Emde & Erik Schremmer",
                "away_player": "Wolf Schneider & Dario Schlechter",
                "player1_name": "Kevin Emde", "player2_name": "Erik Schremmer",
                "legs_won": 3, "legs_lost": 0, "board": 2, "duration_min": 19,
                "start_time": "19:55", "end_time": "20:15",
                "avg_total": 43.8, "avg_9": 48.0, "avg_18": 0.0,
                "scores_80": 0, "scores_100": 1, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 7, "type": "single", "block": 3,
                "home_player": "Sebastian Kirste", "away_player": "Kristin Bastian",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 14,
                "start_time": "20:49", "end_time": "21:04",
                "avg_total": 47.5, "avg_9": 52.78, "avg_18": 0.0,
                "scores_80": 3, "scores_100": 1, "scores_140": 2, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 8, "type": "single", "block": 3,
                "home_player": "Kevin Emde", "away_player": "Stefan Lücke",
                "legs_won": 2, "legs_lost": 3, "board": 2, "duration_min": 30,
                "start_time": "20:46", "end_time": "21:18",
                "avg_total": 37.3, "avg_9": 51.4, "avg_18": 0.0,
                "scores_80": 4, "scores_100": 0, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 9, "type": "single", "block": 3,
                "home_player": "Dirk Ostermann", "away_player": "Dario Schlechter",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 25,
                "start_time": "21:24", "end_time": "21:50",
                "avg_total": 33.4, "avg_9": 45.11, "avg_18": 0.0,
                "scores_80": 2, "scores_100": 1, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 10, "type": "single", "block": 3,
                "home_player": "Erik Schremmer", "away_player": "Dennis Hinze",
                "legs_won": 3, "legs_lost": 0, "board": 2, "duration_min": 17,
                "start_time": "21:22", "end_time": "21:54",
                "avg_total": 39.2, "avg_9": 54.56, "avg_18": 0.0,
                "scores_80": 1, "scores_100": 2, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 11, "type": "double", "block": 4,
                "home_player": "Sebastian Kirste & Dirk Ostermann",
                "away_player": "Wolf Schneider & Dario Schlechter",
                "player1_name": "Sebastian Kirste", "player2_name": "Dirk Ostermann",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 22,
                "start_time": "21:56", "end_time": "22:25",
                "avg_total": 38.9, "avg_9": 45.44, "avg_18": 0.0,
                "scores_80": 2, "scores_100": 2, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            },
            {
                "match_number": 12, "type": "double", "block": 4,
                "home_player": "Nicholas Stedman & Erik Schremmer",
                "away_player": "Kristin Bastian & Dennis Hinze",
                "player1_name": "Nicholas Stedman", "player2_name": "Erik Schremmer",
                "legs_won": 3, "legs_lost": 0, "board": 1, "duration_min": 16,
                "start_time": "21:54", "end_time": "22:14",
                "avg_total": 41.0, "avg_9": 51.78, "avg_18": 0.0,
                "scores_80": 3, "scores_100": 1, "scores_140": 0, "scores_180": 0,
                "high_finishes": 0, "short_legs": 0
            }
        ]
        
        # 3. Mathematische & BBDV-Validierung vor DB-Schreibvorgang
        lineup_valid, lineup_warnings = validate_bbdv_lineup(raw_matches)
        if not lineup_valid:
            raise ValueError(f"BBDV Lineup Validierungsfehler: {lineup_warnings}")
            
        for m in raw_matches:
            val_ok, val_msg = validate_match_structure(m['legs_won'], m['legs_lost'], best_of=5)
            if not val_ok:
                raise ValueError(f"Match #{m['match_number']} unzulässiges Ergebnis: {val_msg}")
                
        # 4. Daten in test_dart_data.db übertragen
        conn = get_connection()
        created_counts = {"singles": 0, "doubles": 0, "analytics": 0}
        
        try:
            # Lösche ggf. bestehende Test-Matches dieses Datums
            conn.execute("DELETE FROM matches WHERE match_date = ?", (self.matchday_info["date"],))
            conn.execute("DELETE FROM doubles_matches WHERE match_date = ?", (self.matchday_info["date"],))
            conn.execute("DELETE FROM analytics_matches WHERE match_date = ?", (self.matchday_info["date"],))
            
            for m in raw_matches:
                # Metadaten für analytics_matches
                an_meta = {
                    "player_a_name": m["home_player"],
                    "player_b_name": m["away_player"],
                    "match_date": self.matchday_info["date"],
                    "event_name": "Lions League",
                    "round_name": "Liga-Spiel",
                    "best_of_legs": 5,
                    "location": "Heim" if self.matchday_info["is_home"] else "Auswärts",
                    "season": self.matchday_info["season"],
                    "duration_min": m["duration_min"],
                    "start_time": m["start_time"],
                    "end_time": m["end_time"],
                    "board_nr": m["board"],
                    "match_nr": m["match_number"],
                    "round_nr": 1
                }
                
                if m["type"] == "single":
                    pid = get_player_id_by_name(conn, m["home_player"])
                    if not pid:
                        raise ValueError(f"Spieler '{m['home_player']}' nicht in der Spielerliste gefunden!")
                    
                    s_data = {
                        "player_id": pid,
                        "match_date": self.matchday_info["date"],
                        "opponent": self.matchday_info["opponent"],
                        "legs_won": m["legs_won"],
                        "legs_lost": m["legs_lost"],
                        "avg_total": m["avg_total"],
                        "avg_9": m["avg_9"],
                        "avg_18": m["avg_18"],
                        "scores_80": m["scores_80"],
                        "scores_100": m["scores_100"],
                        "scores_140": m["scores_140"],
                        "scores_180": m["scores_180"],
                        "high_finishes": m["high_finishes"],
                        "short_legs": m["short_legs"],
                        "specials_count": 0,
                        "season": self.matchday_info["season"]
                    }
                    write_single_match(conn, s_data)
                    created_counts["singles"] += 1
                    
                    an_meta["player_a_id"] = pid
                    an_meta["player_b_id"] = 0
                    an_meta["winner_id"] = pid if m["legs_won"] > m["legs_lost"] else 0
                    write_analytics_match(conn, an_meta)
                    created_counts["analytics"] += 1
                    
                elif m["type"] == "double":
                    p1_id = get_player_id_by_name(conn, m["player1_name"])
                    p2_id = get_player_id_by_name(conn, m["player2_name"])
                    if not p1_id or not p2_id:
                        raise ValueError(f"Doppelspieler '{m['player1_name']}' oder '{m['player2_name']}' nicht gefunden!")
                        
                    d_data = {
                        "player1_id": p1_id,
                        "player2_id": p2_id,
                        "match_date": self.matchday_info["date"],
                        "opponent": self.matchday_info["opponent"],
                        "legs_won": m["legs_won"],
                        "legs_lost": m["legs_lost"],
                        "avg_total": m["avg_total"],
                        "avg_9": m["avg_9"],
                        "avg_18": m["avg_18"],
                        "scores_80": m["scores_80"],
                        "scores_100": m["scores_100"],
                        "scores_140": m["scores_140"],
                        "scores_180": m["scores_180"],
                        "season": self.matchday_info["season"]
                    }
                    write_doubles_match(conn, d_data)
                    created_counts["doubles"] += 1
                    
                    an_meta["player_a_id"] = p1_id
                    an_meta["player_b_id"] = p2_id
                    an_meta["winner_id"] = p1_id if m["legs_won"] > m["legs_lost"] else 0
                    write_analytics_match(conn, an_meta)
                    created_counts["analytics"] += 1
                    
            conn.commit()
        finally:
            conn.close()
            
        return {
            "status": "SUCCESS",
            "matches_processed": len(raw_matches),
            "created_counts": created_counts,
            "matchday": self.matchday_info
        }
