from __future__ import annotations

from typing import Dict, List

VOICE_LIBRARY: Dict[str, Dict[str, object]] = {
    "English": {
        "locale": "en-IN",
        "preview_text": "Hello, this is a preview of the selected outbound voice.",
        "voices": {
            "Female": [
                {"id": "en-IN-NeerjaNeural", "label": "en-IN-NeerjaNeural"},
            ],
            "Male": [
                {"id": "en-IN-PrabhatNeural", "label": "en-IN-PrabhatNeural"},
            ],
        },
    },
    "Hindi": {
        "locale": "hi-IN",
        "preview_text": "Namaste, yah chuni hui awaaz ka sample hai.",
        "voices": {
            "Female": [
                {"id": "hi-IN-SwaraNeural", "label": "hi-IN-SwaraNeural"},
            ],
            "Male": [
                {"id": "hi-IN-MadhurNeural", "label": "hi-IN-MadhurNeural"},
            ],
        },
    },
    "Marathi": {
        "locale": "mr-IN",
        "preview_text": "Namaskar, ha nivadlelya awazacha sample aahe.",
        "voices": {
            "Female": [
                {"id": "mr-IN-AarohiNeural", "label": "mr-IN-AarohiNeural"},
            ],
            "Male": [
                {"id": "mr-IN-ManoharNeural", "label": "mr-IN-ManoharNeural"},
            ],
        },
    },
    "Gujarati": {
        "locale": "gu-IN",
        "preview_text": "Namaste, aa pasand kareli voice nu sample chhe.",
        "voices": {
            "Female": [
                {"id": "gu-IN-DhwaniNeural", "label": "gu-IN-DhwaniNeural"},
            ],
            "Male": [
                {"id": "gu-IN-NiranjanNeural", "label": "gu-IN-NiranjanNeural"},
            ],
        },
    },
    "Bengali": {
        "locale": "bn-IN",
        "preview_text": "Nomoskar, eta nirbachito voice-er sample.",
        "voices": {
            "Female": [
                {"id": "bn-IN-TanishaaNeural", "label": "bn-IN-TanishaaNeural"},
            ],
            "Male": [
                {"id": "bn-IN-BashkarNeural", "label": "bn-IN-BashkarNeural"},
            ],
        },
    },
    "Tamil": {
        "locale": "ta-IN",
        "preview_text": "Vanakkam, idhu therndhedutha kuralin sample.",
        "voices": {
            "Female": [
                {"id": "ta-IN-PallaviNeural", "label": "ta-IN-PallaviNeural"},
            ],
            "Male": [
                {"id": "ta-IN-ValluvarNeural", "label": "ta-IN-ValluvarNeural"},
            ],
        },
    },
    "Telugu": {
        "locale": "te-IN",
        "preview_text": "Namaskaram, idi meeru enchukonna voice sample.",
        "voices": {
            "Female": [
                {"id": "te-IN-ShrutiNeural", "label": "te-IN-ShrutiNeural"},
            ],
            "Male": [
                {"id": "te-IN-MohanNeural", "label": "te-IN-MohanNeural"},
            ],
        },
    },
    "Kannada": {
        "locale": "kn-IN",
        "preview_text": "Namaskara, idu ayke madida dhvaniya sample.",
        "voices": {
            "Female": [
                {"id": "kn-IN-SapnaNeural", "label": "kn-IN-SapnaNeural"},
            ],
            "Male": [
                {"id": "kn-IN-GaganNeural", "label": "kn-IN-GaganNeural"},
            ],
        },
    },
    "Malayalam": {
        "locale": "ml-IN",
        "preview_text": "Namaskaram, ithu theranjedutha voice-inde sample aanu.",
        "voices": {
            "Female": [
                {"id": "ml-IN-SobhanaNeural", "label": "ml-IN-SobhanaNeural"},
            ],
            "Male": [
                {"id": "ml-IN-MidhunNeural", "label": "ml-IN-MidhunNeural"},
            ],
        },
    },
    "Arabic (United Arab Emirates)": {
        "locale": "ar-AE",
        "preview_text": "مرحبا، هذه عينة من الصوت المختار.",
        "voices": {
            "Female": [
                {"id": "ar-AE-FatimaNeural", "label": "ar-AE-FatimaNeural"},
            ],
            "Male": [
                {"id": "ar-AE-HamdanNeural", "label": "ar-AE-HamdanNeural"},
            ],
        },
    },
    
}


def get_available_genders() -> List[str]:
    return ["Female", "Male"]


def get_available_languages() -> List[str]:
    return list(VOICE_LIBRARY.keys())


def get_language_config(language: str) -> Dict[str, object]:
    return VOICE_LIBRARY.get(language, VOICE_LIBRARY["English"])


def get_language_locale(language: str) -> str:
    return str(get_language_config(language).get("locale", "en-IN"))


def get_preview_text(language: str) -> str:
    return str(get_language_config(language).get("preview_text", VOICE_LIBRARY["English"]["preview_text"]))


def get_voice_options(language: str, gender: str) -> List[Dict[str, str]]:
    voices = get_language_config(language).get("voices", {})
    selected_gender = gender if gender in voices else "Female"
    return list(voices.get(selected_gender, []))


def get_default_voice(language: str, gender: str) -> str:
    options = get_voice_options(language, gender)
    if options:
        return options[0]["id"]

    fallback = get_voice_options("English", "Female")
    return fallback[0]["id"]
