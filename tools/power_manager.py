from dataclasses import dataclass
from typing import Dict, Optional
import logging
import asyncio
import psutil
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class PowerState:
    """Display power state"""
    brightness: float
    power_mode: str  # normal/eco/performance
    refresh_rate: int
    power_draw: float  # watts
    temperature: float  # celsius

@dataclass
class PowerProfile:
    """Power management profile"""
    name: str
    cpu_power_limit: int  # Watts
    gpu_power_limit: int  # Watts
    fan_speed: str  # auto/quiet/max
    battery_threshold: Optional[int] = None
    thermal_target: int = 85  # °C

class PowerManager:
    """Manage display power states"""
    
    def __init__(self):
        self.power_states: Dict[int, PowerState] = {}
        self.power_targets = {
            "eco": {"max_power": 15, "max_brightness": 0.7},
            "normal": {"max_power": 25, "max_brightness": 0.9},
            "performance": {"max_power": 35, "max_brightness": 1.0}
        }
        self.active_profile = None
        self.profiles = {
            "max_performance": PowerProfile(
                name="max_performance",
                cpu_power_limit=90,  # Full i9 power
                gpu_power_limit=50,  # Full 5600M power
                fan_speed="max",
                thermal_target=95
            ),
            "balanced": PowerProfile(
                name="balanced", 
                cpu_power_limit=45,  # Base TDP
                gpu_power_limit=35,
                fan_speed="auto",
                thermal_target=85
            ),
            "battery_saver": PowerProfile(
                name="battery_saver",
                cpu_power_limit=25,
                gpu_power_limit=20,
                fan_speed="quiet",
                battery_threshold=20,
                thermal_target=75
            )
        }
        
    async def optimize_power(self, display_id: int, target_mode: str):
        """Optimize display power consumption"""
        try:
            current_state = self.power_states.get(display_id)
            if not current_state:
                return
                
            target = self.power_targets[target_mode]
            
            # Adjust settings to meet power target
            if current_state.power_draw > target["max_power"]:
                # Reduce brightness first
                new_brightness = min(
                    current_state.brightness,
                    target["max_brightness"]
                )
                await self._set_brightness(display_id, new_brightness)
                
                # Reduce refresh rate if needed
                if current_state.power_draw > target["max_power"]:
                    new_refresh = self._calculate_optimal_refresh_rate(
                        current_state.refresh_rate,
                        target["max_power"]
                    )
                    await self._set_refresh_rate(display_id, new_refresh)
                    
            # Monitor temperature
            if current_state.temperature > 80:
                await self._enable_thermal_throttling(display_id)
                
        except Exception as e:
            logger.error(f"Power optimization failed: {e}")
            raise 

    async def set_power_profile(self, profile_name: str):
        """Apply power management profile"""
        try:
            if profile_name not in self.profiles:
                raise ValueError(f"Unknown profile: {profile_name}")
                
            profile = self.profiles[profile_name]
            
            # Configure CPU power
            await self._set_cpu_power(profile.cpu_power_limit)
            
            # Configure GPU power
            await self._set_gpu_power(profile.gpu_power_limit)
            
            # Set fan speed
            await self._set_fan_speed(profile.fan_speed)
            
            # Configure thermal target
            await self._set_thermal_target(profile.thermal_target)
            
            self.active_profile = profile
            
        except Exception as e:
            logger.error(f"Failed to set power profile: {e}")
            raise

    def get_power_info(self) -> Dict:
        """Get power and battery information"""
        try:
            # Run pmset command
            output = subprocess.check_output(
                ['pmset', '-g', 'batt']
            ).decode()
            
            # Parse output
            info = {
                'power_source': 'Unknown',
                'battery_percent': None,
                'time_remaining': None,
                'charging': False
            }
            
            # Extract power source
            if 'AC Power' in output:
                info['power_source'] = 'AC'
            elif 'Battery Power' in output:
                info['power_source'] = 'Battery'
                
            # Extract battery info
            for line in output.split('\n'):
                if '%' in line:
                    # Get percentage
                    percent = line.split('\t')[1].split(';')[0]
                    info['battery_percent'] = int(percent.strip('%'))
                    
                    # Get charging status
                    info['charging'] = 'charging' in line.lower()
                    
                    # Get time remaining
                    if 'no estimate' not in line:
                        for part in line.split(';'):
                            if 'remaining' in part:
                                hours = int(part.split(':')[0].strip())
                                mins = int(part.split(':')[1].strip())
                                info['time_remaining'] = hours * 60 + mins
                                
            return info
            
        except Exception as e:
            logger.error(f"Failed to get power info: {e}")
            return {}
            
    def prevent_sleep(self, duration: int) -> bool:
        """Prevent system sleep for duration (minutes)"""
        try:
            subprocess.run(
                ['caffeinate', '-t', str(duration * 60)],
                check=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to prevent sleep: {e}")
            return False
            
    def allow_sleep(self) -> bool:
        """Allow system sleep"""
        try:
            subprocess.run(['killall', 'caffeinate'], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to allow sleep: {e}")
            return False