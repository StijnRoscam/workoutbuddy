import os
from unittest.mock import mock_open, patch

from app.core.config import Settings, get_settings


class TestSettings:
    def setup_method(self):
        """Clear settings cache before each test."""
        get_settings.cache_clear()

    def test_settings_loads_from_env(self):
        """Test that settings load from environment variables."""
        with (
            patch("builtins.open", mock_open(read_data="")),
            patch.dict(
                os.environ,
                {
                    "APP_NAME": "Test App",
                    "DATABASE_URL": "sqlite:///test.db",
                    "SECRET_KEY": "test-secret-key",
                },
                clear=True,
            ),
        ):
            settings = Settings()
            assert settings.app_name == "Test App"
            assert str(settings.database_url) == "sqlite:///test.db"
            assert settings.secret_key.get_secret_value() == "test-secret-key"

    def test_settings_defaults(self):
        """Test that settings have correct defaults."""
        with (
            patch("builtins.open", mock_open(read_data="")),
            patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "sqlite:///test.db",
                    "SECRET_KEY": "test-secret",
                },
                clear=True,
            ),
        ):
            settings = Settings()
            assert settings.app_name == "WorkoutBuddy API"
            assert settings.environment == "dev"
            assert settings.debug is False
            assert settings.algorithm == "HS256"
            assert settings.access_token_expire_minutes == 30
