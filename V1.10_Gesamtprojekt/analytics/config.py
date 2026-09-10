"""
Dart Analytics Engine - Konfiguration
Zentrale Schwellenwerte für alle Berechnungsmodule.
Keine hartcodierten Werte in der Engine oder im Frontend.
"""

# Score-Kategorien & Schwellenwerte
POOR_SCORE_THRESHOLD = 60          # Schlechte Aufnahme: <= 60
NORMAL_SCORE_MIN = 61              # Normale Aufnahme: 61 - 99
NORMAL_SCORE_MAX = 99
GOOD_SCORE_THRESHOLD = 100         # Gute Aufnahme: 100 - 139
GOOD_SCORE_MAX = 139
EXCELLENT_SCORE_THRESHOLD = 140    # Exzellente Aufnahme: >= 140
MAX_SCORE = 180

# Druck-Schwellenwerte (Opponent Restscore)
HIGH_PRESSURE_REST = 170           # Hoher gegnerischer Druck: <= 170
VERY_HIGH_PRESSURE_REST = 100      # Sehr hoher Druck: <= 100
MODERATE_PRESSURE_REST = 250       # Moderater Druck: 171 - 250
LOW_PRESSURE_REST = 251            # Geringer Druck: > 250

# Leg-Phasen
OPENING_VISITS = 3                 # Opening: Visits 1 bis 3
MID_GAME_START = 4                 # Mid Game: Visits 4 bis 6
MID_GAME_END = 6
FINISH_REST_THRESHOLD = 170        # Finish-Phase: Sobald Rest <= 170 erreicht wird

# Mindeststichproben für statistische Validität
MIN_SAMPLE_LOW = 10                # Unter 10 Legs: Extrem geringe Aussagekraft
MIN_SAMPLE_RESTRICTED = 50         # 10 - 49 Legs: Geringe Aussagekraft
MIN_SAMPLE_MODERATE = 100          # 50 - 99 Legs: Eingeschränkte Aussagekraft
MIN_SAMPLE_SOLID = 250             # 100 - 249 Legs: Solide Aussagekraft
# 250+ Legs: Hohe Aussagekraft

def get_sample_size_rating(legs_count: int) -> dict:
    """Gibt eine Einschätzung der statistischen Verlässlichkeit zurück."""
    if legs_count < MIN_SAMPLE_LOW:
        return {
            'level': 'Sehr gering',
            'badge': '🔴 Unzureichend',
            'desc': 'Zu wenige Daten für belastbare Aussagen (< 10 Legs).',
            'color': '#EF4444'
        }
    elif legs_count < MIN_SAMPLE_RESTRICTED:
        return {
            'level': 'Gering',
            'badge': '🟠 Geringe Aussagekraft',
            'desc': 'Erste Tendenzen erkennbar, jedoch noch volatil (10–49 Legs).',
            'color': '#F97316'
        }
    elif legs_count < MIN_SAMPLE_MODERATE:
        return {
            'level': 'Eingeschränkt',
            'badge': '🟡 Eingeschränkt',
            'desc': 'Gute Orientierungswerte (50–99 Legs).',
            'color': '#EAB308'
        }
    elif legs_count < MIN_SAMPLE_SOLID:
        return {
            'level': 'Solide',
            'badge': '🟢 Solide Basis',
            'desc': 'Statistisch aussagekräftige Datenbasis (100–249 Legs).',
            'color': '#10B981'
        }
    else:
        return {
            'level': 'Hoch',
            'badge': '💎 Hohe Verlässlichkeit',
            'desc': 'Vollständig etabliertes Profil mit hoher Signifikanz (250+ Legs).',
            'color': '#00D4FF'
        }
