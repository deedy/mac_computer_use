import psutil
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import logging
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_used_gb: float
    memory_free_gb: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float

class PerformanceMonitor:
    """Monitor system performance metrics"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self._prev_disk_io = psutil.disk_io_counters()
        self._prev_net_io = psutil.net_io_counters()
        
    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU & Memory
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = (disk_io.read_bytes - self._prev_disk_io.read_bytes) / 1024**2
            disk_write = (disk_io.write_bytes - self._prev_disk_io.write_bytes) / 1024**2
            self._prev_disk_io = disk_io
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent = (net_io.bytes_sent - self._prev_net_io.bytes_sent) / 1024**2
            net_recv = (net_io.bytes_recv - self._prev_net_io.bytes_recv) / 1024**2
            self._prev_net_io = net_io
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_used_gb=memory.used / 1024**3,
                memory_free_gb=memory.available / 1024**3,
                disk_read_mb=disk_read,
                disk_write_mb=disk_write,
                network_sent_mb=net_sent,
                network_recv_mb=net_recv
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise
            
    def get_metrics_history(self, 
                          limit: Optional[int] = None,
                          metric_type: Optional[str] = None) -> List[SystemMetrics]:
        """Get historical metrics data"""
        metrics = self.metrics_history
        
        if metric_type:
            metrics = [
                m for m in metrics 
                if hasattr(m, metric_type)
            ]
            
        if limit:
            metrics = metrics[-limit:]
            
        return metrics 