import speech_recognition as sr
import pyttsx3
import threading
import pythoncom
import time

# ============================================================
# LANGUAGE CONFIGURATION
# ============================================================

# Supported language codes — Google STT format
LANGUAGE_CODES = {
    "english": ["en-US", "en-GB"],
    "urdu":    ["ur-PK", "ur-IN"],
    "hindi":   ["hi-IN", "hi-Latn"],
    "auto":    ["en-US", "ur-PK", "hi-IN"],   # tries all three in order
}

# Set this to "auto", "english", "urdu", or "hindi"
CURRENT_LANGUAGE = "auto"

# ============================================================
# TEXT TO SPEECH
# ============================================================

# ============================================================
# VOICE SETTINGS — change voice here
# ============================================================
# English female (natural): "en-US-JennyNeural" or "en-US-AriaNeural"
# Urdu female (natural):    "ur-PK-UzmaNeural"
# Urdu male:                "ur-PK-AsadNeural"

ZARA_VOICE    = "en-US-JennyNeural"   # default English voice
ZARA_VOICE_UR = "ur-PK-UzmaNeural"   # Urdu voice
SPEECH_RATE   = "-5%"                 # slow down slightly: use "+10%" to speed up

def _detect_urdu(text: str) -> bool:
    """Returns True if text contains Urdu/Arabic script characters."""
    for ch in text:
        if '\u0600' <= ch <= '\u06FF':
            return True
    return False

def speak(text: str, force_voice: str = None):
    """
    Speaks text using Microsoft Edge neural TTS + pygame (silent, no media player).
    Auto-detects Urdu script and switches to Urdu voice.
    """
    def run():
        import asyncio
        import edge_tts
        import tempfile
        import os

        if force_voice:
            voice = force_voice
        elif _detect_urdu(text):
            voice = ZARA_VOICE_UR
        else:
            voice = ZARA_VOICE

        tmp_path = None
        try:
            # ── Step 1: Generate MP3 via Edge TTS ──
            async def _generate():
                communicate = edge_tts.Communicate(text=text, voice=voice, rate=SPEECH_RATE)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    path = f.name
                await communicate.save(path)
                return path

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tmp_path = loop.run_until_complete(_generate())
            loop.close()

            # ── Step 2: Play with pygame (no window, no media player) ──
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()

            # Wait until playback finishes
            import time
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            pygame.mixer.music.unload()
            pygame.mixer.quit()

        except Exception as e:
            print(f"[Zara Voice] Error: {e}")
            # Silent fallback — pyttsx3 if everything fails
            try:
                pythoncom.CoInitialize()
                engine = pyttsx3.init()
                voices_list = engine.getProperty('voices')
                if len(voices_list) > 1:
                    engine.setProperty('voice', voices_list[1].id)
                engine.setProperty('rate', 155)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                pythoncom.CoUninitialize()
            except Exception as ex:
                print(f"[Zara Voice] Fallback also failed: {ex}")

        finally:
            # Cleanup temp file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()


# ============================================================
# FIND BEST MICROPHONE
# ============================================================

def get_best_microphone_index():
    """
    Automatically picks the best available microphone.
    Prefers real mics over virtual/loopback devices.
    Returns None to use system default if nothing is found.
    """
    mic_list = sr.Microphone.list_microphone_names()
    print("\n[Available Microphones]")
    for i, name in enumerate(mic_list):
        print(f"  [{i}] {name}")

    # Priority keywords to prefer (real mics)
    preferred = ["realtek", "microphone", "headset", "input", "capture"]
    # Keywords to avoid (virtual/output devices)
    avoid = ["stereo mix", "loopback", "output", "speaker", "vb-audio",
             "virtual", "wasapi", "mapper"]

    best_index = None
    for i, name in enumerate(mic_list):
        name_lower = name.lower()
        if any(a in name_lower for a in avoid):
            continue
        if any(p in name_lower for p in preferred):
            best_index = i
            break

    if best_index is not None:
        print(f"\n[Selected Mic] [{best_index}] {mic_list[best_index]}")
    else:
        print("\n[Selected Mic] System default")

    return best_index


# ============================================================
# CORE LISTEN FUNCTION — tries multiple language codes
# ============================================================

recognizer = sr.Recognizer()
recognizer.energy_threshold = 2500
recognizer.pause_threshold = 0.9
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_ratio = 1.5

_mic_index = None   # cached after first call

