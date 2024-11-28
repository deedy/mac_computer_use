import psutil
from dataclasses import dataclass
from typing import Dict, List
import subprocess

@dataclass
class SystemHealth:
    cpu_temp: float
    fan_speeds: List[int]
    memory_pressure: str
    disk_health: Dict[str, str]

class HealthMonitor:
    """Monitor system health metrics"""
    
    def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health data"""
        # Get CPU temperature
        temp_cmd = "sudo powermetrics --samplers smc -i1 -n1"
        temp_output = subprocess.check_output(temp_cmd.split()).decode()
        cpu_temp = float(temp_output.split('CPU die temperature:')[1].split()[0])
        
        # Get fan speeds
        fans_cmd = "sudo smc -f"
        fans_output = subprocess.check_output(fans_cmd.split()).decode()
        fan_speeds = [int(line.split()[-1]) for line in fans_output.splitlines()]
        
        # Get memory pressure
        vm = psutil.virtual_memory()
        if vm.percent > 90:
            memory_pressure = "Critical"
        elif vm.percent > 75:
            memory_pressure = "Warning"
        else:
            memory_pressure = "Normal"
            
        # Check disk health
        disk_health = {}
        for disk in psutil.disk_partitions():
            smart_cmd = f"smartctl -H {disk.device}"
            try:
                health = subprocess.check_output(smart_cmd.split()).decode()
                status = "Healthy" if "PASSED" in health else "Warning"
            except:
                status = "Unknown"
            disk_health[disk.device] = status
            
        return SystemHealth(
            cpu_temp=cpu_temp,
            fan_speeds=fan_speeds,
            memory_pressure=memory_pressure,
            disk_health=disk_health
        ) 