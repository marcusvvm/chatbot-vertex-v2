import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.auth import create_access_token, decode_token
from app.core.config import settings
from app.schemas.auth import TokenData


def test_create_access_token():
    """Testa criação de token JWT"""
    token = create_access_token(subject="test_user", purpose="admin")
    
    assert token is not None
    assert isinstance(token, str)
    
    # Decodificar manualmente para verificar
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    assert payload["sub"] == "test_user"
    assert payload["purpose"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_token_valid():
    """Testa decodificação de token válido"""
    token = create_access_token(subject="test_user", purpose="admin")
    token_data = decode_token(token)
    
    assert token_data.sub == "test_user"
    assert token_data.purpose == "admin"


def test_decode_token_expired():
    """Testa token expirado"""
    # Criar token que já está expirado
    expire = datetime.utcnow() - timedelta(hours=1)
    to_encode = {
        "sub": "test_user",
        "purpose": "admin",
        "exp": expire
    }
    
    expired_token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    with pytest.raises(JWTError):
        decode_token(expired_token)


def test_decode_token_invalid_signature():
    """Testa token com assinatura inválida"""
    # Token assinado com chave errada
    wrong_token = jwt.encode(
        {"sub": "test", "purpose": "admin"},
        "wrong-secret-key",
        algorithm="HS256"
    )
    
    with pytest.raises(JWTError):
        decode_token(wrong_token)


def test_token_custom_expiration():
    """Testa token com expiração customizada"""
    token = create_access_token(
        subject="test",
        purpose="admin",
        expiration_hours=1
    )
    
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    
    exp_time = datetime.fromtimestamp(payload["exp"])
    iat_time = datetime.fromtimestamp(payload["iat"])
    
    # Diferença deve ser ~1 hora
    delta = exp_time - iat_time
    assert 3500 < delta.total_seconds() < 3700  # Tolerância de 100s


def test_token_different_purposes():
    """Testa criação de tokens com diferentes propósitos"""
    purposes = ["admin", "readonly", "uploader"]
    
    for purpose in purposes:
        token = create_access_token(subject="test", purpose=purpose)
        token_data = decode_token(token)
        assert token_data.purpose == purpose


def test_token_without_purpose_defaults_to_admin():
    """Testa que token sem purpose usa 'admin' como padrão"""
    # Criar token sem purpose
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "sub": "test_user",
        "exp": expire
    }
    
    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    token_data = decode_token(token)
    assert token_data.purpose == "admin"  # Default value
