import redis.asyncio as redis
from functools import wraps
import pickle

class CacheManager:
    """Redis-based caching for improved performance"""
    
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
    async def cache_result(self, key: str, ttl: int = 3600):
        """Cache decorator for expensive operations"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = f"{key}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached = await self.redis.get(cache_key)
                if cached:
                    return pickle.loads(cached)
                    
                # Execute and cache
                result = await func(*args, **kwargs)
                await self.redis.setex(
                    cache_key,
                    ttl,
                    pickle.dumps(result)
                )
                return result
            return wrapper
        return decorator 