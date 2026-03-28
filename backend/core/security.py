"""
JeevanSetu.AI — Security Module
Input sanitization, rate limiting, and CORS configuration.
"""

import re
import time
import html
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter."""

    def __init__(self, app, requests_per_minute: int = 30):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old entries
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > window_start
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response


def sanitize_text_input(text: str) -> str:
    """Sanitize user text input to prevent injection attacks."""
    if not text:
        return ""

    # HTML escape
    text = html.escape(text)

    # Remove potential script tags (even after escaping, for safety)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Limit length to prevent abuse
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def validate_file_type(filename: str, allowed_types: list[str]) -> bool:
    """Validate file extension against allowed types."""
    if not filename:
        return False
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in allowed_types


ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
ALLOWED_AUDIO_TYPES = ['wav', 'mp3', 'webm', 'ogg', 'flac', 'm4a']
ALLOWED_DOCUMENT_TYPES = ['pdf', 'txt', 'doc', 'docx', 'csv']

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
