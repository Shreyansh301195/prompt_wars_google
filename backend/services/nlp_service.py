"""
JeevanSetu.AI — Google Cloud Natural Language Service
Entity extraction and sentiment analysis for verification.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NLPService:
    """Google Cloud Natural Language API integration."""

    def __init__(self):
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize the Natural Language client."""
        try:
            from google.cloud import language_v2 as language
            self.client = language.LanguageServiceClient()
            self.language = language
            self.available = True
            logger.info("✅ Google Cloud Natural Language API initialized")
        except Exception as e:
            logger.warning(f"⚠️ Natural Language API not available: {e}")
            logger.info("  Entity extraction will be handled by Gemini instead")

    async def analyze_entities(self, text: str) -> dict:
        """
        Extract entities from text using Google Cloud NLP.
        
        Returns:
            dict with 'entities' list and 'language'
        """
        if not self.available:
            return {"entities": [], "error": "NLP service not available"}

        try:
            document = self.language.Document(
                content=text[:10000],  # API limit
                type_=self.language.Document.Type.PLAIN_TEXT,
                language_code="en"
            )

            response = self.client.analyze_entities(
                request={"document": document, "encoding_type": self.language.EncodingType.UTF8}
            )

            entities = []
            for entity in response.entities:
                entity_type_map = {
                    0: "unknown", 1: "person", 2: "location", 3: "organization",
                    4: "event", 5: "work_of_art", 6: "consumer_good",
                    7: "other", 9: "phone_number", 10: "address",
                    11: "date", 12: "number", 13: "price"
                }
                entities.append({
                    "name": entity.name,
                    "type": entity_type_map.get(entity.type_, "other"),
                    "salience": round(getattr(entity, 'salience', 0.5), 3),
                    "metadata": dict(entity.metadata) if entity.metadata else {}
                })

            return {
                "entities": entities,
                "language": response.language_code if hasattr(response, 'language_code') else "en"
            }

        except Exception as e:
            logger.error(f"NLP API error: {e}")
            return {"entities": [], "error": str(e)}

    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of the text."""
        if not self.available:
            return {"score": 0.0, "magnitude": 0.0, "error": "NLP service not available"}

        try:
            document = self.language.Document(
                content=text[:10000],
                type_=self.language.Document.Type.PLAIN_TEXT,
                language_code="en"
            )

            response = self.client.analyze_sentiment(
                request={"document": document, "encoding_type": self.language.EncodingType.UTF8}
            )

            return {
                "score": round(response.document_sentiment.score, 3),
                "magnitude": round(response.document_sentiment.magnitude, 3),
            }

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"score": 0.0, "magnitude": 0.0, "error": str(e)}


# Singleton
_nlp_service: Optional[NLPService] = None


def get_nlp_service() -> NLPService:
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service
