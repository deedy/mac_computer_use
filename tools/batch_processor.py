from typing import List, Dict, Any
from dataclasses import dataclass
from anthropic import Anthropic
from .config import settings

@dataclass
class BatchRequest:
    messages: List[Dict[str, Any]]
    model: str
    max_tokens: int = 1024

class BatchProcessor:
    """Handles batch message processing using Anthropic's batch API"""
    
    def __init__(self, client: Anthropic):
        self.client = client
        
    async def process_batch(self, batch: BatchRequest):
        """Process a batch of messages in parallel"""
        response = await self.client.messages.batch.create(
            requests=[{
                "model": batch.model,
                "max_tokens": batch.max_tokens,
                "messages": msg
            } for msg in batch.messages]
        )
        return response
    
    async def process_chat_history(self, session_id: str, chunk_size: int = 5):
        """Process chat history in batches"""
        from .chat_history import SQLiteChatHistory
        
        history = SQLiteChatHistory(session_id)
        messages = history.messages
        
        # Process in chunks
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            batch = BatchRequest(
                messages=chunk,
                model=settings.DEFAULT_MODEL
            )
            await self.process_batch(batch) 