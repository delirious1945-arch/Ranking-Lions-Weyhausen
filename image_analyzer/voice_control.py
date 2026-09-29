"""
Voice Control & Speech-to-Text Parser für den Dart Match Analyzer.
Erlaubt das Vorlesen von Spieldaten (wer gegen wen, Dauer, Startzeit, Endzeit, Legs, Board etc.)
sowie das separate Vorlesen von Leg-Scores (Aufnahmen für Heim und Gast, Darts, Starter)
und füllt automatisch die entsprechenden Felder und Spalten.
"""
import io
import re
import wave
import datetime
import threading
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Optionale Imports für Audio & Spracherkennung
try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


# Bekannte Spitznamen & Vornamen für zuverlässiges Kader-Matching (inkl. phonetischer Varianten)
NICKNAMES_MAP = {
    # A-Team
    "nicolas steadman": "Nicholas Stedman",
    "nicholas steadman": "Nicholas Stedman",
    "nicolas stedman": "Nicholas Stedman",
    "nicholas stedman": "Nicholas Stedman",
    "nicolas": "Nicholas Stedman",
    "nicholas": "Nicholas Stedman",
    "nikolas": "Nicholas Stedman",
    "niklas": "Nicholas Stedman",
    "nick": "Nicholas Stedman",
    "nicki": "Nicholas Stedman",
    "stedman": "Nicholas Stedman",
    "steadman": "Nicholas Stedman",
    "deadman": "Nicholas Stedman",
    "nicholas deadman": "Nicholas Stedman",
    "nicolas deadman": "Nicholas Stedman",
    
    "sebastian kirste": "Sebastian Kirste",
    "sebastian": "Sebastian Kirste",
    "basti": "Sebastian Kirste",
    "kirste": "Sebastian Kirste",
    
    "dirk ostermann": "Dirk Ostermann",
    "dirk": "Dirk Ostermann",
    "ostermann": "Dirk Ostermann",
    
    "erik schremmer": "Erik Schremmer",
    "erik": "Erik Schremmer",
    "eric": "Erik Schremmer",
    "schremmer": "Erik Schremmer",
    
    "jens goltermann": "Jens Goltermann",
    "jens": "Jens Goltermann",
    "goltermann": "Jens Goltermann",
    
    "kevin emde": "Kevin Emde",
    "kevin": "Kevin Emde",
    "emde": "Kevin Emde",
    
    # B-Team
    "michael kranz": "Michael Kranz",
    "kranz": "Michael Kranz",
    "andre rathje": "André Rathje",
    "andré rathje": "André Rathje",
    "andre": "André Rathje",
    "andré": "André Rathje",
    "rathje": "André Rathje",
    "maik feuerhahn": "Maik Feuerhahn",
    "maik": "Maik Feuerhahn",
    "mike": "Maik Feuerhahn",
    "karsten kohnert": "Karsten Kohnert",
    "karsten": "Karsten Kohnert",
    "kohnert": "Karsten Kohnert",
    "michael gehrt": "Michael Gehrt",
    "gehrt": "Michael Gehrt",
    "timo feuerhahn": "Timo Feuerhahn",
    "timo": "Timo Feuerhahn",
    "karen schulz": "Karen Schulz",
    "karen": "Karen Schulz",
    "jannik baier": "Jannik Baier",
    "baier": "Jannik Baier",
    "martin thomas": "Martin Thomas",
    "michael jochen": "Michael Jochen",
    "jochen": "Michael Jochen"
}

CONNECTORS_AND_FILLERS = set([
    "gegen", "vs", "versus", "und", "mit", "von", "auf", "der", "die", "das", "den", "dem",
    "ein", "eine", "einer", "eines", "einem", "einen", "für", "im", "in", "am", "an", "beans", "heute"
])

NAME_BOUNDARY_WORDS = set([
    "spielte", "spielt", "spielen", "gespielt", "hat", "hatte", "haben", "waren", "war", "ist", "sind",
    "vs", "versus", "gegen", "und", "danach", "anschließend", "mit",
    "legs", "leg", "lex", "lecks", "lags", "lacks", "leks", "läx", "modus", "best", "of", "spiele", "spiel",
    "start", "startete", "startzeit", "beginn", "begann", "von", "ab",
    "ende", "endete", "endzeit", "bis",
    "dauer", "dauerte", "spieldauer", "minuten", "minute", "min", "minutenzahl", "zahl", "anzahl", "zahlen",
    "average", "avg", "gesamt-average", "gesamt", "schnitt",
    "board", "scheibe", "uhr", "um", "punkte", "punkt", "stand", "ergebnis",
    "gast", "gastspieler", "gastgegner", "heim", "heimspieler", "heimgegner", "gegner",
    "es", "wurden", "wurde", "wird", "informiert", "das", "der", "die", "den", "dem", "ein", "eine",
    "wegen", "beans", "heute"
])

