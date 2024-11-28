from dataclasses import dataclass
import logging
from typing import Dict, List
import psutil
import GPUtil

logger = logging.getLogger(__name__)


@dataclass
class DeviceCapabilities:
    """Device hardware capabilities"""
    name: str
    compute_units: int
    memory: int
    memory_type: str
    memory_bandwidth: float
    supports_ane: bool


class DeviceCoordinator:
    """Coordinates workload distribution across devices"""
    
    def __init__(self):
        self.devices = self._detect_devices()
        self.workload_assignments = {}
        
    async def assign_workload(self, workload_type: str, requirements: Dict):
        """Assign workload to optimal device"""
        try:
            # Get device capabilities
            available_devices = {
                name: caps for name, caps in self.devices.items()
                if self._meets_requirements(caps, requirements)
            }
            
            if not available_devices:
                raise ValueError("No suitable device found")
                
            # Select optimal device
            device = await self._select_optimal_device(
                available_devices,
                workload_type,
                requirements
            )
            
            # Register assignment
            self.workload_assignments[workload_type] = device
            
            return {
                "device": device.name,
                "compute_units": device.compute_units,
                "memory": device.memory
            }
            
        except Exception as e:
            logger.error(f"Workload assignment failed: {e}")
            raise
            
    def _detect_devices(self) -> Dict[str, DeviceCapabilities]:
        """Detect available compute devices"""
        devices = {}
        
        # CPU
        cpu_info = psutil.cpu_freq()
        devices["cpu"] = DeviceCapabilities(
            name="cpu",
            compute_units=psutil.cpu_count(),
            memory=psutil.virtual_memory().total,
            memory_type="DDR4",
            memory_bandwidth=42.7,  # GB/s per channel
            supports_ane=False
        )
        
        # GPU
        gpu = GPUtil.getGPUs()[0]  # 5600M
        devices["gpu"] = DeviceCapabilities(
            name="gpu",
            compute_units=40,  # 5600M has 40 CUs
            memory=8192,  # 8GB HBM2
            memory_type="HBM2", 
            memory_bandwidth=394.0,  # GB/s
            supports_ane=False
        )
        
        # Neural Engine
        devices["ane"] = DeviceCapabilities(
            name="ane",
            compute_units=16,  # Neural Engine cores
            memory=0,  # Uses system memory
            memory_type="Unified",
            memory_bandwidth=200.0,  # Estimated
            supports_ane=True
        )
        
        return devices 