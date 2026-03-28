"""
JeevanSetu.AI — Google Cloud Speech-to-Text Service
Converts voice recordings to text for processing.
"""

import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechService:
    """Google Cloud Speech-to-Text integration."""

    def __init__(self):
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize the Speech-to-Text client."""
        try:
            from google.cloud import speech_v1 as speech
            self.client = speech.SpeechClient()
            self.speech = speech
            self.available = True
            logger.info("✅ Google Cloud Speech-to-Text initialized")
        except Exception as e:
            logger.warning(f"⚠️ Speech-to-Text not available: {e}")
            logger.info("  Voice input will use browser-based Web Speech API as fallback")

    async def transcribe_audio(self, audio_data: bytes, 
                                sample_rate: int = 48000,
                                encoding: str = "WEBM_OPUS",
                                language: str = "en-US") -> dict:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate in Hz
            encoding: Audio encoding format
            language: BCP-47 language code
            
        Returns:
            dict with 'text', 'confidence', and 'words'
        """
        if not self.available:
            return {
                "text": "",
                "confidence": 0.0,
                "words": [],
                "error": "Speech-to-Text service not available"
            }

        try:
            # Map encoding string to enum
            encoding_map = {
                "WEBM_OPUS": self.speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "LINEAR16": self.speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "FLAC": self.speech.RecognitionConfig.AudioEncoding.FLAC,
                "MP3": self.speech.RecognitionConfig.AudioEncoding.MP3,
                "OGG_OPUS": self.speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            }

            audio_encoding = encoding_map.get(
                encoding.upper(),
                self.speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
            )

            audio = self.speech.RecognitionAudio(content=audio_data)
            config = self.speech.RecognitionConfig(
                encoding=audio_encoding,
                sample_rate_hertz=sample_rate,
                language_code=language,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                model="latest_long",
                use_enhanced=True,
            )

            response = self.client.recognize(config=config, audio=audio)

            if not response.results:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "words": [],
                    "error": "No speech detected in audio"
                }

            # Combine all results
            full_text = ""
            total_confidence = 0.0
            word_count = 0
            words = []

            for result in response.results:
                alternative = result.alternatives[0]
                full_text += alternative.transcript + " "
                total_confidence += alternative.confidence

                for word_info in alternative.words:
                    words.append({
                        "word": word_info.word,
                        "start_time": word_info.start_time.total_seconds(),
                        "end_time": word_info.end_time.total_seconds(),
                    })

            avg_confidence = total_confidence / len(response.results) if response.results else 0.0

            return {
                "text": full_text.strip(),
                "confidence": round(avg_confidence, 3),
                "words": words,
                "language": language
            }

        except Exception as e:
            logger.error(f"Speech-to-Text error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "words": [],
                "error": str(e)
            }


# Singleton
_speech_service: Optional[SpeechService] = None


def get_speech_service() -> SpeechService:
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service
