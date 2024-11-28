from dataclasses import dataclass
from typing import Dict, Any, Optional
import asyncio
import json
import logging
import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Inter-agent communication message"""
    type: str  # task/result/status
    data: Dict[str, Any]
    sender: str
    recipient: Optional[str] = None

class AgentProtocol:
    """Handles communication between agents"""
    
    def __init__(self, agent_id: str, port: int = 5555):
        self.agent_id = agent_id
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(f"tcp://localhost:{port}")
        
    async def send_message(self, message: Message):
        """Send message to another agent"""
        try:
            await self.socket.send_multipart([
                message.recipient.encode() if message.recipient else b"",
                json.dumps({
                    "type": message.type,
                    "data": message.data,
                    "sender": self.agent_id
                }).encode()
            ])
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
            
    async def receive_message(self) -> Optional[Message]:
        """Receive message from another agent"""
        try:
            recipient, data = await self.socket.recv_multipart()
            message_data = json.loads(data.decode())
            
            return Message(
                type=message_data["type"],
                data=message_data["data"],
                sender=message_data["sender"],
                recipient=recipient.decode() if recipient else None
            )
            
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise 