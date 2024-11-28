import psutil
from dataclasses import dataclass

@dataclass
class MemoryStats:
    total: int
    available: int
    used: int
    cached: int
    swap_used: int

class MemoryManager:
    """Advanced memory management and optimization"""
    
    async def get_memory_stats(self) -> MemoryStats:
        """Get detailed memory statistics"""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return MemoryStats(
            total=vm.total,
            available=vm.available,
            used=vm.used,
            cached=vm.cached,
            swap_used=swap.used
        )
    
    async def optimize_memory(self):
        """Optimize memory usage"""
        # Clear filesystem cache
        await self.shell("sudo purge")
        
        # Optimize swap
        await self.shell("""
            sudo sysctl -w vm.swappiness=10
            sudo sysctl -w vm.vfs_cache_pressure=50
        """) 