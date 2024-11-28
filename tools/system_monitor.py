from dataclasses import dataclass
from typing import Dict, List, Optional
import psutil
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Comprehensive system metrics"""
    cpu_metrics: Dict[str, float]
    memory_metrics: Dict[str, float]
    disk_metrics: Dict[str, float]
    network_metrics: Dict[str, float]
    power_metrics: Dict[str, float]
    thermal_metrics: Dict[str, float]
    timestamp: datetime

class SystemMonitor:
    """Enhanced system monitoring service"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.alert_thresholds = {
            "cpu_temp": 85.0,  # °C
            "memory_pressure": 0.8,  # 80%
            "disk_usage": 0.9,  # 90%
            "power_draw": 35.0  # Watts
        }
        
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        while True:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep last hour of metrics
                if len(self.metrics_history) > 3600:  # 1 hour at 1s intervals
                    self.metrics_history.pop(0)
                    
                # Check for alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(1)  # 1 second interval
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_metrics = {
                "usage": psutil.cpu_percent(interval=0.1),
                "frequency": psutil.cpu_freq().current,
                "load_avg": psutil.getloadavg()[0]
            }
            
            # Memory metrics
            mem = psutil.virtual_memory()
            memory_metrics = {
                "used_percent": mem.percent,
                "available": mem.available / (1024**3),  # GB
                "pressure": self._calculate_memory_pressure()
            }
            
            # Disk metrics
            disk_metrics = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_metrics[partition.mountpoint] = {
                        "used_percent": usage.percent,
                        "io_counters": psutil.disk_io_counters(perdisk=True)
                    }
                except Exception:
                    continue
                    
            # Network metrics
            net = psutil.net_io_counters()
            network_metrics = {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
                "packets_sent": net.packets_sent,
                "packets_recv": net.packets_recv
            }
            
            return SystemMetrics(
                cpu_metrics=cpu_metrics,
                memory_metrics=memory_metrics,
                disk_metrics=disk_metrics,
                network_metrics=network_metrics,
                power_metrics=self._get_power_metrics(),
                thermal_metrics=self._get_thermal_metrics(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            raise
            
    def _calculate_memory_pressure(self) -> float:
        """Calculate memory pressure score (0-1)"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Factors to consider
            mem_used_factor = mem.percent / 100
            swap_used_factor = swap.percent / 100 if swap.total > 0 else 0
            
            # Calculate pressure score
            pressure = (mem_used_factor * 0.7) + (swap_used_factor * 0.3)
            return min(pressure, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Memory pressure calculation failed: {e}")
            return 0.0 