def find_lions_player_in_text(text: str) -> Optional[str]:
    clean_t = text.lower()
    for k in sorted(NICKNAMES_MAP.keys(), key=len, reverse=True):
        if re.search(rf'\b{re.escape(k)}\b', clean_t):
            return NICKNAMES_MAP[k]
    return None

def clean_bounded_name(text: str, max_words: int = 3) -> str:
    """Extrahiert einen sauberen Spielernamen (1-3 Wörter), bricht bei Stoppwörtern, Zahlen und Zeiten ab."""
    if not text:
        return ""
    tokens = re.split(r'[\s,;:!/\(\)\[\]\.-]+', text.strip())
    start_idx = 0
    while start_idx < len(tokens):
        w = tokens[start_idx].lower().strip()
        if w in CONNECTORS_AND_FILLERS or not w:
            start_idx += 1
        else:
            break

    name_parts = []
    for tok in tokens[start_idx:]:
        tl = tok.lower().strip()
        if not tl:
            continue
        if tl in NAME_BOUNDARY_WORDS:
            break
        if re.match(r'^\d+(\.\d+)?$', tl) or re.match(r'^\d{1,2}:\d{2}$', tl):
            break
        name_parts.append(tok.strip().title())
        if len(name_parts) >= max_words:
            break
    return " ".join(name_parts).strip()

# Deutsche Zahlwörter für Einheiten und Zehner
UNITS_GERMAN = {
    "null": 0, "eins": 1, "ein": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5,
    "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "sechzehn": 16, "siebzehn": 17,
    "achtzehn": 18, "neunzehn": 19
}

TENS_GERMAN = {
    "zwanzig": 20, "dreißig": 30, "vierzig": 40, "fünfzig": 50,
    "sechzig": 60, "siebzig": 70, "achtzig": 80, "neunzig": 90
}

# Deutsche Zahlwörter für Zeit-, Leg- & Mengenangaben
GERMAN_NUMBER_WORDS = {
    "null": 0, "eins": 1, "ein": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5,
    "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "sechzehn": 16, "siebzehn": 17,
    "achtzehn": 18, "neunzehn": 19, "zwanzig": 20, "einundzwanzig": 21, "zweiundzwanzig": 22,
    "dreiundzwanzig": 23, "vierundzwanzig": 24, "fünfundzwanzig": 25, "sechsundzwanzig": 26,
    "siebenundzwanzig": 27, "achtundzwanzig": 28, "neunundzwanzig": 29, "dreißig": 30,
    "fünfunddreißig": 35, "vierzig": 40, "fünfundvierzig": 45, "fünfzig": 50, "sechzig": 60,
    "siebzig": 70, "achtzig": 80, "neunzig": 90, "hundert": 100
}


def parse_german_number_word(word: str) -> int:
    """Konvertiert ein deutsches Zahlwort von 0 bis 180 in eine Ganzzahl, oder -1 falls kein Zahlwort."""
    w = word.lower().strip(" ,;:.!?")
    if not w:
        return -1
    if re.match(r'^\d+$', w):
        return int(w)
    if w in UNITS_GERMAN:
        return UNITS_GERMAN[w]
    if w in TENS_GERMAN:
        return TENS_GERMAN[w]
    if w in ["hundert", "einhundert"]:
        return 100

    # z. B. "achtundsechzig", "einundzwanzig", "fünfundachtzig"
    m_und = re.match(r'^(ein|zwei|drei|vier|fünf|sechs|sieben|acht|neun)und(zwanzig|dreißig|vierzig|fünfzig|sechzig|siebzig|achtzig|neunzig)$', w)
    if m_und:
        unit_val = UNITS_GERMAN[m_und.group(1)]
        ten_val = TENS_GERMAN[m_und.group(2)]
        return ten_val + unit_val

    # z. B. "einhundert..." oder "hundert..." (z. B. "hundertvierzig", "einhundertachtzig", "hundertachtundsechzig")
    m_h = re.match(r'^(?:ein)?hundert(.*)$', w)
    if m_h:
        rest = m_h.group(1).strip()
        if not rest:
            return 100
        rest_val = parse_german_number_word(rest)
        if rest_val != -1:
            return 100 + rest_val

    return -1


