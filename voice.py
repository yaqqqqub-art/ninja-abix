"""
voice.py - Guard der kothar awaj (text to speech).

Install korun (ekbar):
    pip install pyttsx3
    pip install gTTS

Kibhabe kaj kore:
  1. pyttsx3 (offline, sathe sathe bole) - age eta try kore.
  2. pyttsx3 na thakle ba kaj na korle gTTS (Google TTS, internet lage) use kore.
  3. dutor ekta o na thakle game chup-chap cholbe (kotha shudhu bubble e lekha thakbe).

Use:
    import voice
    voice.init()
    voice.say("Freeze! Don't move!")
Awaj alada thread e bole, tai game atke na.
"""
import os
import queue
import tempfile
import threading
import time

import lang

_q = queue.Queue(maxsize=2)
_state = {"started": False, "backend": None, "enabled": True, "thread": None}
_SHORT = {"en": "en", "bn": "bn", "zh-CN": "zh", "ja": "ja", "es": "es"}
_engine = {"e": None}


def _has(module):
    try:
        __import__(module)
        return True
    except Exception:
        return False


def backend_name():
    """Kon library paoa gese: 'pyttsx3' | 'gTTS' | None"""
    if _has("pyttsx3"):
        return "pyttsx3"
    if _has("gtts"):
        return "gTTS"
    return None


def init(enabled=True):
    _state["enabled"] = enabled
    if _state["started"]:
        return _state["backend"]
    _state["backend"] = backend_name()
    _state["started"] = True
    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    _state["thread"] = th
    return _state["backend"]


def set_language(code):
    """Bhasha bodlano - guard er kotha oi bhasha-y bolbe (anubad thakle)."""
    lang.set_lang(code)


def set_enabled(on):
    _state["enabled"] = bool(on)


def say(text):
    """Kotha bolo (queue te dhoke; beshi jome gele notun ta fele deya hoy)."""
    if not _state["enabled"] or not text:
        return False
    if not _state["started"]:
        init()
    try:
        _q.put_nowait(lang.speak_text(text))      # (kotha, gTTS bhasha code)
        return True
    except queue.Full:
        return False


# ------------------------------------------------------------------
# internal
# ------------------------------------------------------------------
def _speak_pyttsx3(text, code="en"):
    try:
        import pyttsx3
    except Exception:
        return False
    try:
        eng = _engine["e"]
        if eng is None:
            eng = pyttsx3.init()
            eng.setProperty("rate", 150)
            eng.setProperty("volume", 1.0)
            _engine["e"] = eng
        short = _SHORT.get(code, "en")
        chosen = None
        try:
            voices = eng.getProperty("voices")
            if short == "en":                                    # purush-er gola khuje ne
                for v in voices:
                    name = (getattr(v, "name", "") or "").lower()
                    if any(k in name for k in ("david", "male", "mark", "alex", "daniel", "george")) \
                            and "female" not in name:
                        chosen = v.id
                        break
            else:                                                # oi bhasha-r gola (na thakle gTTS e jabe)
                for v in voices:
                    name = ((getattr(v, "name", "") or "") + " " + str(getattr(v, "id", ""))
                            + " " + str(getattr(v, "languages", ""))).lower()
                    if any(k in name for k in lang.VOICE_HINT.get(short, ())):
                        chosen = v.id
                        break
                if chosen is None:
                    return False
            if chosen:
                eng.setProperty("voice", chosen)
        except Exception:
            if short != "en":
                return False
        eng.say(text)
        eng.runAndWait()
        return True
    except Exception:
        _engine["e"] = None
        return False


def _speak_gtts(text, code="en"):
    try:
        from gtts import gTTS
        import pygame
    except Exception:
        return False
    path = None
    try:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        gTTS(text=text, lang=code).save(path)
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        return True
    except Exception:
        return False
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def _worker():
    while True:
        item = _q.get()
        if item is None:
            return
        if not _state["enabled"]:
            continue
        text, code = item
        if _speak_pyttsx3(text, code):
            continue
        _speak_gtts(text, code)
