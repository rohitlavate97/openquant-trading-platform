"""Global pytest fixtures and configuration."""

import pytest
from httpx import ASGITransport, AsyncClient
from openquant.interfaces.api.app import create_app


@pytest.fixture
def app():
    """Create FastAPI application instance for testing."""
    return create_app()


@pytest.fixture
async def async_client(app):
    """Provide asynchronous HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
