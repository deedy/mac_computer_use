from dataclasses import dataclass
import psutil
import logging
from typing import Dict
import GPUtil
from Foundation import NSProcessInfo

logger = logging.getLogger(__name__)

@dataclass
class ThermalProfile:
    """Thermal profile for 16" MacBook Pro"""
    cpu_tdp: int = 45  # Base TDP for i9-9880H
    gpu_tdp: int = 50  # TDP for 5600M
    max_cpu_temp: float = 100.0
    max_gpu_temp: float = 95.0
    target_cpu_temp: float = 85.0
    target_gpu_temp: float = 80.0

class HardwareOptimizer:
    """Hardware-specific optimizations for 16" MacBook Pro"""
    
    def __init__(self):
        self.thermal_profile = ThermalProfile()
        self.power_info = NSProcessInfo.processInfo()
        self.gpu_info = GPUtil.getGPUs()[0]  # AMD 5600M
        
    async def optimize_for_display_count(self, display_count: int):
        """Optimize based on number of connected displays"""
        try:
            if display_count > 1:
                # Multiple display optimization for 5600M
                await self._configure_multi_display()
            else:
                # Single display optimization
                await self._configure_single_display()
                
        except Exception as e:
            logger.error(f"Display optimization failed: {e}")
            raise
            
    async def optimize_for_metal_workload(self):
        """Optimize for Metal compute workloads on 5600M"""
        try:
            # Configure HBM2 memory for compute
            await self._optimize_hbm2_memory()
            
            # Set optimal Metal performance mode
            await self._set_metal_performance_mode()
            
            # Configure memory bandwidth
            await self._optimize_memory_bandwidth()
            
        except Exception as e:
            logger.error(f"Metal optimization failed: {e}")
            raise
            
    async def _configure_multi_display(self):
        """Configure for multiple display output"""
        try:
            # Optimize HBM2 memory bandwidth allocation
            await self._set_memory_bandwidth_mode("display_optimized")
            
            # Adjust power limits for sustained performance
            await self._set_power_limits(
                cpu_tdp=40,  # Reduce CPU power for GPU headroom
                gpu_tdp=50   # Max GPU power for displays
            )
            
            # Configure display controller
            await self._configure_display_controller(
                memory_reserved=2048,  # Reserve 2GB for displays
                refresh_sync=True      # Sync refresh rates
            )
            
        except Exception as e:
            logger.error(f"Multi-display configuration failed: {e}")
            raise
            
    async def _optimize_hbm2_memory(self):
        """Optimize HBM2 memory configuration"""
        try:
            # Configure HBM2 power states
            await self._set_hbm2_power_state("performance")
            
            # Set memory clock speeds
            await self._set_memory_clocks(
                base_clock=1000,    # MHz
                boost_clock=1500    # MHz
            )
            
            # Configure memory controller
            await self._set_memory_controller(
                page_size=4096,     # 4K pages
                prefetch=True,      # Enable prefetching
                caching="write_back"
            )
            
        except Exception as e:
            logger.error(f"HBM2 optimization failed: {e}")
            raise
            
    async def optimize_for_battery(self, target_hours: float):
        """Optimize for battery life target"""
        try:
            current_power = self.power_info.thermalState()
            
            if target_hours > 4:
                # Long battery life mode
                await self._set_power_profile("battery_optimized")
                await self._configure_cpu_scheduler("efficiency")
                await self._set_gpu_power_state("low")
                
            elif target_hours > 2:
                # Balanced battery mode
                await self._set_power_profile("balanced")
                await self._configure_cpu_scheduler("balanced")
                await self._set_gpu_power_state("balanced")
                
            else:
                # Performance mode with power awareness
                await self._set_power_profile("performance")
                await self._configure_cpu_scheduler("performance")
                await self._set_gpu_power_state("auto")
                
        except Exception as e:
            logger.error(f"Battery optimization failed: {e}")
            raise
            
    async def optimize_for_thermal_headroom(self):
        """Optimize based on available thermal headroom"""
        try:
            cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
            gpu_temp = self.gpu_info.temperature
            
            cpu_headroom = self.thermal_profile.max_cpu_temp - cpu_temp
            gpu_headroom = self.thermal_profile.max_gpu_temp - gpu_temp
            
            if cpu_headroom < 10 or gpu_headroom < 10:
                # Critical thermal situation
                await self._emergency_thermal_mitigation()
            elif cpu_headroom < 20 or gpu_headroom < 15:
                # Approaching thermal limits
                await self._proactive_thermal_management()
            else:
                # Good thermal headroom
                await self._optimize_for_performance()
                
        except Exception as e:
            logger.error(f"Thermal optimization failed: {e}")
            raise
            
    async def _emergency_thermal_mitigation(self):
        """Emergency thermal management"""
        try:
            # Immediate actions to reduce temperatures
            await self._set_cpu_power_limit(25)  # Reduce to 25W
            await self._set_gpu_power_limit(35)  # Reduce to 35W
            await self._set_fan_speed("max")
            await self._throttle_background_processes()
            
        except Exception as e:
            logger.error(f"Emergency thermal mitigation failed: {e}")
            raise
            
    async def _optimize_memory_bandwidth(self):
        """Optimize memory bandwidth allocation"""
        try:
            # Configure memory controller settings
            await self._set_memory_controller_mode("compute")
            
            # Optimize DDR4-2667 settings
            await self._configure_memory_timings(
                cas_latency=15,
                tras=35,
                trcd=15,
                trp=15,
                command_rate=1
            )
            
            # Configure memory power states
            await self._set_memory_power_state("performance")
            
        except Exception as e:
            logger.error(f"Memory bandwidth optimization failed: {e}")
            raise 