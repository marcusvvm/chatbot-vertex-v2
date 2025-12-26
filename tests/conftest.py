import pytest
from app.core.auth import create_access_token


@pytest.fixture
def auth_headers():
    """Retorna headers de autenticação para testes"""
    token = create_access_token(subject="test_user", purpose="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def valid_token():
    """Retorna um token válido para testes"""
    return create_access_token(subject="test_user", purpose="admin")