def detect_speech_segments(
    audio_np: np.ndarray,
    sample_rate: int = 16000,
    chunk_ms: int = 100,
    min_silence_ms: int = 450,
    padding_ms: int = 250
) -> List[np.ndarray]:
    """
    Unterteilt ein Audio-Signal anhand von Sprechpausen (Stille >= min_silence_ms)
    in separate Audio-Segmente.
    Erkennt gezielte Pausen zwischen einzelnen Zahlen (z. B. 100 [Pause] 68) zuverlässig.
    Nutzt adaptive Schwellenwertbestimmung mit harter Unter- und Obergrenze (20.0 bis 50.0 RMS)
    und 250ms Padding, um Abschneiden von Wortanfängen/-enden sicher zu verhindern.
    """
    chunk_samples = int(sample_rate * (chunk_ms / 1000.0))
    padding_samples = int(sample_rate * (padding_ms / 1000.0))
    min_silence_chunks = max(2, int(min_silence_ms / chunk_ms))
    
    audio_np = np.asarray(audio_np).flatten()
    total_samples = len(audio_np)
    if total_samples < chunk_samples:
        return [audio_np]

    num_chunks = total_samples // chunk_samples
    chunk_rms = []
    for i in range(num_chunks):
        c = audio_np[i * chunk_samples : (i + 1) * chunk_samples].astype(float)
        rms = np.sqrt(np.mean(np.square(c)))
        chunk_rms.append(rms)

    sorted_rms = sorted(chunk_rms)
    p10_idx = max(1, int(len(sorted_rms) * 0.10))
    ambient_noise = np.mean(sorted_rms[:p10_idx])
    thresh = min(max(20.0, ambient_noise * 1.6), 50.0)

    is_speech = [r >= thresh for r in chunk_rms]

    segments_idx: List[Tuple[int, int]] = []
    in_speech = False
    speech_start_chunk = 0
    silence_count = 0

    for i, speech in enumerate(is_speech):
        if speech:
            if not in_speech:
                in_speech = True
                speech_start_chunk = i
            silence_count = 0
        else:
            if in_speech:
                silence_count += 1
                if silence_count >= min_silence_chunks:
                    speech_end_chunk = i - silence_count + 1
                    segments_idx.append((speech_start_chunk, speech_end_chunk))
                    in_speech = False
                    silence_count = 0

    if in_speech:
        speech_end_chunk = num_chunks
        segments_idx.append((speech_start_chunk, speech_end_chunk))

    if not segments_idx:
        return [audio_np]

    audio_segments = []
    for s_chunk, e_chunk in segments_idx:
        start_samp = max(0, s_chunk * chunk_samples - padding_samples)
        end_samp = min(total_samples, e_chunk * chunk_samples + padding_samples)
        seg = audio_np[start_samp:end_samp]
        if len(seg) >= int(sample_rate * 0.15):  # mind. 150ms
            audio_segments.append(seg)

    return audio_segments if audio_segments else [audio_np]


def is_voice_available() -> Tuple[bool, str]:
    """Prüft, ob alle Voraussetzungen für Sprachaufnahmen vorhanden sind."""
    if sd is None:
        return False, "sounddevice ist nicht installiert."
    if sr is None:
        return False, "SpeechRecognition ist nicht installiert."
    try:
        devices = sd.query_devices()
        input_devs = [d for d in devices if d.get('max_input_channels', 0) > 0]
        if not input_devs:
            return False, "Kein funktionierendes Mikrofon gefunden."
    except Exception as e:
        return False, f"Audio-Geräte-Fehler: {e}"
    return True, "Sprachsteuerung bereit"


