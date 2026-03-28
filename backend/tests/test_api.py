"""
JeevanSetu.AI — API Tests
Unit tests for all API endpoints with mocked Google services.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json

from backend.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /api/health endpoint."""

    def test_health_check_returns_200(self):
        """Health check should return 200 with service status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "services" in data

    def test_health_check_has_all_services(self):
        """Health check should list all Google services."""
        response = client.get("/api/health")
        data = response.json()
        services = data["services"]
        expected_services = ["gemini", "ollama", "speech_to_text", 
                            "text_to_speech", "natural_language", "vision", "maps"]
        for service in expected_services:
            assert service in services, f"Missing service: {service}"


class TestServicesStatus:
    """Tests for the /api/services-status endpoint."""

    def test_services_status_returns_all(self):
        """Services status should return info for all services."""
        response = client.get("/api/services-status")
        assert response.status_code == 200
        data = response.json()
        assert "gemini" in data
        assert "ollama" in data
        assert "speech_to_text" in data
        assert "text_to_speech" in data
        assert "natural_language" in data
        assert "vision" in data
        assert "maps" in data

    def test_each_service_has_required_fields(self):
        """Each service should have name, available, and description."""
        response = client.get("/api/services-status")
        data = response.json()
        for service_key, service_data in data.items():
            assert "name" in service_data, f"{service_key} missing 'name'"
            assert "available" in service_data, f"{service_key} missing 'available'"
            assert "description" in service_data, f"{service_key} missing 'description'"


class TestProcessEndpoint:
    """Tests for the /api/process endpoint."""

    def test_process_requires_input(self):
        """Process should reject requests with no input."""
        response = client.post("/api/process")
        assert response.status_code == 400

    @patch('backend.services.gemini_service.GeminiService.process_full_pipeline')
    def test_process_with_text(self, mock_pipeline):
        """Process should handle text input."""
        mock_pipeline.return_value = {
            "classification": {
                "input_type": "text",
                "domain": "medical",
                "urgency": "high",
                "confidence": 0.92,
                "summary": "Medical emergency described"
            },
            "extracted_data": {
                "entities": [{"name": "chest pain", "type": "symptom", "value": "chest pain", "confidence": 0.95}],
                "key_facts": ["Patient experiencing chest pain"],
                "relationships": [],
                "summary": "Patient with chest pain symptoms"
            },
            "actions": [
                {
                    "id": 1,
                    "title": "Call Emergency Services",
                    "description": "Call 112 immediately",
                    "priority": "immediate",
                    "category": "emergency",
                    "is_verified": True,
                    "verification_notes": "Standard emergency protocol",
                    "contact_info": "112"
                }
            ],
            "stages": [],
            "ai_engine": "gemini"
        }

        response = client.post(
            "/api/process",
            data={"text": "I have severe chest pain"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "medical"
        assert data["urgency"] == "high"
        assert len(data["action_plan"]) > 0

    def test_process_rejects_bad_image_type(self):
        """Process should reject unsupported image types."""
        response = client.post(
            "/api/process",
            files={"image": ("test.exe", b"data", "application/octet-stream")}
        )
        assert response.status_code == 400


class TestHistoryEndpoint:
    """Tests for the /api/history endpoint."""

    def test_history_returns_list(self):
        """History should return a list of entries."""
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total" in data
        assert isinstance(data["history"], list)


class TestTTSEndpoint:
    """Tests for the /api/tts endpoint."""

    def test_tts_requires_text(self):
        """TTS should reject empty text."""
        response = client.post(
            "/api/tts",
            json={"text": "", "language": "en-US"}
        )
        assert response.status_code == 400

    @patch('backend.services.tts_service.TTSService.synthesize')
    def test_tts_with_text(self, mock_synth):
        """TTS should return audio data for valid text."""
        mock_synth.return_value = {
            "audio_base64": "dGVzdA==",
            "format": "mp3",
            "language": "en-US"
        }
        response = client.post(
            "/api/tts",
            json={"text": "Hello world", "language": "en-US", "voice_type": "standard"}
        )
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_info(self):
        """Root should return app information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "JeevanSetu.AI"
        assert "docs" in data


class TestInputSanitization:
    """Tests for input sanitization."""

    def test_sanitize_html(self):
        """Should escape HTML in text input."""
        from backend.core.security import sanitize_text_input
        result = sanitize_text_input('<script>alert("xss")</script>')
        assert '<script>' not in result

    def test_sanitize_long_input(self):
        """Should truncate very long inputs."""
        from backend.core.security import sanitize_text_input
        long_text = "a" * 20000
        result = sanitize_text_input(long_text)
        assert len(result) <= 10000

    def test_sanitize_empty(self):
        """Should handle empty input."""
        from backend.core.security import sanitize_text_input
        assert sanitize_text_input("") == ""
        assert sanitize_text_input(None) == ""

    def test_validate_file_type(self):
        """Should validate file types correctly."""
        from backend.core.security import validate_file_type, ALLOWED_IMAGE_TYPES
        assert validate_file_type("photo.jpg", ALLOWED_IMAGE_TYPES) is True
        assert validate_file_type("photo.png", ALLOWED_IMAGE_TYPES) is True
        assert validate_file_type("virus.exe", ALLOWED_IMAGE_TYPES) is False
        assert validate_file_type("", ALLOWED_IMAGE_TYPES) is False
