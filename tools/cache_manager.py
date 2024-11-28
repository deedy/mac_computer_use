import redis
from typing import Any, Optional, List, Dict
import pickle
import logging
from datetime import timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration"""
    REDIS_URL: str = "redis://localhost:6379/0"
    DEFAULT_TTL: int = 3600  # 1 hour
    BATCH_RESULT_TTL: int = 2592000  # 30 days
    MAX_CACHE_SIZE: int = 10000
    ENABLE_COMPRESSION: bool = True

class CacheManager:
    """Enhanced Redis-based caching with batch support"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis = redis.from_url(self.config.REDIS_URL)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            data = self.redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
            
    async def set(self, 
                  key: str, 
                  value: Any, 
                  expire: Optional[timedelta] = None,
                  nx: bool = False):
        """Set value in cache with optional NX flag"""
        try:
            data = pickle.dumps(value)
            
            if nx:
                success = self.redis.setnx(key, data)
                if not success:
                    return False
                    
            else:
                self.redis.set(key, data)
                
            if expire:
                self.redis.expire(key, expire.total_seconds())
                
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False
            
    async def delete(self, key: str):
        """Delete value from cache"""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            
    async def clear(self):
        """Clear all cached values"""
        try:
            self.redis.flushdb()
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        try:
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.get(key)
            values = pipe.execute()
            
            return {
                key: pickle.loads(value) if value else None
                for key, value in zip(keys, values)
            }
            
        except Exception as e:
            logger.error(f"Batch get failed: {e}")
            return {}
            
    async def batch_set(self, 
                       items: Dict[str, Any],
                       expire: Optional[timedelta] = None):
        """Set multiple values in cache"""
        try:
            pipe = self.redis.pipeline()
            
            for key, value in items.items():
                data = pickle.dumps(value)
                pipe.set(key, data)
                if expire:
                    pipe.expire(key, expire.total_seconds())
                    
            pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Batch set failed: {e}")
            return False 