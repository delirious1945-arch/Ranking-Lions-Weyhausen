import os
import sys
import pandas as pd
import json

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

GT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", 
    "Dart_Match_Image_Analyzer", "output", "spieltage", 
    "28-08-2026_Lions-A_SP02_vs_DC-Old-No-7-Sülfeld-D"
)

matches_csv = os.path.join(GT_DIR, "28-08-2026_Lions-A_SP02_vs_DC-Old-No-7-Sülfeld-D_matches.csv")
stats_csv = os.path.join(GT_DIR, "28-08-2026_Lions-A_SP02_vs_DC-Old-No-7-Sülfeld-D_statistics.csv")
legs_csv = os.path.join(GT_DIR, "28-08-2026_Lions-A_SP02_vs_DC-Old-No-7-Sülfeld-D_legs.csv")
info_json = os.path.join(GT_DIR, "28-08-2026_Lions-A_SP02_vs_DC-Old-No-7-Sülfeld-D_spieltag_info.json")

df_matches = pd.read_csv(matches_csv, sep=";")
df_stats = pd.read_csv(stats_csv, sep=";")
df_legs = pd.read_csv(legs_csv, sep=";")
with open(info_json, "r", encoding="utf-8") as f:
    info = json.load(f)

print("=== GROUND TRUTH REFERENZDATEN ===")
print("Spieltag:", info)
print(f"Matches ({len(df_matches)}):")
for idx, r in df_matches.iterrows():
    print(f"  Match {r['match_number']}: {r['home_player']} vs {r['away_player']} -> {r['result_str']} (Board {r['board']}, {r['start_datetime']} - {r['end_datetime']})")

print(f"\nStats ({len(df_stats)} Zeilen):")
print(df_stats[['match_id', 'player', 'overall_average', 'first_9_avg', 'scoring_80_plus', 'scoring_100_plus', 'scoring_140_plus', 'scoring_180']].head(6))
