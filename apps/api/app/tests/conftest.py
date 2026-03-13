import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def settings():
    """Get application settings."""
    from app.core.config import get_settings

    return get_settings()
