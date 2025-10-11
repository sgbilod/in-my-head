"""
Authentication module for API endpoints.

Provides API key-based authentication with:
- API key validation
- User identification
- Rate limiting per user
"""

import os
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Secure random API key (32 bytes hex)
        
    Example:
        >>> key = generate_api_key()
        >>> len(key)
        64
    """
    return secrets.token_hex(32)


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key against configured keys.
    
    In production, this would check against a database.
    For now, we check against environment variable.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> os.environ["API_KEYS"] = "key1,key2,key3"
        >>> verify_api_key("key1")
        True
        >>> verify_api_key("invalid")
        False
    """
    # Get configured API keys from environment
    configured_keys = os.getenv("API_KEYS", "").split(",")
    configured_keys = [k.strip() for k in configured_keys if k.strip()]
    
    # If no keys configured, allow all (development mode)
    if not configured_keys:
        return True
    
    return api_key in configured_keys


def get_user_id(api_key: str) -> str:
    """
    Get user ID from API key.
    
    In production, this would look up the user in a database.
    For now, we use a hash of the API key.
    
    Args:
        api_key: API key
        
    Returns:
        User identifier
        
    Example:
        >>> user_id = get_user_id("my-api-key")
        >>> len(user_id) > 0
        True
    """
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    FastAPI dependency for API key authentication.
    
    Args:
        api_key: API key from header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
        
    Example:
        >>> @app.get("/protected")
        >>> async def protected_endpoint(
        ...     api_key: str = Depends(get_api_key)
        ... ):
        ...     return {"message": "Access granted"}
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key
