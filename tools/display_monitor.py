from dataclasses import dataclass
from typing import Dict, List, Optional
import Quartz
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class DisplayPerformanceMetrics:
    """Display performance metrics"""
    frame_rate: float
    frame_time: float
    vsync_status: bool
    gpu_utilization: float
    memory_usage: float
    power_usage: float
    temperature: float
    artifacts_detected: bool
    timestamp: datetime

@dataclass
class WindowMetrics:
    """Window performance and layout metrics"""
    window_id: int
    app_name: str
    title: str
    position: tuple[int, int]
    size: tuple[int, int]
    is_minimized: bool
    is_fullscreen: bool
    occlusion: float  # % of window visible
    render_time: float

class DisplayMonitor:
    """Monitor display performance and window management"""
    
    def __init__(self):
        self.metrics_history: Dict[int, List[DisplayPerformanceMetrics]] = {}
        self.window_metrics: Dict[int, WindowMetrics] = {}
        self.sampling_interval = 1.0  # seconds
        
    async def start_monitoring(self):
        """Start continuous display monitoring"""
        while True:
            try:
                await self._collect_metrics()
                await self._analyze_performance()
                await asyncio.sleep(self.sampling_interval)
            except Exception as e:
                logger.error(f"Display monitoring error: {e}")
                
    async def _collect_metrics(self):
        """Collect display performance metrics"""
        for display_id in Quartz.CGDisplayCopyAllDisplayModes(None, None):
            try:
                metrics = DisplayPerformanceMetrics(
                    frame_rate=Quartz.CGDisplayModeGetRefreshRate(display_id),
                    frame_time=await self._measure_frame_time(display_id),
                    vsync_status=self._check_vsync(display_id),
                    gpu_utilization=await self._get_gpu_stats(display_id),
                    memory_usage=await self._get_gpu_memory(display_id),
                    power_usage=await self._get_power_usage(display_id),
                    temperature=await self._get_temperature(display_id),
                    artifacts_detected=await self._detect_artifacts(display_id),
                    timestamp=datetime.now()
                )
                
                if display_id not in self.metrics_history:
                    self.metrics_history[display_id] = []
                    
                self.metrics_history[display_id].append(metrics)
                
                # Keep last hour of metrics
                self.metrics_history[display_id] = self.metrics_history[display_id][-3600:]
                
            except Exception as e:
                logger.error(f"Error collecting metrics for display {display_id}: {e}")
                
    async def _analyze_performance(self):
        """Analyze display performance and detect issues"""
        for display_id, metrics in self.metrics_history.items():
            if not metrics:
                continue
                
            latest = metrics[-1]
            
            # Check for performance issues
            if latest.frame_rate < 30:
                logger.warning(f"Low frame rate on display {display_id}: {latest.frame_rate} FPS")
                
            if latest.frame_time > 33.33:  # More than 30ms frame time
                logger.warning(f"High frame time on display {display_id}: {latest.frame_time}ms")
                
            if latest.artifacts_detected:
                logger.warning(f"Display artifacts detected on display {display_id}")
                
            if latest.temperature > 80:  # °C
                logger.warning(f"High GPU temperature for display {display_id}: {latest.temperature}°C")
                
    async def optimize_windows(self):
        """Optimize window layout and performance"""
        try:
            windows = await self._get_window_list()
            
            for window in windows:
                # Calculate optimal position
                optimal_pos = await self._calculate_optimal_position(window)
                
                # Update window metrics
                self.window_metrics[window.window_id] = WindowMetrics(
                    window_id=window.window_id,
                    app_name=window.app_name,
                    title=window.title,
                    position=optimal_pos,
                    size=window.size,
                    is_minimized=window.is_minimized,
                    is_fullscreen=window.is_fullscreen,
                    occlusion=await self._calculate_occlusion(window),
                    render_time=await self._measure_window_render_time(window)
                )
                
                # Apply optimizations
                if window.render_time > 16.67:  # More than 60 FPS
                    await self._optimize_window_performance(window)
                    
        except Exception as e:
            logger.error(f"Window optimization error: {e}")
            
    def get_display_metrics(self, display_id: int) -> List[DisplayPerformanceMetrics]:
        """Get metrics history for a display"""
        return self.metrics_history.get(display_id, [])
        
    def get_window_metrics(self, window_id: int) -> Optional[WindowMetrics]:
        """Get metrics for a window"""
        return self.window_metrics.get(window_id) 