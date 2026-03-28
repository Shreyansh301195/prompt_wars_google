"""
JeevanSetu.AI — Google Cloud Text-to-Speech Service
Generates audio from text for accessibility.
"""

import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """Google Cloud Text-to-Speech integration for accessibility."""

    def __init__(self):
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize the Text-to-Speech client."""
        try:
            from google.cloud import texttospeech_v1 as tts
            self.client = tts.TextToSpeechClient()
            self.tts = tts
            self.available = True
            logger.info("✅ Google Cloud Text-to-Speech initialized")
        except Exception as e:
            logger.warning(f"⚠️ Text-to-Speech not available: {e}")
            logger.info("  Audio output will use browser-based Speech Synthesis as fallback")

    async def synthesize(self, text: str, language: str = "en-US",
                         voice_type: str = "standard") -> dict:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            language: BCP-47 language code
            voice_type: 'standard' or 'neural'
            
        Returns:
            dict with 'audio_base64' (base64 encoded MP3) and metadata
        """
        if not self.available:
            return {
                "audio_base64": "",
                "error": "Text-to-Speech service not available. Use browser speech synthesis."
            }

        try:
            synthesis_input = self.tts.SynthesisInput(text=text[:5000])  # Limit to 5000 chars

            # Select voice
            voice_name = f"{language}-Standard-A"
            ssml_gender = self.tts.SsmlVoiceGender.FEMALE

            if voice_type == "neural":
                voice_name = f"{language}-Neural2-A"

            voice = self.tts.VoiceSelectionParams(
                language_code=language,
                name=voice_name,
                ssml_gender=ssml_gender,
            )

            audio_config = self.tts.AudioConfig(
                audio_encoding=self.tts.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0,
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            audio_base64 = base64.b64encode(response.audio_content).decode("utf-8")

            return {
                "audio_base64": audio_base64,
                "format": "mp3",
                "language": language,
                "voice_type": voice_type,
                "text_length": len(text)
            }

        except Exception as e:
            logger.error(f"Text-to-Speech error: {e}")
            return {
                "audio_base64": "",
                "error": str(e)
            }


# Singleton
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
