import os
import sys
import glob
import re
from PIL import Image
import easyocr

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PICS_DIR = os.path.join(os.path.dirname(__file__), "..", "Spieltage_Pics", "Spieltag 2 A Team")
files = sorted(glob.glob(os.path.join(PICS_DIR, "*.png")))

print(f"Initialisiere EasyOCR...")
reader = easyocr.Reader(['de', 'en'], gpu=False)

print(f"Scanne Header von {len(files)} Bildern...")
summary = []

for idx, f in enumerate(files):
    bn = os.path.basename(f)
    img = Image.open(f)
    w, h = img.size
    header_crop = img.crop((0, 0, w, min(140, h)))
    import numpy as np
    header_np = np.array(header_crop)
    res = reader.readtext(header_np)
    texts = [r[1] for r in res]
    full_h_text = " | ".join(texts)
    
    # Ermittle Match-Nummer (#1 bis #12)
    match_num = None
    m_match = re.search(r'#\s*([0-9]{1,2})', full_h_text)
    if m_match:
        match_num = int(m_match.group(1))
    elif "Spielbericht" in full_h_text or "Lions Weyhausen A" in full_h_text:
        match_num = "SPIELBERICHT_OVERVIEW"
        
    summary.append({
        "file": bn,
        "match_num": match_num,
        "header": full_h_text
    })
    if (idx + 1) % 10 == 0 or idx == len(files) - 1:
        print(f"Fortschritt: {idx + 1}/{len(files)} gescannt.")

import json
with open(os.path.join(os.path.dirname(__file__), "scanned_headers.json"), "w", encoding="utf-8") as out:
    json.dump(summary, out, indent=2, ensure_ascii=False)

print("Scan abgeschlossen. Ergebnisse in scanned_headers.json gespeichert.")
