from pydantic import BaseModel
from typing import Optional


class TokenData(BaseModel):
    """Dados extraídos do token JWT"""
    sub: str  # Subject (identificador do token)
    purpose: Optional[str] = "admin"  # Propósito do token


class TokenCreate(BaseModel):
    """Modelo para criar novo token via API (futuro)"""
    sub: str
    purpose: str = "admin"
    expiration_hours: Optional[int] = None
