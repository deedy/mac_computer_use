import psutil
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_used_gb: float
    memory_free_gb: float
    memory_cached_gb: float
    memory_swap_gb: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float

class ActivityMonitor:
    """Native macOS system monitoring"""
    
    def __init__(self):
        self._prev_disk_io = psutil.disk_io_counters()
        self._prev_net_io = psutil.net_io_counters()
        
    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        try:
            # Get memory info
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Get disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = (
                disk_io.read_bytes - self._prev_disk_io.read_bytes
            ) / 1024**2
            disk_write = (
                disk_io.write_bytes - self._prev_disk_io.write_bytes
            ) / 1024**2
            self._prev_disk_io = disk_io
            
            # Get network I/O
            net_io = psutil.net_io_counters()
            net_sent = (
                net_io.bytes_sent - self._prev_net_io.bytes_sent
            ) / 1024**2
            net_recv = (
                net_io.bytes_recv - self._prev_net_io.bytes_recv
            ) / 1024**2
            self._prev_net_io = net_io
            
            return SystemMetrics(
                cpu_percent=psutil.cpu_percent(),
                memory_used_gb=mem.used / 1024**3,
                memory_free_gb=mem.available / 1024**3,
                memory_cached_gb=mem.cached / 1024**3,
                memory_swap_gb=swap.used / 1024**3,
                disk_read_mb=disk_read,
                disk_write_mb=disk_write,
                network_sent_mb=net_sent,
                network_recv_mb=net_recv
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise