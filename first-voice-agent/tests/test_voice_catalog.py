import unittest
from unittest.mock import patch

from utils.agent_utils import voice_catalog


class VoiceCatalogTests(unittest.TestCase):
    def test_get_available_genders_returns_supported_order(self) -> None:
        self.assertEqual(voice_catalog.get_available_genders(), ["Female", "Male"])

    def test_get_available_languages_matches_voice_library_keys(self) -> None:
        self.assertEqual(
            voice_catalog.get_available_languages(),
            list(voice_catalog.VOICE_LIBRARY.keys()),
        )

    def test_get_language_config_returns_requested_language(self) -> None:
        hindi_config = voice_catalog.get_language_config("Hindi")

        self.assertEqual(hindi_config["locale"], "hi-IN")
        self.assertEqual(
            hindi_config["preview_text"],
            "Namaste, yah chuni hui awaaz ka sample hai.",
        )

    def test_get_language_config_falls_back_to_english_for_unknown_language(self) -> None:
        self.assertEqual(
            voice_catalog.get_language_config("Spanish"),
            voice_catalog.VOICE_LIBRARY["English"],
        )

    def test_get_language_locale_returns_selected_locale(self) -> None:
        self.assertEqual(voice_catalog.get_language_locale("Marathi"), "mr-IN")

    def test_get_language_locale_falls_back_to_english_locale(self) -> None:
        self.assertEqual(voice_catalog.get_language_locale("Spanish"), "en-IN")

    def test_get_preview_text_returns_selected_language_text(self) -> None:
        self.assertEqual(
            voice_catalog.get_preview_text("Gujarati"),
            "Namaste, aa pasand kareli voice nu sample chhe.",
        )

    def test_get_preview_text_falls_back_to_english_text(self) -> None:
        self.assertEqual(
            voice_catalog.get_preview_text("Spanish"),
            voice_catalog.VOICE_LIBRARY["English"]["preview_text"],
        )

    def test_get_voice_options_returns_gender_specific_voices(self) -> None:
        self.assertEqual(
            voice_catalog.get_voice_options("Tamil", "Male"),
            [{"id": "ta-IN-ValluvarNeural", "label": "ta-IN-ValluvarNeural"}],
        )

    def test_get_voice_options_falls_back_to_female_when_gender_is_unknown(self) -> None:
        self.assertEqual(
            voice_catalog.get_voice_options("Hindi", "Nonbinary"),
            [{"id": "hi-IN-SwaraNeural", "label": "hi-IN-SwaraNeural"}],
        )

    def test_get_voice_options_falls_back_to_english_for_unknown_language(self) -> None:
        self.assertEqual(
            voice_catalog.get_voice_options("Spanish", "Male"),
            [{"id": "en-IN-PrabhatNeural", "label": "en-IN-PrabhatNeural"}],
        )

    def test_get_default_voice_returns_first_voice_for_language_and_gender(self) -> None:
        self.assertEqual(
            voice_catalog.get_default_voice("Arabic (United Arab Emirates)", "Female"),
            "ar-AE-FatimaNeural",
        )

    def test_get_default_voice_uses_english_fallback_when_language_has_no_voices(self) -> None:
        patched_library = {
            **voice_catalog.VOICE_LIBRARY,
            "Test": {
                "locale": "te-ST",
                "preview_text": "Test preview",
                "voices": {"Female": [], "Male": []},
            },
        }

        with patch.object(voice_catalog, "VOICE_LIBRARY", patched_library):
            self.assertEqual(
                voice_catalog.get_default_voice("Test", "Male"),
                "en-IN-NeerjaNeural",
            )


if __name__ == "__main__":
    unittest.main()
