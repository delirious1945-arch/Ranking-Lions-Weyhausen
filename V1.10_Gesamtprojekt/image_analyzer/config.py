"""
Konfiguration und Konstanten für den Dart Match Image Analyzer.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "Spieltage_Pics", "Spieltag 2 A Team")
DEFAULT_OUTPUT_CSV_DIR = os.path.join(os.path.dirname(BASE_DIR), "output", "csv")
DEFAULT_OUTPUT_JSON_DIR = os.path.join(os.path.dirname(BASE_DIR), "output", "json")

# Farb-Schwellenwerte für UI-Erkennung (2K / 3K Darts)
# Rot/Orange für aktiven Tab (z.B. aktives Leg, Startspieler-Markierung)
ACTIVE_TAB_COLOR_RGB = (180, 20, 20)
ACTIVE_TAB_TOLERANCE = 50

# Schwellenwerte für OCR-Konfidenz
CONFIDENCE_THRESHOLD_HIGH = 0.90      # Grün: 90%+
CONFIDENCE_THRESHOLD_MEDIUM = 0.70    # Gelb: 70% - 89%
# Unter 70%: Rot / Prüfen

# Standard Dart Spielmodus & Startscore
DEFAULT_START_SCORE = 501
DEFAULT_MODE = "501 (Double Out)"
