"""
Rate limiting module for API endpoints.

Provides:
- Token bucket algorithm
- Per-user rate limiting
- Redis-backed storage
- Configurable limits
"""

import time
from typing import Optional
from functools import wraps
import redis
from fastapi import HTTPException, status

from .auth import get_user_id


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Limits requests per user using Redis for distributed rate limiting.
    
    Attributes:
        redis_client: Redis client for storage
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 2,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
            
        Example:
            >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(
        self,
        user_id: str,
        cost: int = 1
    ) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: User identifier
            cost: Request cost (default: 1)
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
            
        Example:
            >>> limiter = RateLimiter(max_requests=10, window_seconds=60)
            >>> allowed, retry_after = limiter.is_allowed("user123")
            >>> if allowed:
            ...     # Process request
            ...     pass
            ... else:
            ...     # Reject with retry_after
            ...     pass
        """
        key = f"rate_limit:{user_id}"
        now = int(time.time())
        window_start = now - self.window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry
        pipe.expire(key, self.window_seconds)
        
        # Execute pipeline
        results = pipe.execute()
        current_requests = results[1]
        
        # Check if allowed
        if current_requests < self.max_requests:
            return True, None
        else:
            # Calculate retry after
            oldest_entry = self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_entry:
                oldest_time = int(oldest_entry[0][1])
                retry_after = self.window_seconds - (now - oldest_time)
                return False, max(1, retry_after)
            else:
                return False, self.window_seconds
    
    def reset(self, user_id: str):
        """
        Reset rate limit for user.
        
        Args:
            user_id: User identifier
            
        Example:
            >>> limiter = RateLimiter()
            >>> limiter.reset("user123")
        """
        key = f"rate_limit:{user_id}"
        self.redis_client.delete(key)
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining requests for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of remaining requests
            
        Example:
            >>> limiter = RateLimiter(max_requests=10)
            >>> remaining = limiter.get_remaining("user123")
            >>> print(f"Remaining: {remaining}/10")
        """
        key = f"rate_limit:{user_id}"
        now = int(time.time())
        window_start = now - self.window_seconds
        
        # Remove old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_requests = self.redis_client.zcard(key)
        
        return max(0, self.max_requests - current_requests)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        )
    
    return _rate_limiter


def rate_limit(cost: int = 1):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        cost: Request cost (default: 1)
        
    Example:
        >>> @app.post("/upload")
        >>> @rate_limit(cost=5)
        >>> async def upload_document(
        ...     api_key: str = Depends(get_api_key)
        ... ):
        ...     # Process upload
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, api_key: str, **kwargs):
            # Get user ID from API key
            user_id = get_user_id(api_key)
            
            # Check rate limit
            limiter = get_rate_limiter()
            allowed, retry_after = limiter.is_allowed(user_id, cost)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )
            
            # Call endpoint
            return await func(*args, api_key=api_key, **kwargs)
        
        return wrapper
    
    return decorator


# Import os for environment variables
import os
