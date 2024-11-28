from typing import Dict
import platform
import subprocess
import logging
from AppKit import NSWorkspace


logger = logging.getLogger(__name__)


class SystemInfo:
    """Native macOS system information"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        try:
            # Get OS info
            os_info = {
                'name': platform.mac_ver()[0],
                'version': subprocess.check_output(
                    ['sw_vers', '-productVersion']
                ).decode().strip(),
                'build': subprocess.check_output(
                    ['sw_vers', '-buildVersion']
                ).decode().strip(),
                'arch': platform.machine()
            }
            
            # Get hardware info
            hw_info = {
                'model': subprocess.check_output(
                    ['sysctl', '-n', 'hw.model']
                ).decode().strip(),
                'cpu_brand': subprocess.check_output(
                    ['sysctl', '-n', 'machdep.cpu.brand_string']
                ).decode().strip(),
                'cpu_cores': subprocess.check_output(
                    ['sysctl', '-n', 'hw.ncpu']
                ).decode().strip(),
                'memory_gb': round(
                    int(subprocess.check_output(
                        ['sysctl', '-n', 'hw.memsize']
                    ).decode().strip()) / 1024**3
                )
            }
            
            # Get active user info
            user_info = {
                'username': subprocess.check_output(
                    ['whoami']
                ).decode().strip(),
                'full_name': subprocess.check_output(
                    ['id', '-F']
                ).decode().strip(),
                'home_dir': subprocess.check_output(
                    ['echo', '$HOME']
                ).decode().strip()
            }
            
            return {
                'os': os_info,
                'hardware': hw_info,
                'user': user_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {} 