from dataclasses import dataclass
import logging
import psutil
import GPUtil
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    temperature: float
    power_consumption: float
    timestamp: datetime


class PerformanceAgent:
    """Agent for monitoring and optimizing system performance"""
    
    def __init__(self):
        self.metrics_history = []
        self.thresholds = {
            "cpu_critical": 90.0,
            "memory_critical": 85.0,
            "gpu_critical": 85.0,
            "temp_critical": 85.0
        }
        
    async def monitor_system(self):
        """Collect system metrics"""
        try:
            # Get CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            
            # Get memory metrics
            memory = psutil.virtual_memory()
            
            # Get GPU metrics
            gpu = GPUtil.getGPUs()[0]  # First GPU
            
            metrics = SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                gpu_usage=gpu.load * 100 if gpu else None,
                temperature=max(psutil.sensors_temperatures()['coretemp'][0].current,
                              gpu.temperature if gpu else 0),
                power_consumption=self._estimate_power_consumption(
                    cpu_freq.current, gpu.load if gpu else 0
                ),
                timestamp=datetime.now()
            )
            
            self.metrics_history.append(metrics)
            await self._check_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            raise
            
    async def optimize_performance(self):
        """Optimize system based on metrics"""
        try:
            metrics = self.metrics_history[-1]
            
            # CPU optimization
            if metrics.cpu_usage > self.thresholds["cpu_critical"]:
                await self._optimize_cpu()
                
            # Memory optimization
            if metrics.memory_usage > self.thresholds["memory_critical"]:
                await self._optimize_memory()
                
            # GPU optimization
            if metrics.gpu_usage and \
               metrics.gpu_usage > self.thresholds["gpu_critical"]:
                await self._optimize_gpu()
                
            # Thermal optimization
            if metrics.temperature > self.thresholds["temp_critical"]:
                await self._optimize_thermal()
                
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise 