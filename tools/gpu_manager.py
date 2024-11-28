from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class GPUStats:
    utilization: float
    memory_used: int
    temperature: float
    power_draw: float

class GPUManager:
    """Advanced GPU management and monitoring"""
    
    async def get_gpu_stats(self) -> Optional[GPUStats]:
        """Get current GPU statistics"""
        try:
            result = await self.shell("ioreg -r -c IOAccelerator")
            data = json.loads(result.output)
            
            # Parse GPU stats from ioreg output
            stats = GPUStats(
                utilization=data.get('GPUUtilization', 0.0),
                memory_used=data.get('UsedGPUMemory', 0),
                temperature=data.get('GPUTemperature', 0.0),
                power_draw=data.get('GPUPowerDraw', 0.0)
            )
            return stats
        except:
            return None
            
    async def optimize_for_task(self, task_type: str):
        """Optimize GPU settings for specific tasks"""
        if task_type == "ml":
            await self.shell("""
                defaults write com.apple.AMDRadeonX6000HWServices MLPerformanceMode -bool true
                defaults write com.apple.AMDRadeonX6000HWServices PowerSavingsMode -bool false
            """)
        elif task_type == "graphics":
            await self.shell("""
                defaults write com.apple.AMDRadeonX6000HWServices GraphicsPerformanceMode -bool true
                defaults write com.apple.AMDRadeonX6000HWServices PowerSavingsMode -bool false
            """) 