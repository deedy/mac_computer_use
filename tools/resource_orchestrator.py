from dataclasses import dataclass
import logging
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ResourceAllocation:
    """Resource allocation details"""
    resource_type: str  # cpu/gpu/memory
    amount: float  # Percentage
    priority: int  # 1-5
    duration: float  # Seconds


class ResourceOrchestrator:
    """Orchestrates resource allocation between agents"""
    
    def __init__(self):
        self.allocations: Dict[str, List[ResourceAllocation]] = {}
        self.resource_limits = {
            "cpu": 90.0,  # Max 90% allocation
            "gpu": 85.0,  # Max 85% allocation
            "memory": 80.0  # Max 80% allocation
        }
        
    async def request_resources(self, agent_id: str, request: ResourceAllocation):
        """Handle resource allocation request"""
        try:
            # Check current allocations
            current_usage = self._get_current_usage(request.resource_type)
            
            # Check if request can be fulfilled
            if current_usage + request.amount > self.resource_limits[request.resource_type]:
                # Need to negotiate
                return await self._negotiate_resources(request)
                
            # Allocate resources
            self.allocations.setdefault(agent_id, []).append(request)
            
            return {
                "success": True,
                "allocated": request.amount,
                "duration": request.duration
            }
            
        except Exception as e:
            logger.error(f"Resource request failed: {e}")
            raise
            
    async def _negotiate_resources(self, request: ResourceAllocation):
        """Negotiate resource allocation with other agents"""
        try:
            # Get current allocations for resource type
            current = [
                alloc for allocs in self.allocations.values()
                for alloc in allocs
                if alloc.resource_type == request.resource_type
            ]
            
            # Sort by priority (lower number = higher priority)
            current.sort(key=lambda x: x.priority)
            
            # Try to free up resources
            freed = 0.0
            for alloc in current:
                if alloc.priority > request.priority:
                    # Can preempt this allocation
                    freed += alloc.amount
                    await self._deallocate_resources(alloc)
                    
                if freed >= request.amount:
                    break
                    
            return {
                "success": freed >= request.amount,
                "allocated": min(request.amount, freed),
                "reason": "Negotiated allocation"
            }
            
        except Exception as e:
            logger.error(f"Resource negotiation failed: {e}")
            raise 