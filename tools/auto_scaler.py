from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass
class ScalingPolicy:
    cpu_threshold: float = 80.0
    memory_threshold: float = 80.0
    scale_up_increment: int = 1
    scale_down_increment: int = 1
    cooldown_period: int = 300  # seconds

class AutoScaler:
    """Automatic resource scaling based on usage metrics"""
    
    def __init__(self, policy: ScalingPolicy = ScalingPolicy()):
        self.policy = policy
        self.last_scale_time = 0
        
    async def monitor_and_scale(self):
        """Continuously monitor and scale resources"""
        while True:
            try:
                await self._check_and_scale()
            except Exception as e:
                logger.error(f"Scaling error: {e}")
            await asyncio.sleep(60)  # Check every minute
            
    async def _check_and_scale(self):
        """Check metrics and scale if needed"""
        from .metrics import MetricsCollector
        
        metrics = MetricsCollector()
        cpu_usage = await metrics.get_cpu_usage()
        memory_usage = await metrics.get_memory_usage()
        
        if self._should_scale_up(cpu_usage, memory_usage):
            await self._scale_up()
        elif self._should_scale_down(cpu_usage, memory_usage):
            await self._scale_down() 