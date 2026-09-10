"""
Abstrahierte OCR-Schnittstelle (EasyOCR mit Fallback).
"""
from typing import List, Dict, Any, Union
import numpy as np
from PIL import Image

_easyocr_reader = None

def get_ocr_reader():
    """Initialisiert den EasyOCR Reader singleton."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            # Deutsche und englische Erkennung, CPU-optimiert
            _easyocr_reader = easyocr.Reader(['de', 'en'], gpu=False)
        except Exception as e:
            print(f"Hinweis: EasyOCR Initialisierung: {e}")
            _easyocr_reader = None
    return _easyocr_reader

def extract_ocr_boxes(image: Union[Image.Image, np.ndarray]) -> List[Dict[str, Any]]:
    """
    Führt OCR auf dem Bild aus und liefert erkannte Texte, Koordinaten und Konfidenz.
    Rückgabe: [{'text': str, 'confidence': float, 'box': [[x1,y1], [x2,y2], ...]}]
    """
    reader = get_ocr_reader()
    if reader is None:
        return []
        
    if isinstance(image, Image.Image):
        img_np = np.array(image)
    else:
        img_np = image
        
    results = reader.readtext(img_np)
    extracted = []
    for box, text, conf in results:
        extracted.append({
            'text': str(text).strip(),
            'confidence': round(float(conf), 2),
            'box': box
        })
    return extracted
