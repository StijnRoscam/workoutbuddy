from unittest.mock import Mock, patch

import pytest


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


class TestDatabase:
    def test_base_has_metadata(self):
        """Test that Base has metadata defined."""
        from app.core.db import Base

        assert Base.metadata is not None

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        from app.core.db import get_db

        mock_session = Mock()
        mock_session_local = Mock(return_value=mock_session)

        with patch("app.core.db.SessionLocal", mock_session_local):
            with get_db() as db:
                assert db == mock_session

            mock_session.close.assert_called_once()
