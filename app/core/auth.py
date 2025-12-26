from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenData
from typing import Optional


def create_access_token(
    subject: str,
    purpose: str = "admin",
    expiration_hours: Optional[int] = None
) -> str:
    """
    Cria um token JWT.
    
    Args:
        subject: Identificador do token (ex: "admin_user")
        purpose: Propósito ("admin", "readonly", "uploader")
        expiration_hours: Horas até expirar (default: config)
    
    Returns:
        Token JWT string
    """
    if expiration_hours is None:
        expiration_hours = settings.JWT_EXPIRATION_HOURS
    
    expire = datetime.utcnow() + timedelta(hours=expiration_hours)
    
    to_encode = {
        "sub": subject,
        "purpose": purpose,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT string
    
    Returns:
        TokenData com informações do token
    
    Raises:
        JWTError: Se token for inválido ou expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        sub: str = payload.get("sub")
        if sub is None:
            raise JWTError("Token sem 'sub' claim")
        
        purpose: str = payload.get("purpose", "admin")
        
        return TokenData(sub=sub, purpose=purpose)
    
    except JWTError as e:
        raise e
