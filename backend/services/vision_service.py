"""
JeevanSetu.AI — Google Cloud Vision Service
OCR and image analysis for document/medical record processing.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VisionService:
    """Google Cloud Vision API integration."""

    def __init__(self):
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize the Vision API client."""
        try:
            from google.cloud import vision_v1 as vision
            self.client = vision.ImageAnnotatorClient()
            self.vision = vision
            self.available = True
            logger.info("✅ Google Cloud Vision API initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vision API not available: {e}")
            logger.info("  Image analysis will be handled by Gemini multimodal instead")

    async def detect_text(self, image_data: bytes) -> dict:
        """
        Perform OCR on an image.
        
        Returns:
            dict with 'text' and 'blocks'
        """
        if not self.available:
            return {"text": "", "blocks": [], "error": "Vision API not available"}

        try:
            image = self.vision.Image(content=image_data)
            response = self.client.document_text_detection(image=image)

            if response.error.message:
                return {"text": "", "blocks": [], "error": response.error.message}

            full_text = ""
            blocks = []

            if response.full_text_annotation:
                full_text = response.full_text_annotation.text

                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        block_text = ""
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = "".join([s.text for s in word.symbols])
                                block_text += word_text + " "
                        blocks.append({
                            "text": block_text.strip(),
                            "confidence": round(block.confidence, 3) if hasattr(block, 'confidence') else 0.0
                        })

            return {
                "text": full_text,
                "blocks": blocks,
                "block_count": len(blocks)
            }

        except Exception as e:
            logger.error(f"Vision OCR error: {e}")
            return {"text": "", "blocks": [], "error": str(e)}

    async def detect_labels(self, image_data: bytes) -> dict:
        """
        Detect labels/objects in an image.
        
        Returns:
            dict with 'labels' list
        """
        if not self.available:
            return {"labels": [], "error": "Vision API not available"}

        try:
            image = self.vision.Image(content=image_data)
            response = self.client.label_detection(image=image)

            if response.error.message:
                return {"labels": [], "error": response.error.message}

            labels = []
            for label in response.label_annotations:
                labels.append({
                    "description": label.description,
                    "score": round(label.score, 3),
                    "topicality": round(label.topicality, 3)
                })

            return {"labels": labels}

        except Exception as e:
            logger.error(f"Vision label detection error: {e}")
            return {"labels": [], "error": str(e)}

    async def detect_safe_search(self, image_data: bytes) -> dict:
        """Check image for safe search violations."""
        if not self.available:
            return {"safe": True, "error": "Vision API not available"}

        try:
            image = self.vision.Image(content=image_data)
            response = self.client.safe_search_detection(image=image)
            safe = response.safe_search_annotation

            likelihood_name = {
                0: "UNKNOWN", 1: "VERY_UNLIKELY", 2: "UNLIKELY",
                3: "POSSIBLE", 4: "LIKELY", 5: "VERY_LIKELY"
            }

            return {
                "safe": safe.adult < 4 and safe.violence < 4,
                "adult": likelihood_name.get(safe.adult, "UNKNOWN"),
                "violence": likelihood_name.get(safe.violence, "UNKNOWN"),
                "medical": likelihood_name.get(safe.medical, "UNKNOWN"),
            }

        except Exception as e:
            logger.error(f"Safe search error: {e}")
            return {"safe": True, "error": str(e)}


# Singleton
_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
