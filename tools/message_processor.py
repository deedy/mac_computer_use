from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from .batch_manager import BatchManager, BatchRequest
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Process messages with batching and caching"""
    
    def __init__(self, 
                 client,
                 batch_size: int = 100,
                 max_wait: float = 5.0):
        self.client = client
        self.batch_manager = BatchManager(client)
        self.cache = CacheManager()
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.pending_messages: List[BatchRequest] = []
        self.processing = False
        
    async def process_message(self, message: Dict[str, Any]) -> str:
        """Add message to batch queue"""
        request = BatchRequest(
            custom_id=f"msg_{datetime.now().timestamp()}",
            params=message
        )
        
        self.pending_messages.append(request)
        
        # Start processing if needed
        if not self.processing:
            asyncio.create_task(self._process_batches())
            
        return request.custom_id
        
    async def _process_batches(self):
        """Process pending messages in batches"""
        self.processing = True
        
        try:
            while self.pending_messages:
                # Get next batch
                batch = self.pending_messages[:self.batch_size]
                self.pending_messages = self.pending_messages[self.batch_size:]
                
                # Create and monitor batch
                batch_id = await self.batch_manager.create_batch(batch)
                
                while not await self.batch_manager.monitor_batch(batch_id):
                    await asyncio.sleep(1.0)
                    
                # Get and cache results
                results = await self.batch_manager.get_batch_results(batch_id)
                
                # Cache individual message results
                await self.cache.batch_set(
                    {r.custom_id: r for r in results},
                    expire=self.cache.config.DEFAULT_TTL
                )
                
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            
        finally:
            self.processing = False
            
    async def get_result(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get processed message result"""
        try:
            result = await self.cache.get(message_id)
            if result:
                return {
                    "success": result.success,
                    "content": result.content,
                    "error": result.error,
                    "metadata": result.metadata
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None 