import os
import sys
import glob
from PIL import Image

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PICS_DIR = os.path.join(os.path.dirname(__file__), "..", "Spieltage_Pics", "Spieltag 2 A Team")
files = glob.glob(os.path.join(PICS_DIR, "*.png"))

print(f"Gefundene PNG-Dateien: {len(files)}")
by_type = {"numbered": [], "screenshot": []}
for f in sorted(files):
    bn = os.path.basename(f)
    if bn[0].isdigit() and not bn.startswith("Screenshot"):
        by_type["numbered"].append(bn)
    else:
        by_type["screenshot"].append(bn)

print(f"Nummerierte Dateien (z.B. 1.png - 6.png): {by_type['numbered']}")
print(f"Screenshot-Dateien: {len(by_type['screenshot'])}")
if by_type['screenshot']:
    print("Erste 5 Screenshots:", by_type['screenshot'][:5])
    print("Letzte 5 Screenshots:", by_type['screenshot'][-5:])
