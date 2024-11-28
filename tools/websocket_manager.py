import asyncio
from fastapi import WebSocket
from typing import Dict, Set
import json
import time
from fastapi import WebSocketDisconnect
import logging
from .activity_monitor import ActivityMonitor
from .metrics import ActivityMetrics
from .media_manager import MediaManager
from .mock_transformers import MockTransformersManager
from .sidecar import SidecarManager, DisplayCalibration, ColorProfile
from .display_monitor import DisplayMonitor

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._reconnect_attempts: Dict[str, int] = {}
        self.MAX_RECONNECT_ATTEMPTS = 5
        self.RECONNECT_DELAY = 1.0  # seconds
        
        # Initialize managers
        self.activity_monitor = ActivityMonitor()
        self.media_manager = MediaManager()
        self.transformers_manager = MockTransformersManager()
        self.sidecar_manager = SidecarManager()
        self.display_monitor = DisplayMonitor()
        
        # Start monitoring tasks
        self._start_monitoring_tasks()
        
    def _start_monitoring_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._monitor_displays())
        asyncio.create_task(self._monitor_display_performance())
        asyncio.create_task(self.broadcast_metrics())
        
    async def _monitor_displays(self):
        """Monitor Sidecar display changes"""
        while True:
            try:
                # Get all active displays
                displays = [
                    {
                        "id": display.id,
                        "width": display.width,
                        "height": display.height,
                        "rotation": display.rotation,
                        "refresh_rate": display.refresh_rate,
                        "is_retina": display.is_retina,
                        "is_airplay": display.is_airplay,
                        "calibration": display.calibration.__dict__ if display.calibration else None,
                        "error_count": display.error_count,
                        "last_error": display.last_error
                    }
                    for display in self.sidecar_manager.active_displays.values()
                ]
                
                # Broadcast to all sessions
                for session_id in self.active_connections:
                    await self.broadcast_update(
                        session_id,
                        {
                            "type": "display_update",
                            "timestamp": time.time(),
                            "displays": displays
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error monitoring displays: {e}")
                
            await asyncio.sleep(1)  # Check every second
            
    async def _monitor_display_performance(self):
        """Monitor display performance metrics"""
        while True:
            try:
                # Collect metrics for all displays
                for display_id in self.sidecar_manager.active_displays:
                    metrics = self.display_monitor.get_display_metrics(int(display_id))
                    if metrics:
                        latest = metrics[-1]
                        await self.broadcast_update(
                            "all",  # Broadcast to all sessions
                            {
                                "type": "display_performance",
                                "display_id": display_id,
                                "metrics": {
                                    "frame_rate": latest.frame_rate,
                                    "frame_time": latest.frame_time,
                                    "gpu_utilization": latest.gpu_utilization,
                                    "temperature": latest.temperature,
                                    "artifacts_detected": latest.artifacts_detected,
                                    "timestamp": latest.timestamp.isoformat()
                                }
                            }
                        )
                        
                # Optimize windows periodically
                await self.display_monitor.optimize_windows()
                
            except Exception as e:
                logger.error(f"Display performance monitoring error: {e}")
                
            await asyncio.sleep(1)  # Update every second
            
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client with reconnection support"""
        try:
            await websocket.accept()
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)
            self._reconnect_attempts[session_id] = 0
            
            # Send initial connection status
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected"
            })
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self._handle_reconnection(websocket, session_id)
            
    async def _handle_reconnection(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket reconnection attempts"""
        attempts = self._reconnect_attempts.get(session_id, 0)
        
        while attempts < self.MAX_RECONNECT_ATTEMPTS:
            try:
                await asyncio.sleep(self.RECONNECT_DELAY * (2 ** attempts))
                await self.connect(websocket, session_id)
                return
            except Exception as e:
                attempts += 1
                self._reconnect_attempts[session_id] = attempts
                logger.warning(f"Reconnection attempt {attempts} failed: {e}")
        
        logger.error(f"Max reconnection attempts reached for session {session_id}")
        await self.disconnect(websocket, session_id)
            
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a WebSocket client"""
        self.active_connections[session_id].remove(websocket)
        if not self.active_connections[session_id]:
            del self.active_connections[session_id]
            
    async def broadcast_update(self, session_id: str, data: dict):
        """Broadcast update with improved error handling and retries"""
        if session_id in self.active_connections:
            if data.get("type") == "display_calibration":
                try:
                    display_id = data["display_id"]
                    calibration = DisplayCalibration(**data["calibration"])
                    
                    success = await self.sidecar_manager.calibrate_display(
                        display_id,
                        calibration
                    )
                    
                    data["success"] = success
                    if not success:
                        data["error"] = "Failed to apply display calibration"
                        
                except Exception as e:
                    data["error"] = str(e)
                    
            elif data.get("type") == "media_upload":
                try:
                    media_file = await self.media_manager.save_uploaded_file(
                        data["file_data"],
                        data["filename"]
                    )
                    data["file_info"] = {
                        "path": str(media_file.file_path),
                        "type": media_file.media_type,
                        "size": media_file.file_size,
                        "duration": media_file.duration,
                        "resolution": media_file.resolution
                    }
                except Exception as e:
                    data["error"] = str(e)
            elif data.get("type") == "transformers":
                try:
                    if data["action"] == "load_model":
                        result = await self.transformers_manager.load_model(
                            data["model_id"],
                            data["task"]
                        )
                        data["model_info"] = result.__dict__
                    elif data["action"] == "inference":
                        result = await self.transformers_manager.run_inference(
                            data["model_id"],
                            data["inputs"],
                            **data.get("params", {})
                        )
                        data["result"] = result
                    elif data["action"] == "unload_model":
                        await self.transformers_manager.unload_model(data["model_id"])
                        data["status"] = "unloaded"
                except Exception as e:
                    data["error"] = str(e)
                    
            dead_connections = set()
            
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json({
                        "type": "update",
                        "timestamp": time.time(),
                        "data": data
                    })
                except WebSocketDisconnect:
                    dead_connections.add(connection)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                await self.disconnect(dead, session_id) 
            
    async def broadcast_metrics(self):
        """Broadcast system metrics to all connected clients"""
        while True:
            try:
                # Collect metrics
                system_metrics = await self.activity_monitor.get_system_metrics()
                process_list = await self.activity_monitor.get_process_list()
                
                # Update Prometheus metrics
                await ActivityMetrics.collect_metrics()
                
                # Broadcast to all sessions
                for session_id in self.active_connections:
                    await self.broadcast_update(
                        session_id,
                        {
                            "type": "metrics",
                            "timestamp": time.time(),
                            "system_metrics": system_metrics.__dict__,
                            "processes": [p.__dict__ for p in process_list[:10]]
                        }
                    )
            except Exception as e:
                logger.error(f"Error broadcasting metrics: {e}")
                
            await asyncio.sleep(2)  # Update every 2 seconds 
            
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Cleanup Sidecar displays
            self.sidecar_manager.cleanup()
            
            # Close all connections
            for session_id in list(self.active_connections.keys()):
                for connection in self.active_connections[session_id]:
                    asyncio.create_task(self.disconnect(connection, session_id))
                    
        except Exception as e:
            logger.error(f"Cleanup error: {e}")