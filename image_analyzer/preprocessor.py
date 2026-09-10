"""
Bildvorverarbeitung und Farbanalyse für 2K Darts Screenshots.
"""
import numpy as np
from PIL import Image

def load_image(image_path: str) -> Image.Image:
    """Lädt ein Bild über PIL."""
    return Image.open(image_path).convert('RGB')

def detect_active_tab_and_colors(image: Image.Image) -> dict:
    """
    Analysiert rote/orange Farbtöne in der oberen Tab-Leiste,
    um den aktiven Tab (z.B. Spielinfo, Statistiken, Scoreboard)
    sowie den farblich markierten Startspieler zu identifizieren.
    """
    img_np = np.array(image)
    h, w, _ = img_np.shape
    
    # Obere 25% des Bildes (Tab-Bereich)
    top_region = img_np[:int(h * 0.25), :]
    
    # Rote/Orange Pixel filtern (R > 140, G < 60, B < 60)
    red_mask = (top_region[:, :, 0] > 140) & (top_region[:, :, 1] < 60) & (top_region[:, :, 2] < 60)
    has_red_tabs = np.sum(red_mask) > 100
    
    return {
        'has_active_red_tab': bool(has_red_tabs),
        'dimensions': (w, h)
    }

def enhance_for_ocr(image: Image.Image) -> Image.Image:
    """
    Optimiert einen Screenshot für OCR auf dunklen Hintergründen:
    Invertiert Text bei Bedarf und maximiert den Kontrast der weißen Schrift.
    """
    img_np = np.array(image.convert('L'))
    # Kontrast-Spreizung
    p2, p98 = np.percentile(img_np, (2, 98))
    if p98 > p2:
        img_rescaled = np.clip((img_np - p2) / (p98 - p2) * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(img_rescaled)
    return image
