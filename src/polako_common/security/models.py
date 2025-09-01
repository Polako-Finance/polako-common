"""Security models for authentication and authorization"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # subject (user ID)
    exp: int  # expiration time
    iat: int  # issued at
    iss: str  # issuer
    aud: str  # audience
    scopes: List[str] = []
    tenant_id: Optional[str] = None
    merchant_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class User(BaseModel):
    """User model for authentication"""
    id: str
    email: str
    name: str
    scopes: List[str] = []
    tenant_id: Optional[str] = None
    merchant_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