def record_and_transcribe(
    max_duration_sec: float = 300.0,
    sample_rate: int = 16000,
    stop_event: Optional[threading.Event] = None,
    on_status: Optional[callable] = None,
    on_timer: Optional[callable] = None,
    device: Optional[int] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Nimmt Audio vom Standard-Mikrofon auf (bis zu max_duration_sec, default 5 Minuten = 300s)
    und transkribiert es via Google Speech (de-DE).
    Erkennt Sprechpausen (z. B. zwischen 100 und 68) und transkribiert die Segmente getrennt,
    sodass Pausen einzelne Zahlen trennen und nicht zu einer Gesamtzahl (z. B. 168) verschmelzen.
    Kann vorzeitig über stop_event beendet werden.
    Gibt (transkribierter_text, fehlermeldung) zurück.
    """
    ok, err_msg = is_voice_available()
    if not ok:
        return None, err_msg

    if on_status:
        on_status("🎙️ Höre zu... Bitte sprechen...")

    try:
        frames = []
        chunk_size = int(sample_rate * 0.1)  # 100ms Chunks

        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', blocksize=chunk_size, device=device) as stream:
            elapsed = 0.0
            step = 0.1
            while elapsed < max_duration_sec:
                if stop_event and stop_event.is_set():
                    break
                data, overflowed = stream.read(chunk_size)
                frames.append(data.copy())
                elapsed += step
                if on_timer and int(elapsed * 10) % 5 == 0:  # Alle 0.5s Timer-Update
                    on_timer(elapsed)

        if not frames:
            return None, "Keine Audiodaten aufgezeichnet."

        if on_status:
            on_status("⏳ Analysiere Sprechpausen und wandle Sprache in Text um...")

        audio_np = np.concatenate(frames, axis=0).flatten()

        # Prüfen, ob überhaupt Lautstärke/Signal vorhanden war
        volume_rms = np.sqrt(np.mean(np.square(audio_np.astype(float))))
        if volume_rms < 15:  # Nahezu absolute Stille
            return None, "Keine Stimme erkannt (zu leise oder Mikrofon stumm)."

        recognizer = sr.Recognizer()

        def _transcribe_seg(seg_bytes: bytes) -> Optional[str]:
            try:
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(seg_bytes)
                wav_io.seek(0)
                with sr.AudioFile(wav_io) as source:
                    audio_data = recognizer.record(source)
                txt = recognizer.recognize_google(audio_data, language="de-DE")
                return txt.strip() if txt else None
            except Exception:
                return None

        # Pausenerkennung: In separate Sprachsegmente zerlegen
        audio_segments = detect_speech_segments(audio_np, sample_rate=sample_rate, min_silence_ms=450)

        # Vollständige Aufnahme als primäres Sicherheitsnetz bereithalten
        full_audio_text = _transcribe_seg(audio_np.tobytes())

        if len(audio_segments) > 1:
            # Segmente sequentiell transkribieren (verhindert API-Rate-Limits und Socket-Resets)
            raw_results = []
            for s in audio_segments:
                raw_results.append(_transcribe_seg(s.tobytes()))

            # Automatische Nachbar-Kontext-Reparatur für einzelne nicht verstandene Segmente (z. B. isoliertes "null")
            for i in range(len(raw_results)):
                if raw_results[i] is None:
                    repaired = None
                    if i > 0 and raw_results[i - 1]:
                        ctx_audio = np.concatenate([
                            audio_segments[i - 1].flatten(),
                            np.zeros(int(sample_rate * 0.15), dtype=np.int16),
                            audio_segments[i].flatten()
                        ])
                        ctx_txt = _transcribe_seg(ctx_audio.tobytes())
                        if ctx_txt:
                            words = ctx_txt.split()
                            if len(words) >= 2:
                                repaired = words[-1]
                    if not repaired and i < len(audio_segments) - 1:
                        ctx_audio = np.concatenate([
                            audio_segments[i].flatten(),
                            np.zeros(int(sample_rate * 0.15), dtype=np.int16),
                            audio_segments[i + 1].flatten()
                        ])
                        ctx_txt = _transcribe_seg(ctx_audio.tobytes())
                        if ctx_txt:
                            words = ctx_txt.split()
                            if len(words) >= 2:
                                repaired = words[0]
                    if repaired:
                        raw_results[i] = repaired

            valid_results = [r for r in raw_results if r]

            # Zahlwörter pro Segment normalisieren
            seg_parts = []
            for item in valid_results:
                num_val = parse_german_number_word(item)
                if num_val != -1:
                    seg_parts.append(str(num_val))
                else:
                    seg_parts.append(item)

            # Sicherheitsabgleich: Falls Segmente fehlgeschlagen sind (None)
            # und die Gesamtaufnahme mehr verwertbare Zahlen/Wörter enthält,
            # nutzen wir das Gesamtergebnis, damit garantiert keine Zahl fehlt.
            if full_audio_text:
                full_nums = re.findall(r'\b\d+\b', full_audio_text)
                seg_nums = re.findall(r'\b\d+\b', " ".join(seg_parts))
                if any(r is None for r in raw_results) and len(full_nums) > len(seg_nums):
                    return full_audio_text, None

            if seg_parts:
                return ", ".join(seg_parts), None
            elif full_audio_text:
                return full_audio_text, None
            return None, "Sprache konnte nicht verstanden werden. Bitte noch einmal deutlich sprechen."

        else:
            # Nur ein zusammenhängendes Segment
            if full_audio_text:
                return full_audio_text, None
            text = _transcribe_seg(audio_np.tobytes())
            if not text:
                return None, "Sprache konnte nicht verstanden werden. Bitte noch einmal deutlich sprechen."
            return text.strip(), None

    except sr.UnknownValueError:
        return None, "Sprache konnte nicht verstanden werden. Bitte noch einmal deutlich sprechen."
    except sr.RequestError as e:
        return None, f"Verbindungsfehler zur Spracherkennung: {e}"
    except Exception as e:
        return None, f"Fehler bei der Aufnahme: {e}"


def _normalize_text(text: str) -> str:
    """Normalisiert deutsche Zahlwörter und typische Sprach-Muster."""
    t = text.lower()
    t = t.replace(" - ", " bis ").replace("–", " bis ")
    
    # "20 uhr 15" -> "20:15"
    t = re.sub(r'(\b\d{1,2})\s*uhr\s*(\d{1,2})\b', r'\1:\2', t)
    # "20 uhr" -> "20:00"
    t = re.sub(r'(\b\d{1,2})\s*uhr\b', r'\1:00', t)
    
    # Deutsche Zahlwörter ersetzen
    for word, num in GERMAN_NUMBER_WORDS.items():
        t = re.sub(rf'\b{word}\b', str(num), t)

    return t


def match_player_name(query: str, kader: List[str]) -> Optional[str]:
    """Sucht einen Spielernamen im Kader (Vollname, Vorname, Nachname, Spitzname)."""
    if not query:
        return None
    clean_q = query.strip().lower()
    
    # 1. Spitznamen-Lookup
    if clean_q in NICKNAMES_MAP:
        target = NICKNAMES_MAP[clean_q]
        if target in kader or not kader:
            return target

    # 2. Exakter Match im Kader
    for p in kader:
        if p.lower() == clean_q:
            return p

    # 3. Vorname / Nachname Match
    for p in kader:
        parts = p.lower().split()
        if any(part == clean_q for part in parts):
            return p
            
    # 4. Teilstring Match
    for p in kader:
        if clean_q in p.lower() or p.lower() in clean_q:
            return p

    return None


def parse_match_speech(text: str, kader: Optional[List[str]] = None, is_home_match: bool = True) -> Dict[str, Any]:
    """
    Chronologische & Keyword-gestützte Erkennung der 8 Felder:
    1. Heimspieler
    2. Name des Gastspielers
    3. Gespielte Legs
    4. Startzeit
    5. Endzeit
    6. Minutenzahl (Dauer)
    7. Gesamt-Average Heim
    8. Gesamt-Average Gast
    """
    if not text:
        return {}

    kader = kader or list(NICKNAMES_MAP.values())
    raw = text.strip()
    t = raw

    # 1. Normalisierung von Kommazahlen, Zahlenwörtern und Uhrzeiten
    t = re.sub(r'(\d+)\s*komma\s*(\d+)', r'\1.\2', t, flags=re.IGNORECASE)
    t = re.sub(r'(\b\d{1,2}),(\d{1,2}\b)', r'\1.\2', t)
    t = re.sub(r'(\b\d{1,2})\s*uhr\s*(\d)\b', r'\1:0\2', t, flags=re.IGNORECASE)
    t = re.sub(r'(\b\d{1,2})\s*uhr\s*(\d{2})\b', r'\1:\2', t, flags=re.IGNORECASE)
    t = re.sub(r'(\b\d{1,2})\s*uhr\b', r'\1:00', t, flags=re.IGNORECASE)

    result = {
        'raw_text': text,
        'home_player': None,
        'away_player': None,
        'num_legs': None,
        'start_time': None,
        'end_time': None,
        'duration_min': None,
        'avg_home': None,
        'avg_away': None,
        'board': None,
        'match_number': None
    }

    # Optionale Marker für Board & Spielnummer
    bm = re.search(r'\b(?:board|scheibe)\s*(\d{1,2})\b', t, flags=re.IGNORECASE)
    if bm:
        result['board'] = int(bm.group(1))

    mn = re.search(r'\b(?:spiel|match|einzel|doppel)(?:\s*(?:nummer|nr\.?|#))?\s*(\d{1,2})\b', t, flags=re.IGNORECASE)
    if mn:
        result['match_number'] = int(mn.group(1))

    # 3. Modus / Legs
    # Zuerst: "3 Legs" oder "3 Lex"
    lm = re.search(r'\b(\d{1,2})\s*(?:legs|leg|lex|lecks|spiele)\b', t, flags=re.IGNORECASE)
    if not lm:
        # Dann: "Modus: 3", "Best of 5", "es wurden 3" (nicht gefolgt von Doppelpunkt wie bei Uhrzeit)
        lm = re.search(r'\b(?:legs|leg|lex|lecks|modus|best\s*of|es\s+wurden)\s*[:\s]*(\d{1,2})\b(?!\s*:\s*\d{2})', t, flags=re.IGNORECASE)
    if lm:
        result['num_legs'] = int(lm.group(1))

    # 6. Minutenzahl / Dauer
    # Zuerst: "17 Minuten" oder "17 min"
    dm = re.search(r'\b(\d{1,3})\s*(?:minuten|minute|min)\b', t, flags=re.IGNORECASE)
    if not dm:
        # Dann: "Dauer: 17", "Minutenzahl 17", "Spieldauer 17"
        dm = re.search(r'\b(?:spieldauer|minutenzahl|dauerte|dauer)\s*[:\s]*(\d{1,3})\b', t, flags=re.IGNORECASE)
    if dm:
        result['duration_min'] = int(dm.group(1))

    # 4. & 5. Start- und Endzeit
    time_pair = re.search(r'\b(\d{1,2}:\d{2})\s*(?:bis|bis um|-)\s*(\d{1,2}:\d{2})\b', t, flags=re.IGNORECASE)
    if time_pair:
        result['start_time'] = time_pair.group(1)
        result['end_time'] = time_pair.group(2)
    else:
        sm = re.search(r'\b(?:start|startzeit|beginn|von|ab|startete(?:\s*um)?)\s*[:\s]*(\d{1,2}:\d{2})\b', t, flags=re.IGNORECASE)
        if sm:
            result['start_time'] = sm.group(1)
        em = re.search(r'\b(?:ende|endzeit|bis|endete(?:\s*um)?)\s*[:\s]*(\d{1,2}:\d{2})\b', t, flags=re.IGNORECASE)
        if em:
            result['end_time'] = em.group(1)

    all_times = re.findall(r'\b(\d{1,2}:\d{2})\b', t)
    if not result['start_time'] and not result['end_time']:
        if len(all_times) >= 2:
            result['start_time'] = all_times[0]
            result['end_time'] = all_times[1]
        elif len(all_times) == 1:
            result['end_time'] = all_times[0]
    elif not result['start_time'] and len(all_times) >= 1 and all_times[0] != result['end_time']:
        result['start_time'] = all_times[0]

    # Automatische Zeit-Ergänzung falls Startzeit oder Endzeit fehlt
    if result['end_time'] and result['duration_min'] and not result['start_time']:
        try:
            eh, em_val = map(int, result['end_time'].split(':'))
            dt_e = datetime.datetime(2026, 1, 1, eh, em_val)
            dt_s = dt_e - datetime.timedelta(minutes=result['duration_min'])
            result['start_time'] = dt_s.strftime("%H:%M")
        except Exception:
            pass

    if result['start_time'] and result['duration_min'] and not result['end_time']:
        try:
            sh, sm_val = map(int, result['start_time'].split(':'))
            dt_s = datetime.datetime(2026, 1, 1, sh, sm_val)
            dt_e = dt_s + datetime.timedelta(minutes=result['duration_min'])
            result['end_time'] = dt_e.strftime("%H:%M")
        except Exception:
            pass

    if result['start_time'] and result['end_time'] and not result['duration_min']:
        try:
            sh, sm_val = map(int, result['start_time'].split(':'))
            eh, em_val = map(int, result['end_time'].split(':'))
            dt_s = datetime.datetime(2026, 1, 1, sh, sm_val)
            dt_e = datetime.datetime(2026, 1, 1, eh, em_val)
            if dt_e < dt_s:
                dt_e += datetime.timedelta(days=1)
            result['duration_min'] = int((dt_e - dt_s).total_seconds() // 60)
        except Exception:
            pass

    # 7. & 8. Gesamt-Averages
    av_h = re.search(r'\b(?:gesamt-average|average|avg|schnitt)\s*(?:für\s+)?(?:heimspieler|heimgegner|heim)\s*[:\s]*(\d{1,2}(?:\.\d{1,2})?)\b', t, flags=re.IGNORECASE)
    if av_h:
        result['avg_home'] = float(av_h.group(1))
    av_g = re.search(r'\b(?:gesamt-average|average|avg|schnitt)\s*(?:für\s+)?(?:gastspieler|gastgegner|gast)\s*[:\s]*(\d{1,2}(?:\.\d{1,2})?)\b', t, flags=re.IGNORECASE)
    if av_g:
        result['avg_away'] = float(av_g.group(1))

    # Chronologische Averages (Kommazahlen wie 43.8, 41.6)
    float_nums = re.findall(r'\b\d{2}\.\d{1,2}\b', t)
    if result['avg_home'] is None and result['avg_away'] is None:
        if len(float_nums) >= 2:
            result['avg_home'] = float(float_nums[0])
            result['avg_away'] = float(float_nums[1])
        elif len(float_nums) == 1:
            result['avg_home'] = float(float_nums[0])

    # 1. & 2. SPIELER-ZUORDNUNG & SAUBERE ABGRENZUNG
    hg_match = re.search(r'\b(?:heimspieler|heimgegner|heim)\b[:\s]*(.*?)(?=\s*\b(?:gastspieler|gastgegner|gast)\b|$)', t, flags=re.IGNORECASE)
    gg_match = re.search(r'\b(?:gastspieler|gastgegner|gast)\b[:\s]*(.*)', t, flags=re.IGNORECASE)

    explicit_home = None
    explicit_away = None
    if hg_match and gg_match:
        cand_h = clean_bounded_name(hg_match.group(1))
        cand_g = clean_bounded_name(gg_match.group(1))
        
        h_lions = find_lions_player_in_text(cand_h)
        g_lions = find_lions_player_in_text(cand_g)
        
        explicit_home = h_lions or cand_h
        explicit_away = g_lions or cand_g

    if explicit_home and explicit_away:
        result['home_player'] = explicit_home
        result['away_player'] = explicit_away
    else:
        # Intelligente Extraktion aus dem Gesamttext
        lions_p = find_lions_player_in_text(t)
        
        # Text von Lions-Spieler und dessen Spitznamen bereinigen
        t_without_lions = t
        if lions_p:
            for k, v in NICKNAMES_MAP.items():
                if v == lions_p:
                    t_without_lions = re.sub(rf'\b{re.escape(k)}\b', ' ', t_without_lions, flags=re.IGNORECASE)
        
        # Falls "Heimgegner..." oder "Heimspieler..." vorkommt, starte direkt dahinter
        h_prefix_m = re.search(r'\b(?:heimgegner|heimspieler|heim)\b[:\s]*(.*)', t_without_lions, flags=re.IGNORECASE)
        target_subtext = h_prefix_m.group(1) if h_prefix_m else t_without_lions
        
        opp_name = clean_bounded_name(target_subtext)

        if is_home_match:
            # Heimspiel: Lions sind Heim, Gegner ist Gast
            result['home_player'] = lions_p or "Lions Spieler"
            result['away_player'] = opp_name or "Gegner"
        else:
            # Auswärtsspiel: Gegner ist Heim, Lions sind Gast!
            result['home_player'] = opp_name or "Gegner"
            result['away_player'] = lions_p or "Lions Spieler"

    return result


def split_invalid_dart_number(val_str: str) -> List[int]:
    """
    Plausibilisiert und zerlegt Ziffernfolgen beliebiger Länge in gültige Dart-Scores (0 bis 180).
    Verhindert zuverlässig, dass aneinanderhängende Zahlen (wie '40402262', '33279100' oder '01313')
    verloren gehen, indem sie automatisch in plausible Dart-Scores (z. B. [40, 40, 22, 62], [33, 27, 9, 100], [0, 13, 13])
    aufgeteilt werden.
    """
    if not val_str:
        return []
    try:
        val = int(val_str)
    except ValueError:
        return []

    # Wenn es bereits ein einzelner gültiger Dart-Score ist (und keine führende Null wie '013' hat)
    if 0 <= val <= 180 and not (len(val_str) > 1 and val_str.startswith('0')):
        return [val]

    memo = {}

    def is_valid_token(tok: str) -> bool:
        if not tok:
            return False
        if len(tok) > 1 and tok.startswith('0'):
            return False  # Keine führenden Nullen wie '05', '00', '01'
        v = int(tok)
        return 0 <= v <= 180

    def solve(idx: int):
        if idx == len(val_str):
            return [[]]
        if idx in memo:
            return memo[idx]

        results = []
        for length in (3, 2, 1):
            if idx + length <= len(val_str):
                chunk = val_str[idx : idx + length]
                if is_valid_token(chunk):
                    v = int(chunk)
                    for rest in solve(idx + length):
                        results.append([v] + rest)

        memo[idx] = results
        return results

    all_solutions = solve(0)
    if not all_solutions:
        return [val] if val <= 180 else []

    def score_solution(sol: List[int]) -> int:
        score = 0
        # Strenge Strafe für aufeinanderfolgende Nullen (im Dartsport bei Spracheingabe nie vorhanden)
        for i in range(len(sol) - 1):
            if sol[i] == 0 and sol[i + 1] == 0:
                score -= 1000

        for x in sol:
            if 100 <= x <= 180:
                score += 35  # Typische Highscores (100, 140, 180 etc.)
            elif 10 <= x <= 99:
                score += 20  # Standard-Aufnahmen (z.B. 40, 60, 81, 26, 33, 27)
            elif x == 0:
                score += 10  # Einzelne Null ist gültig
            elif 1 <= x <= 9:
                score -= 15  # 1-stellige Zahlen 1-9 sind im Dart seltener
        return score

    all_solutions.sort(key=score_solution, reverse=True)
    return all_solutions[0]


def parse_leg_scores_speech(text: str) -> Dict[str, Any]:
    """
    Parst eingesprochene Leg-Scores für Heim- und Gastspieler.
    Unterstützt verschiedene Sprechweisen:
    - Blockweise: "Heim 100, 60, 140, 81, 20. Gast 60, 45, 100, 81, 0."
    - Blockweise mit Bezeichnungen: "Punkte Heim: 100 60 140 ... Punkte Gast: 60 45 100"
    - Rundenweise: "100 zu 60, 60 zu 45, 140 zu 100, 81 zu 81, 20"
    - Mit Darts: "Darts Heim 15, Darts Gast 18"
    - Mit Starter: "Starter Heim" oder "Gast beginnt"
    - Mit Leg: "Leg 2"
    """
    if not text:
        return {}

    norm = text.lower()
    norm = norm.replace("–", "-").replace("—", "-")
    
    result = {
        'raw_text': text,
        'leg_number': None,
        'scores_a': [],
        'scores_b': [],
        'darts_a': None,
        'darts_b': None,
        'starter': None
    }

    # 1. Leg Nummer (z.B. "Leg 2", "Leg Nummer 3")
    leg_m = re.search(r'\bleg(?:\s*(?:nummer|nr\.?|#))?\s*(\d{1,2})\b', norm)
    if leg_m:
        result['leg_number'] = int(leg_m.group(1))

    # 2. Starter (z.B. "Starter Heim", "Gast beginnt", "Heim fängt an")
    if re.search(r'\b(?:starter\s+heim|heim\s+beginnt|heim\s+fängt\s+an|heimspieler\s+beginnt)\b', norm):
        result['starter'] = 'Heimspieler'
    elif re.search(r'\b(?:starter\s+gast|gast\s+beginnt|gast\s+fängt\s+an|gastspieler\s+beginnt)\b', norm):
        result['starter'] = 'Gastspieler'

    # 3. Darts extrahieren (z.B. "Darts Heim 15", "Darts Gast 18")
    da_m = re.search(r'\bdarts?\s+(?:für\s+)?(?:heimspieler|heim)\s*[:\s]*(\d{1,2})\b', norm)
    if not da_m:
        da_m = re.search(r'\b(\d{1,2})\s*darts?\s+(?:für\s+)?(?:heimspieler|heim)\b', norm)
    if da_m:
        result['darts_a'] = int(da_m.group(1))

    db_m = re.search(r'\bdarts?\s+(?:für\s+)?(?:gastspieler|gast)\s*[:\s]*(\d{1,2})\b', norm)
    if not db_m:
        db_m = re.search(r'\b(\d{1,2})\s*darts?\s+(?:für\s+)?(?:gastspieler|gast)\b', norm)
    if db_m:
        result['darts_b'] = int(db_m.group(1))

    # Text von Darts-, Leg- und Starter-Klauseln befreien, damit diese Zahlen nicht in den Scores landen
    clean = norm
    clean = re.sub(r'\bleg(?:\s*(?:nummer|nr\.?|#))?\s*\d{1,2}\b', '', clean)
    clean = re.sub(r'\bdarts?\s+(?:für\s+)?(?:heimspieler|heim|gastspieler|gast)\s*[:\s]*\d{1,2}\b', '', clean)
    clean = re.sub(r'\b\d{1,2}\s*darts?\s+(?:für\s+)?(?:heimspieler|heim|gastspieler|gast)\b', '', clean)
    clean = re.sub(r'\b(?:starter\s+heim|heim\s+beginnt|heim\s+fängt\s+an|heimspieler\s+beginnt|starter\s+gast|gast\s+beginnt|gast\s+fängt\s+an|gastspieler\s+beginnt)\b', '', clean)

    def extract_numbers(s: str) -> List[int]:
        tokens = re.split(r'[\s,;:\n]+', s)
        nums = []
        for tok in tokens:
            t_clean = tok.strip(" .-_")
            if not t_clean:
                continue
            if re.match(r'^\d+$', t_clean):
                sub_nums = split_invalid_dart_number(t_clean)
                nums.extend(sub_nums)
            else:
                gw_val = parse_german_number_word(t_clean)
                if 0 <= gw_val <= 180:
                    nums.append(gw_val)
        return nums

    # 4. Scores parsen: Heim vs Gast Blöcke
    hg_split = re.search(r'\b(?:heimspieler|heim|punkte\s+heim|scores\s+heim)\b[:\s]+(.*?)\b(?:danach\s+gast|dann\s+gast|gastspieler|gast|punkte\s+gast|scores\s+gast)\b[:\s]*(.*)', clean, flags=re.DOTALL | re.IGNORECASE)
    gh_split = re.search(r'\b(?:gastspieler|gast|punkte\s+gast|scores\s+gast)\b[:\s]+(.*?)\b(?:heimspieler|heim|punkte\s+heim|scores\s+heim)\b[:\s]+(.*)', clean, flags=re.DOTALL | re.IGNORECASE)
    g_only_split = re.search(r'^(.*?)\b(?:danach\s+gast|dann\s+gast|gastspieler|gast|punkte\s+gast|scores\s+gast)\b[:\s]*(.*)', clean, flags=re.DOTALL | re.IGNORECASE)
    h_only_split = re.search(r'^(.*?)\b(?:heimspieler|heim|punkte\s+heim|scores\s+heim)\b[:\s]*(.*)', clean, flags=re.DOTALL | re.IGNORECASE)

    if hg_split:
        result['scores_a'] = extract_numbers(hg_split.group(1))
        result['scores_b'] = extract_numbers(hg_split.group(2))
    elif gh_split:
        result['scores_b'] = extract_numbers(gh_split.group(1))
        result['scores_a'] = extract_numbers(gh_split.group(2))
    elif g_only_split and g_only_split.group(1).strip():
        # User hat z. B. "40 40 22 ... Gast 100 68 ..." gesprochen (ohne "Heim" am Anfang)
        result['scores_a'] = extract_numbers(g_only_split.group(1))
        result['scores_b'] = extract_numbers(g_only_split.group(2))
    elif g_only_split and not g_only_split.group(1).strip():
        # User hat nur "Gast 100 68 28 ..." gesprochen
        result['scores_b'] = extract_numbers(g_only_split.group(2))
    elif h_only_split and not h_only_split.group(1).strip():
        # User hat nur "Heim 40 40 22 ..." gesprochen
        result['scores_a'] = extract_numbers(h_only_split.group(2))
    else:
        # Fall B: Rundenweise "100 zu 60, 60 zu 45, 140 zu 100"
        pair_matches = re.findall(r'\b(\d{1,3})\s*(?:zu|gegen|-)\s*(\d{1,3})\b', clean)
        if pair_matches:
            for p1, p2 in pair_matches:
                v1, v2 = int(p1), int(p2)
                if 0 <= v1 <= 180:
                    result['scores_a'].append(v1)
                if 0 <= v2 <= 180:
                    result['scores_b'].append(v2)
        else:
            # Fall C: Nur für Heim
            all_nums = extract_numbers(clean)
            if all_nums:
                result['scores_a'] = all_nums

    return result
