"""
Konfiguration und Liga-Stammdaten für den Datenübertragungs-Agenten
"""

KADER_A = [
    "Nicholas Stedman",
    "Dirk Ostermann",
    "Sebastian Kirste",
    "Erik Schremmer",
    "Jens Goltermann",
    "Kevin Emde"
]

KADER_B = [
    "Michael Kranz",
    "André Rathje",
    "Maik Feuerhahn",
    "Karsten Kohnert",
    "Michael Gehrt",
    "Timo Feuerhahn",
    "Karen Schulz",
    "Jannik Baier",
    "Martin Thomas",
    "Michael Jochen"
]

STAFFEL_7_OPPONENTS = [
    "Bromer Burglöwen B",
    "DC Gamsen 96 B",
    "DC Old No.7 Sülfeld D",
    "DC Wolfsjäger C",
    "Erst zart dann Dart A",
    "Riederockets MTV Vollbüttel B",
    "TSV Rethen D",
    "VfB Bullseye Fallersleben B",
    "VfL Wolfsburg e.V. F"
]

STAFFEL_11_OPPONENTS = [
    "1.DC Didderse A",
    "Aller-Oker-Darter A",
    "Dart Kongs Triangel B",
    "FireDarter C",
    "HSV Isedarter B",
    "Mad House Fallersleben E",
    "RaZa Darts A",
    "VfL Wettmershagen B"
]

# Offizielle BBDV-Blockeinteilung 4-2-4-2
MATCH_TYPES = {
    1: {"type": "single", "label": "Einzel 1", "block": 1},
    2: {"type": "single", "label": "Einzel 2", "block": 1},
    3: {"type": "single", "label": "Einzel 3", "block": 1},
    4: {"type": "single", "label": "Einzel 4", "block": 1},
    5: {"type": "double", "label": "Doppel 1", "block": 2},
    6: {"type": "double", "label": "Doppel 2", "block": 2},
    7: {"type": "single", "label": "Einzel 5", "block": 3},
    8: {"type": "single", "label": "Einzel 6", "block": 3},
    9: {"type": "single", "label": "Einzel 7", "block": 3},
    10: {"type": "single", "label": "Einzel 8", "block": 3},
    11: {"type": "double", "label": "Doppel 3", "block": 4},
    12: {"type": "double", "label": "Doppel 4", "block": 4},
}
