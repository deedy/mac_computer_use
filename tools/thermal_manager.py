from dataclasses import dataclass
import logging
from typing import Dict, List
import psutil
import GPUtil
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ThermalZone:
    """Thermal zone information"""
    name: str
    current_temp: float
    target_temp: float
    critical_temp: float
    fan_speed: int  # RPM


class ThermalManager:
    """Advanced thermal management for i9 + 5600M"""
    
    def __init__(self):
        self.thermal_zones = {
            "cpu": ThermalZone(
                name="cpu",
                current_temp=0.0,
                target_temp=85.0,
                critical_temp=100.0,
                fan_speed=0
            ),
            "gpu": ThermalZone(
                name="gpu",
                current_temp=0.0,
                target_temp=80.0,
                critical_temp=95.0,
                fan_speed=0
            )
        }
        self.fan_curves = {
            "quiet": {
                "min_speed": 1200,
                "max_speed": 3000,
                "ramp_start": 65,
                "ramp_end": 85
            },
            "balanced": {
                "min_speed": 1500,
                "max_speed": 4200,
                "ramp_start": 60,
                "ramp_end": 80
            },
            "performance": {
                "min_speed": 2000,
                "max_speed": 5400,
                "ramp_start": 55,
                "ramp_end": 75
            }
        }
        
    async def monitor_temperatures(self):
        """Monitor and manage thermal zones"""
        try:
            # Get CPU temps
            cpu_temps = psutil.sensors_temperatures()
            if 'coretemp' in cpu_temps:
                self.thermal_zones["cpu"].current_temp = max(
                    t.current for t in cpu_temps['coretemp']
                )
                
            # Get GPU temp
            gpu = GPUtil.getGPUs()[0]  # 5600M
            self.thermal_zones["gpu"].current_temp = gpu.temperature
            
            # Check thermal status
            await self._check_thermal_status()
            
        except Exception as e:
            logger.error(f"Temperature monitoring failed: {e}")
            raise
            
    async def _check_thermal_status(self):
        """Check and respond to thermal conditions"""
        try:
            for zone in self.thermal_zones.values():
                if zone.current_temp >= zone.critical_temp:
                    await self._handle_critical_temp(zone)
                elif zone.current_temp >= zone.target_temp:
                    await self._handle_high_temp(zone)
                    
        except Exception as e:
            logger.error(f"Thermal status check failed: {e}")
            raise