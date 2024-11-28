from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class BatchRequest:
    """Message batch request"""
    custom_id: str
    params: Dict[str, Any]

@dataclass 
class BatchResult:
    """Message batch result"""
    custom_id: str
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchManager:
    """Manage message batches with Anthropic API"""
    
    def __init__(self, client, cache_manager=None):
        self.client = client
        self.cache = cache_manager
        self.active_batches: Dict[str, datetime] = {}
        
    async def create_batch(self, requests: List[BatchRequest]) -> str:
        """Create a new message batch"""
        try:
            # Create batch through Anthropic API
            batch = await self.client.beta.messages.batches.create(
                requests=[{
                    "custom_id": req.custom_id,
                    "params": {
                        "model": req.params.get("model", "claude-3-sonnet-20240229"),
                        "max_tokens": req.params.get("max_tokens", 1024),
                        "messages": req.params["messages"]
                    }
                } for req in requests]
            )
            
            # Track batch
            self.active_batches[batch.id] = datetime.now()
            
            return batch.id
            
        except Exception as e:
            logger.error(f"Failed to create batch: {e}")
            raise
            
    async def get_batch_results(self, batch_id: str) -> List[BatchResult]:
        """Get results from a processed batch"""
        try:
            # Check cache first
            if self.cache:
                cached = await self.cache.get(f"batch:{batch_id}")
                if cached:
                    return cached
                    
            # Get results from API
            results = []
            async for entry in self.client.beta.messages.batches.results(batch_id):
                if entry.result.type == "succeeded":
                    results.append(BatchResult(
                        custom_id=entry.custom_id,
                        success=True,
                        content=entry.result.message.content[0].text,
                        metadata={
                            "usage": entry.result.message.usage,
                            "model": entry.result.message.model
                        }
                    ))
                else:
                    results.append(BatchResult(
                        custom_id=entry.custom_id,
                        success=False,
                        error=entry.result.error.message
                    ))
                    
            # Cache results
            if self.cache and results:
                await self.cache.set(
                    f"batch:{batch_id}", 
                    results,
                    expire=self.cache.config.BATCH_RESULT_TTL
                )
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to get batch results: {e}")
            raise
            
    async def monitor_batch(self, batch_id: str) -> bool:
        """Monitor batch processing status"""
        try:
            batch = await self.client.beta.messages.batches.retrieve(batch_id)
            return batch.processing_status == "ended"
        except Exception as e:
            logger.error(f"Failed to monitor batch {batch_id}: {e}")
            return False 