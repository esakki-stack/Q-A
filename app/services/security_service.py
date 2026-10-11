"""
Authentication and Security Services
JWT-based auth, API keys, password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import secrets
import logging

# Handle optional dependencies
try:
    from passlib.context import CryptContext
except ImportError:
    CryptContext = None

try:
    from jose import JWTError, jwt
except ImportError:
    JWTError = None
    jwt = None

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


class SecurityService:
    """Authentication and security service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: Dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token encoding error: {e}")
            raise

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Token verification error: {e}")
            return None

    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_token(user_id: str) -> str:
        """Generate authentication token for user"""
        data = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return SecurityService.create_access_token(data)
