from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid loading from env vars."""
    mock_settings_instance = Mock()
    mock_settings_instance.database_url = "sqlite:///./test.db"
    mock_settings_instance.secret_key = Mock()
    mock_settings_instance.secret_key.get_secret_value.return_value = "test-secret"
    mock_settings_instance.algorithm = "HS256"
    mock_settings_instance.access_token_expire_minutes = 30
    mock_settings_instance.cors_origins = ["http://localhost:3000"]
    mock_settings_instance.app_name = "Test App"
    mock_settings_instance.environment = "test"
    mock_settings_instance.debug = True

    with patch("app.core.config.get_settings", return_value=mock_settings_instance):
        yield mock_settings_instance


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, mock_settings):
        """Test that health check returns status ok."""
        from app.main import app

        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
