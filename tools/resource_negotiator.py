from dataclasses import dataclass
import logging
from typing import Dict, List, Optional
import psutil
import GPUtil
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ResourceRequest:
    """Resource allocation request"""
    agent_id: str
    resource_type: str  # cpu/gpu/memory/io
    amount: float  # Percentage of total resource
    priority: int  # 1-5
    duration: Optional[float]  # Seconds, None for indefinite
    timestamp: datetime


class ResourceNegotiator:
    """Manages resource allocation between agents"""
    
    def __init__(self):
        self.active_allocations: Dict[str, List[ResourceRequest]] = {}
        self.resource_limits = {
            "cpu": 90.0,  # Max 90% CPU allocation
            "gpu": 85.0,  # Max 85% GPU allocation
            "memory": 80.0,  # Max 80% memory allocation
            "io": 70.0  # Max 70% I/O bandwidth
        }
        
    async def request_resources(self, request: ResourceRequest) -> Dict:
        """Handle resource allocation request"""
        try:
            # Check current resource usage
            current_usage = await self._get_resource_usage(request.resource_type)
            
            # Check if request can be fulfilled
            if current_usage + request.amount > self.resource_limits[request.resource_type]:
                # Need to negotiate
                return await self._negotiate_resources(request)
            
            # Allocate resources
            allocation = await self._allocate_resources(request)
            self.active_allocations.setdefault(request.agent_id, []).append(request)
            
            return allocation
            
        except Exception as e:
            logger.error(f"Resource request failed: {e}")
            raise
            
    async def _negotiate_resources(self, request: ResourceRequest) -> Dict:
        """Negotiate resource allocation with other agents"""
        try:
            # Get current allocations for resource type
            current = [
                alloc for allocs in self.active_allocations.values()
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
                    
            # Try allocation again
            if freed >= request.amount:
                return await self._allocate_resources(request)
            else:
                # Return reduced allocation if possible
                reduced_amount = min(request.amount, freed)
                if reduced_amount > 0:
                    request.amount = reduced_amount
                    return await self._allocate_resources(request)
                    
            return {
                "success": False,
                "reason": "Insufficient resources",
                "available": freed
            }
            
        except Exception as e:
            logger.error(f"Resource negotiation failed: {e}")
            raise 