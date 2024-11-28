"""Middleware module for caching, rate limiting, and monitoring."""

import time
import asyncio
import json
from typing import Any, Optional, Dict, Callable
from redis.asyncio import Redis
from datetime import datetime
from functools import wraps
from loguru import logger
from .config import settings


def serialize_value(value: Any) -> str:
    """Serialize value for Redis storage."""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)


def deserialize_value(value: Optional[str]) -> Any:
    """Deserialize value from Redis storage."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return value


class RedisManager:
    """Redis connection and health management."""
    
    _instance: Optional['RedisManager'] = None
    _client: Optional[Redis] = None
    _lock: Optional[asyncio.Lock] = None
    _health_check_interval: int = 30
    _last_health_check: float = 0
    _max_retries: int = 3
    _retry_delay: float = 0.1
    _loop: Optional[asyncio.AbstractEventLoop] = None
    
    def __new__(cls) -> 'RedisManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = None
            cls._instance._loop = None
        return cls._instance
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._lock is None:
            self._lock = asyncio.Lock()
            
        # Store the event loop
        self._loop = asyncio.get_running_loop()
            
        async with self._lock:
            if self._client is None:
                try:
                    self._client = Redis.from_url(
                        settings.REDIS_URL,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    # Test connection
                    await self._client.ping()
                    logger.info("Redis connection established")
                except Exception as e:
                    logger.warning(
                        f"Failed to connect to Redis: {e}. Using in-memory storage."
                    )
                    self._client = None
    
    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client instance."""
        return self._client
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        if not self._client:
            return False
            
        current_time = time.time()
        if current_time - self._last_health_check < self._health_check_interval:
            return True
            
        try:
            await self._client.ping()
            self._last_health_check = current_time
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
            
    async def cleanup(self) -> None:
        """Cleanup Redis connection."""
        if self._lock is None:
            self._lock = asyncio.Lock()
            
        async with self._lock:
            if self._client:
                try:
                    await self._client.close()
                except Exception as e:
                    logger.error(f"Redis cleanup error: {e}")
                finally:
                    self._client = None
                    self._loop = None


class CacheManager:
    """Cache management with Redis backend."""
    
    def __init__(self, ttl: int = 3600):
        """Initialize cache manager."""
        self.redis_manager = RedisManager()
        self.ttl = ttl
        self._local_cache: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        # Try Redis first
        if self.redis_manager.client and self.redis_manager._loop and not self.redis_manager._loop.is_closed():
            try:
                value = await self.redis_manager.client.get(key)
                return deserialize_value(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to local cache
        return self._local_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set cached value."""
        ttl = ttl or self.ttl
        
        # Serialize value
        serialized_value = serialize_value(value)
        
        # Try Redis first
        if self.redis_manager.client and self.redis_manager._loop and not self.redis_manager._loop.is_closed():
            try:
                await self.redis_manager.client.set(
                    key,
                    serialized_value,
                    ex=ttl
                )
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to local cache
        self._local_cache[key] = value
        return True


class RateLimiter:
    """Rate limiting with Redis backend."""
    
    def __init__(self, limit: int = 60):
        """Initialize rate limiter."""
        self.redis_manager = RedisManager()
        self.limit = limit
        self._local_limits: Dict[str, Dict[float, int]] = {}
    
    async def check_rate_limit(self, key: str = "default") -> bool:
        """Check if rate limit is exceeded."""
        # Try Redis first
        if self.redis_manager.client and self.redis_manager._loop and not self.redis_manager._loop.is_closed():
            try:
                current_time = int(time.time())
                window_key = f"ratelimit:{key}:{current_time // 60}"
                
                async with self.redis_manager._lock:
                    count = await self.redis_manager.client.incr(window_key)
                    if count == 1:
                        await self.redis_manager.client.expire(window_key, 60)
                    return count <= self.limit
                    
            except Exception as e:
                logger.error(f"Redis rate limit error: {e}")
        
        # Fallback to local rate limiting
        current_time = time.time()
        if key not in self._local_limits:
            self._local_limits[key] = {}
            
        # Clean up old entries
        self._local_limits[key] = {
            ts: count for ts, count in self._local_limits[key].items()
            if current_time - ts < 60
        }
        
        # Check current count
        current_count = sum(self._local_limits[key].values())
        if current_count >= self.limit:
            return False
            
        # Increment counter
        self._local_limits[key][current_time] = 1
        return True


def rate_limit(key_prefix: str = ""):
    """Rate limiting decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            rate_limiter = RateLimiter()
            key = f"{key_prefix}:{func.__name__}"
            
            if not await rate_limiter.check_rate_limit(key):
                raise Exception("Rate limit exceeded")
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache(ttl: int = 3600):
    """Caching decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_manager = CacheManager(ttl)
            key = f"cache:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = await cache_manager.get(key)
            if cached is not None:
                return cached
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def retry(max_retries: int = 3, delay: float = 0.1):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                        
            raise last_error
        return wrapper
    return decorator


def audit_trail(func: Callable) -> Callable:
    """Audit trail decorator."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        success = False
        error = None
        
        try:
            result = await func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration = time.time() - start_time
            
            # Log audit trail
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs),
                "duration": duration,
                "success": success,
                "error": error
            }
            
            logger.info(f"Audit trail: {audit_data}")
            
    return wrapper 