def listen(language: str = None, timeout: int = 8, phrase_limit: int = 15):
    """
    Records from microphone and converts speech to text.

    Parameters:
        language: "auto", "english", "urdu", "hindi", or None (uses CURRENT_LANGUAGE)
        timeout:  seconds to wait before giving up if no speech detected
        phrase_limit: max seconds of speech to capture

    Returns:
        str: recognized text, or None if nothing was understood
    """
    global _mic_index

    lang_key = (language or CURRENT_LANGUAGE).lower()
    lang_codes = LANGUAGE_CODES.get(lang_key, LANGUAGE_CODES["auto"])

    pythoncom.CoInitialize()
    try:
        # Cache mic index so we don't scan on every call
        if _mic_index is None:
            _mic_index = get_best_microphone_index()

        mic_kwargs = {"device_index": _mic_index} if _mic_index is not None else {}

        with sr.Microphone(**mic_kwargs) as source:
            print(f"\n[Voice] Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            print(f"[Voice] Listening... (energy threshold: {int(recognizer.energy_threshold)})")

            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
            except sr.WaitTimeoutError:
                print("[Voice] No speech detected (timeout)")
                return None

        # Try each language code in order
        for lang_code in lang_codes:
            try:
                print(f"[Voice] Recognizing with language: {lang_code}")
                text = recognizer.recognize_google(audio, language=lang_code)
                print(f"[Voice] Recognized ({lang_code}): {text}")
                return text

            except sr.UnknownValueError:
                print(f"[Voice] Could not understand with {lang_code}, trying next...")
                continue

            except sr.RequestError as e:
                print(f"[Voice] Google STT service error: {e}")
                # Try offline fallback if network fails
                return _try_offline_fallback(audio)

        print("[Voice] Could not understand speech in any language")
        return None

    except Exception as e:
        print(f"[Voice] Unexpected error: {str(e)}")
        return None

    finally:
        pythoncom.CoUninitialize()


# ============================================================
# OFFLINE FALLBACK (Sphinx — works without internet)
# ============================================================

def _try_offline_fallback(audio):
    """
    Falls back to CMU Sphinx for offline English recognition.
    Only used if Google STT is unavailable.
    Install with: pip install pocketsphinx
    """
    try:
        text = recognizer.recognize_sphinx(audio)
        print(f"[Voice] Offline fallback result: {text}")
        return text
    except Exception:
        print("[Voice] Offline fallback also failed")
        return None


# ============================================================
# LANGUAGE SWITCHER
# ============================================================

def set_language(lang: str):
    """
    Call this to change the recognition language at runtime.
    Options: "auto", "english", "urdu", "hindi"
    """
    global CURRENT_LANGUAGE
    lang = lang.lower()
    if lang in LANGUAGE_CODES:
        CURRENT_LANGUAGE = lang
        print(f"[Voice] Language set to: {lang}")
    else:
        print(f"[Voice] Unknown language '{lang}'. Options: {list(LANGUAGE_CODES.keys())}")


# ============================================================
# WAKE WORD DETECTION — listens for "zara" before processing
# ============================================================

WAKE_WORDS = ["zara", "hey zara", "ok zara", "zara"]

def listen_for_wake_word(timeout: int = 10):
    """
    Listens continuously until it hears the wake word 'Zara'.
    Returns the full command spoken after the wake word,
    or None if only the wake word was detected (wait for next input).
    """
    global _mic_index
    pythoncom.CoInitialize()
    try:
        if _mic_index is None:
            _mic_index = get_best_microphone_index()

        mic_kwargs = {"device_index": _mic_index} if _mic_index is not None else {}

        with sr.Microphone(**mic_kwargs) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("[Zara] Waiting for wake word...")

            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return None

        try:
            text = recognizer.recognize_google(audio, language="en-US").lower()
            print(f"[Zara] Heard: {text}")

            for word in WAKE_WORDS:
                if word in text:
                    # Extract command after wake word
                    after = text.split(word, 1)[-1].strip(" ,.")
                    print(f"[Zara] Wake word detected! Command: '{after}'")
                    return after if after else "__WAKE_ONLY__"

        except (sr.UnknownValueError, sr.RequestError):
            pass

        return None

    finally:
        pythoncom.CoUninitialize()


# ============================================================
# MICROPHONE DIAGNOSTICS — run this to troubleshoot
# ============================================================

def test_microphone():
    """
    Run this function directly to test your mic setup.
    It prints all available mics and tests a 5-second recording.
    """
    print("\n=== MICROPHONE TEST ===")
    mics = sr.Microphone.list_microphone_names()
    for i, name in enumerate(mics):
        print(f"  [{i}] {name}")

    index = get_best_microphone_index()
    mic_kwargs = {"device_index": index} if index is not None else {}

    print("\nSpeak for 5 seconds (testing English + Urdu + Hindi)...")
    pythoncom.CoInitialize()
    try:
        with sr.Microphone(**mic_kwargs) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)

        for code in ["en-US", "ur-PK", "hi-IN"]:
            try:
                result = recognizer.recognize_google(audio, language=code)
                print(f"  [{code}] → {result}")
            except sr.UnknownValueError:
                print(f"  [{code}] → (not understood)")
            except sr.RequestError as e:
                print(f"  [{code}] → Error: {e}")
    finally:
        pythoncom.CoUninitialize()

    print("=== TEST DONE ===\n")


# Run test if executed directly
if __name__ == "__main__":
    test_microphone()