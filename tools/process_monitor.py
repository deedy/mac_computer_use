from typing import Dict, List, Optional
from AppKit import NSWorkspace
import psutil
import logging
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a running process"""
    pid: int
    name: str
    app_name: str
    bundle_id: Optional[str]
    path: str
    cpu_percent: float
    memory_mb: float
    status: str
    created: datetime
    is_app: bool


class ProcessMonitor:
    """Native macOS process monitoring"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self._prev_cpu_times = {}
        
    async def get_running_apps(self) -> List[Dict]:
        """Get list of running applications"""
        try:
            apps = []
            for app in self.workspace.runningApplications():
                apps.append({
                    'name': app.localizedName(),
                    'bundle_id': app.bundleIdentifier(),
                    'pid': app.processIdentifier(),
                    'path': app.bundleURL().path(),
                    'is_active': app.isActive(),
                    'is_hidden': app.isHidden()
                })
            return apps
        except Exception as e:
            logger.error(f"Failed to get running apps: {e}")
            return []
            
    async def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed process information"""
        try:
            # Get psutil process info
            proc = psutil.Process(pid)
            
            # Get app info if it's an app
            app_info = None
            for app in self.workspace.runningApplications():
                if app.processIdentifier() == pid:
                    app_info = app
                    break
                    
            return ProcessInfo(
                pid=pid,
                name=proc.name(),
                app_name=app_info.localizedName() if app_info else proc.name(),
                bundle_id=app_info.bundleIdentifier() if app_info else None,
                path=proc.exe(),
                cpu_percent=await self._get_cpu_percent(proc),
                memory_mb=proc.memory_info().rss / 1024 / 1024,
                status=proc.status(),
                created=datetime.fromtimestamp(proc.create_time()),
                is_app=app_info is not None
            )
            
        except Exception as e:
            logger.error(f"Failed to get process info for PID {pid}: {e}")
            return None
            
    async def _get_cpu_percent(self, proc: psutil.Process) -> float:
        """Calculate CPU usage percentage"""
        try:
            # Get current CPU times
            cpu_times = proc.cpu_times()
            
            # Calculate difference from previous measurement
            if proc.pid in self._prev_cpu_times:
                prev = self._prev_cpu_times[proc.pid]
                user_time = cpu_times.user - prev.user
                system_time = cpu_times.system - prev.system
                cpu_percent = (user_time + system_time) * 100
            else:
                cpu_percent = 0
                
            # Store current measurement
            self._prev_cpu_times[proc.pid] = cpu_times
            
            return cpu_percent
            
        except Exception:
            return 0.0 