import subprocess
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PowerState:
    battery_percent: float
    is_charging: bool
    time_remaining: Optional[int]
    power_source: str

class EnergyManager:
    """Manage system power and energy settings"""
    
    def get_power_state(self) -> PowerState:
        """Get current power state"""
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        
        # Parse pmset output
        power_source = 'Battery' if 'Battery Power' in lines[0] else 'AC Power'
        percent = float(lines[1].split('\t')[1].rstrip('%;'))
        is_charging = '; charging' in lines[1]
        
        # Parse time remaining if available
        time_remaining = None
        if '(' in lines[1]:
            time_str = lines[1].split('(')[1].split(')')[0]
            if time_str.endswith('remaining'):
                hours, mins = map(int, time_str.split(' remaining')[0].split(':'))
                time_remaining = hours * 60 + mins
                
        return PowerState(
            battery_percent=percent,
            is_charging=is_charging,
            time_remaining=time_remaining,
            power_source=power_source
        )
        
    def set_power_mode(self, mode: str):
        """Set power mode (low_power/high_performance)"""
        if mode == 'low_power':
            subprocess.run(['pmset', '-a', 'lowpowermode', '1'])
        else:
            subprocess.run(['pmset', '-a', 'lowpowermode', '0']) 