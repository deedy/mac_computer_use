from dataclasses import dataclass
from typing import Dict
import psutil
import logging
from datetime import datetime
import asyncio
import GPUtil
import py3nvml

logger = logging.getLogger(__name__)

@dataclass
class MacBookProConfig:
    """MacBook Pro 16-inch 2019 specific configuration"""
    cpu_model: str = "Intel Core i9-9880H"
    base_clock: float = 2.4  # GHz
    max_clock: float = 5.0   # GHz
    gpu_model: str = "AMD Radeon Pro 5600M"
    gpu_memory: int = 8192   # MB
    ram_size: int = 64       # GB
    ram_speed: int = 2667    # MHz

class PerformanceOptimizer:
    """Optimized for 2019 16" MacBook Pro with i9 and 5600M"""
    
    def __init__(self):
        self.config = MacBookProConfig()
        self.performance_modes = {
            "eco": {
                "cpu_power": 0.6,  # 60% max power
                "gpu_power": 0.5,  # Conservative for 5600M
                "fan_speed": "quiet",
                "max_temp": 75.0   # °C
            },
            "balanced": {
                "cpu_power": 0.8,
                "gpu_power": 0.7,
                "fan_speed": "auto",
                "max_temp": 85.0
            },
            "performance": {
                "cpu_power": 1.0,
                "gpu_power": 1.0,
                "fan_speed": "max",
                "max_temp": 95.0
            },
            "gpu_intensive": {  # Special mode for 5600M workloads
                "cpu_power": 0.7,
                "gpu_power": 1.0,
                "fan_speed": "max",
                "max_temp": 90.0,
                "gpu_memory_target": 0.9  # 90% GPU memory utilization target
            }
        }
        
    async def optimize_for_workload(self, workload_type: str):
        """Optimize system for specific workload types"""
        try:
            if workload_type == "gpu_compute":
                # Optimize for AMD 5600M compute tasks
                await self._optimize_gpu_compute()
            elif workload_type == "cpu_intensive":
                # Optimize for i9 processor
                await self._optimize_cpu_intensive()
            elif workload_type == "balanced":
                # Balance between CPU and 5600M GPU
                await self._optimize_balanced()
                
        except Exception as e:
            logger.error(f"Workload optimization failed: {e}")
            raise
            
    async def _optimize_gpu_compute(self):
        """Optimize for AMD 5600M GPU compute workloads"""
        try:
            # Set GPU fan curve aggressive
            await self._set_gpu_fan_curve("aggressive")
            
            # Optimize GPU memory allocation
            await self._optimize_gpu_memory()
            
            # Ensure CPU doesn't thermal throttle GPU
            await self._manage_cpu_for_gpu()
            
        except Exception as e:
            logger.error(f"GPU compute optimization failed: {e}")
            raise
            
    async def _optimize_cpu_intensive(self):
        """Optimize for i9-9880H CPU intensive workloads"""
        try:
            # Configure Intel power management
            await self._set_intel_power_profile("performance")
            
            # Optimize Turbo Boost behavior
            await self._configure_turbo_boost()
            
            # Set aggressive fan curve for CPU
            await self._set_cpu_fan_curve("aggressive")
            
        except Exception as e:
            logger.error(f"CPU optimization failed: {e}")
            raise
            
    async def _optimize_gpu_memory(self):
        """Optimize AMD 5600M 8GB HBM2 memory"""
        try:
            # Get current GPU memory usage
            gpu = GPUtil.getGPUs()[0]  # AMD 5600M
            
            if gpu.memoryUtil > 0.9:  # Over 90% memory utilization
                # Attempt to free up GPU memory
                await self._clear_gpu_memory_pressure()
                
        except Exception as e:
            logger.error(f"GPU memory optimization failed: {e}")
            raise
            
    async def _manage_cpu_for_gpu(self):
        """Manage CPU to prevent GPU thermal throttling"""
        try:
            # Get CPU and GPU temperatures
            cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
            gpu_temp = GPUtil.getGPUs()[0].temperature
            
            if gpu_temp > 85 and cpu_temp > 80:
                # Reduce CPU power to help GPU thermals
                await self._reduce_cpu_power()
                
        except Exception as e:
            logger.error(f"CPU-GPU thermal management failed: {e}")
            raise
            
    async def _configure_turbo_boost(self):
        """Configure Intel Turbo Boost for i9-9880H"""
        try:
            # Check current temperature
            cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
            
            if cpu_temp < 85:
                # Allow full Turbo Boost
                await self._set_turbo_boost(enabled=True)
            else:
                # Limit Turbo Boost to prevent thermal throttling
                await self._set_turbo_boost(enabled=True, limit_ratio=0.8)
                
        except Exception as e:
            logger.error(f"Turbo Boost configuration failed: {e}")
            raise