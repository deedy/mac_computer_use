from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi import File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
from pydantic import BaseModel, Field
from datetime import datetime
from .tools.tool_integration import ToolIntegrationManager
from .tools.mcp_integration import MCPIntegration
from .tools.model_manager import ModelManager

class ModelRequest(BaseModel):
    model_id: str
    task: str

class InferenceRequest(BaseModel):
    model_id: str
    inputs: str
    params: Optional[dict] = None

class DisplayConfig(BaseModel):
    resolution: Optional[tuple[int, int]] = None
    rotation: Optional[int] = None
    refresh_rate: Optional[float] = None

class DisplayCalibrationRequest(BaseModel):
    """Request model for display calibration"""
    brightness: float = Field(0.0, ge=0.0, le=1.0)
    contrast: float = Field(1.0, ge=0.0, le=1.0)
    gamma: float = Field(2.2, ge=1.8, le=2.4)
    color_profile: str
    white_point: tuple[float, float, float] = Field(
        default=(1.0, 1.0, 1.0),
        description="RGB white point values between 0.0 and 1.0"
    )

class WindowMetricsResponse(BaseModel):
    """Response model for window metrics"""
    window_id: int
    app_name: str
    title: str
    position: tuple[int, int]
    size: tuple[int, int]
    is_minimized: bool
    is_fullscreen: bool
    occlusion: float
    render_time: float

class DisplayMetricsResponse(BaseModel):
    """Response model for display metrics"""
    frame_rate: float = Field(..., description="Current refresh rate in Hz")
    frame_time: float = Field(..., description="Frame time in milliseconds")
    vsync_status: bool = Field(..., description="VSync enabled status")
    gpu_utilization: float = Field(..., description="GPU utilization percentage")
    memory_usage: float = Field(..., description="GPU memory usage in MB")
    power_usage: float = Field(..., description="Power consumption in watts")
    temperature: float = Field(..., description="GPU temperature in Celsius")
    artifacts_detected: bool
    timestamp: str

class DisplayProfileRequest(BaseModel):
    """Request model for display profile management"""
    name: str
    settings: Dict[str, Any]
    auto_switch: bool = False
    schedule: Optional[Dict[str, str]] = None

class DisplayArrangementRequest(BaseModel):
    """Request model for multi-display arrangement"""
    displays: List[Dict[str, Any]]
    layout: str = Field(..., description="grid/horizontal/vertical/custom")
    spacing: int = Field(0, ge=0, le=100)
    sync_enabled: bool = False

app = FastAPI()
websocket_manager = WebSocketManager()
tool_manager = ToolIntegrationManager()
mcp_integration = MCPIntegration()
model_manager = ModelManager()

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit
        "http://localhost:3000"   # Optional frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint with session management"""
    await websocket_manager.connect(websocket, session_id)
    
    try:
        while True:
            try:
                # Receive and parse message
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle different message types
                if data["type"] == "command":
                    result = await process_command(data["command"])
                    await websocket_manager.broadcast_update(
                        session_id,
                        {
                            "type": "command_result",
                            "command": data["command"],
                            "result": result
                        }
                    )
                elif data["type"] == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket, session_id)

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()} 

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    try:
        contents = await file.read()
        media_file = await websocket_manager.media_manager.save_uploaded_file(
            contents,
            file.filename
        )
        return {
            "success": True,
            "file_info": {
                "path": str(media_file.file_path),
                "type": media_file.media_type,
                "size": media_file.file_size,
                "duration": media_file.duration,
                "resolution": media_file.resolution
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@app.post("/api/capture/{media_type}")
async def capture_media(media_type: str, duration: Optional[int] = None):
    """Capture media from device"""
    try:
        if media_type == "audio":
            media_file = await websocket_manager.media_manager.record_audio(
                duration=duration or 10
            )
        elif media_type == "video":
            media_file = await websocket_manager.media_manager.capture_video(
                duration=duration or 10
            )
        elif media_type == "image":
            media_file = await websocket_manager.media_manager.capture_image()
        else:
            raise HTTPException(status_code=400, detail="Invalid media type")
            
        return {
            "success": True,
            "file_info": {
                "path": str(media_file.file_path),
                "type": media_file.media_type,
                "size": media_file.file_size,
                "duration": media_file.duration,
                "resolution": media_file.resolution
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@app.post("/api/transformers/load")
async def load_model(request: ModelRequest):
    """Load a Hugging Face Transformers model"""
    try:
        model_info = await websocket_manager.transformers_manager.load_model(
            request.model_id,
            request.task
        )
        return {
            "success": True,
            "model_info": model_info.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/transformers/inference")
async def run_inference(request: InferenceRequest):
    """Run inference with a loaded model"""
    try:
        result = await websocket_manager.transformers_manager.run_inference(
            request.model_id,
            request.inputs,
            **(request.params or {})
        )
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/transformers/{model_id}")
async def unload_model(model_id: str):
    """Unload a model to free memory"""
    try:
        await websocket_manager.transformers_manager.unload_model(model_id)
        return {
            "success": True,
            "message": f"Model {model_id} unloaded"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/transformers/loaded")
async def get_loaded_models():
    """Get information about currently loaded models"""
    models = websocket_manager.transformers_manager.get_loaded_models()
    return {
        "success": True,
        "models": [model.__dict__ for model in models]
    } 

@app.get("/api/sidecar/ipads")
async def get_available_ipads():
    """Get list of available iPads"""
    try:
        ipads = await websocket_manager.sidecar_manager.get_available_ipads()
        return {
            "success": True,
            "ipads": [vars(ipad) for ipad in ipads]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sidecar/start/{ipad_id}")
async def start_sidecar(ipad_id: str, position: Optional[str] = None):
    """Start Sidecar session"""
    try:
        success = await websocket_manager.sidecar_manager.start_sidecar(
            ipad_id, position
        )
        return {
            "success": success,
            "message": "Sidecar session started" if success else "Failed to start Sidecar"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sidecar/displays")
async def get_sidecar_displays():
    """Get active Sidecar displays"""
    try:
        displays = await websocket_manager.sidecar_manager.get_sidecar_displays()
        return {
            "success": True,
            "displays": [vars(display) for display in displays]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sidecar/configure/{display_id}")
async def configure_display(display_id: int, config: DisplayConfig):
    """Configure Sidecar display settings"""
    try:
        success = await websocket_manager.sidecar_manager.configure_display(
            display_id,
            config.resolution,
            config.rotation,
            config.refresh_rate
        )
        return {
            "success": success,
            "message": "Display configured" if success else "Failed to configure display"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sidecar/displays/active")
async def get_active_displays():
    """Get all active Sidecar displays"""
    try:
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
            for display in websocket_manager.sidecar_manager.active_displays.values()
        ]
        return {
            "success": True,
            "displays": displays
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sidecar/displays/{display_id}/calibrate")
async def calibrate_display(display_id: int, calibration: DisplayCalibrationRequest):
    """Calibrate a Sidecar display"""
    try:
        from .tools.sidecar import DisplayCalibration, ColorProfile
        
        # Validate color profile
        if calibration.color_profile not in ColorProfile.__members__:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid color profile. Must be one of: {list(ColorProfile.__members__.keys())}"
            )
        
        # Create calibration settings
        display_calibration = DisplayCalibration(
            brightness=calibration.brightness,
            contrast=calibration.contrast,
            gamma=calibration.gamma,
            color_profile=ColorProfile[calibration.color_profile],
            white_point=calibration.white_point
        )
        
        # Apply calibration
        success = await websocket_manager.sidecar_manager.calibrate_display(
            display_id,
            display_calibration
        )
        
        return {
            "success": success,
            "message": "Display calibrated successfully" if success else "Failed to calibrate display"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sidecar/displays/{display_id}/reset")
async def reset_display_calibration(display_id: int):
    """Reset display calibration to defaults"""
    try:
        success = await websocket_manager.sidecar_manager.reset_calibration(display_id)
        return {
            "success": success,
            "message": "Display calibration reset" if success else "Failed to reset calibration"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/metrics/{display_id}")
async def get_display_metrics(
    display_id: int,
    limit: Optional[int] = None,
    metric_types: Optional[List[str]] = None,
    aggregate: Optional[str] = None  # none/avg/min/max
) -> Dict[str, Any]:
    """Get enhanced performance metrics for a display"""
    try:
        metrics = websocket_manager.display_monitor.get_display_metrics(display_id)
        
        # Filter by metric types if specified
        if metric_types:
            metrics = [
                {k: v for k, v in m.__dict__.items() if k in metric_types}
                for m in metrics
            ]
            
        # Apply aggregation if requested
        if aggregate and metrics:
            if aggregate == "avg":
                metrics = {
                    k: sum(m[k] for m in metrics) / len(metrics)
                    for k in metrics[0].keys()
                    if isinstance(metrics[0][k], (int, float))
                }
            elif aggregate == "min":
                metrics = {
                    k: min(m[k] for m in metrics)
                    for k in metrics[0].keys()
                    if isinstance(metrics[0][k], (int, float))
                }
            elif aggregate == "max":
                metrics = {
                    k: max(m[k] for m in metrics)
                    for k in metrics[0].keys()
                    if isinstance(metrics[0][k], (int, float))
                }
                
        # Apply limit after aggregation
        if limit and not aggregate:
            metrics = metrics[-limit:]
            
        return {
            "success": True,
            "display_id": display_id,
            "metrics": metrics,
            "aggregation": aggregate
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/metrics/latest")
async def get_latest_metrics() -> Dict[str, Dict[str, DisplayMetricsResponse]]:
    """Get latest metrics for all displays"""
    try:
        latest_metrics = {}
        for display_id in websocket_manager.sidecar_manager.active_displays:
            metrics = websocket_manager.display_monitor.get_display_metrics(
                int(display_id)
            )
            if metrics:
                latest = metrics[-1]
                latest_metrics[str(display_id)] = DisplayMetricsResponse(
                    frame_rate=latest.frame_rate,
                    frame_time=latest.frame_time,
                    vsync_status=latest.vsync_status,
                    gpu_utilization=latest.gpu_utilization,
                    memory_usage=latest.memory_usage,
                    power_usage=latest.power_usage,
                    temperature=latest.temperature,
                    artifacts_detected=latest.artifacts_detected,
                    timestamp=latest.timestamp.isoformat()
                )
        return {
            "success": True,
            "metrics": latest_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/windows/metrics")
async def get_window_metrics() -> Dict[str, List[WindowMetricsResponse]]:
    """Get metrics for all windows"""
    try:
        metrics = []
        for window_id, window in websocket_manager.display_monitor.window_metrics.items():
            metrics.append(WindowMetricsResponse(
                window_id=window.window_id,
                app_name=window.app_name,
                title=window.title,
                position=window.position,
                size=window.size,
                is_minimized=window.is_minimized,
                is_fullscreen=window.is_fullscreen,
                occlusion=window.occlusion,
                render_time=window.render_time
            ))
        return {
            "success": True,
            "windows": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/windows/{window_id}/optimize")
async def optimize_window(window_id: int):
    """Optimize a specific window"""
    try:
        window = websocket_manager.display_monitor.get_window_metrics(window_id)
        if not window:
            raise HTTPException(
                status_code=404,
                detail=f"Window {window_id} not found"
            )
            
        await websocket_manager.display_monitor._optimize_window_performance(window)
        return {
            "success": True,
            "message": f"Window {window_id} optimized"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/optimize")
async def optimize_all_displays(
    optimization_level: str = "balanced",  # performance/quality/balanced
    power_mode: Optional[str] = None,  # normal/power-save/performance
    target_fps: Optional[int] = None,
    preserve_color: bool = True
):
    """Enhanced display optimization"""
    try:
        result = await websocket_manager.display_monitor.optimize_displays(
            optimization_level=optimization_level,
            power_mode=power_mode,
            target_fps=target_fps,
            preserve_color=preserve_color
        )
        return {
            "success": True,
            "optimizations": result.optimizations,
            "power_savings": result.power_savings,
            "performance_impact": result.performance_impact
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/performance/issues")
async def get_performance_issues() -> Dict[str, List[Dict]]:
    """Get current performance issues"""
    try:
        issues = []
        for display_id in websocket_manager.sidecar_manager.active_displays:
            metrics = websocket_manager.display_monitor.get_display_metrics(
                int(display_id)
            )
            if metrics:
                latest = metrics[-1]
                if latest.frame_rate < 30:
                    issues.append({
                        "display_id": display_id,
                        "type": "low_frame_rate",
                        "value": latest.frame_rate,
                        "threshold": 30
                    })
                if latest.frame_time > 33.33:
                    issues.append({
                        "display_id": display_id,
                        "type": "high_frame_time",
                        "value": latest.frame_time,
                        "threshold": 33.33
                    })
                if latest.temperature > 80:
                    issues.append({
                        "display_id": display_id,
                        "type": "high_temperature",
                        "value": latest.temperature,
                        "threshold": 80
                    })
                if latest.artifacts_detected:
                    issues.append({
                        "display_id": display_id,
                        "type": "artifacts_detected",
                        "timestamp": latest.timestamp.isoformat()
                    })
        return {
            "success": True,
            "issues": issues
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/profiles")
async def create_display_profile(profile: DisplayProfileRequest):
    """Create a new display profile"""
    try:
        # Save profile settings
        await websocket_manager.display_monitor.save_profile(
            name=profile.name,
            settings=profile.settings,
            auto_switch=profile.auto_switch,
            schedule=profile.schedule
        )
        return {
            "success": True,
            "message": f"Profile {profile.name} created"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/profiles")
async def get_display_profiles():
    """Get all saved display profiles"""
    try:
        profiles = await websocket_manager.display_monitor.get_profiles()
        return {
            "success": True,
            "profiles": profiles
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/profiles/{profile_name}/apply")
async def apply_display_profile(profile_name: str):
    """Apply a saved display profile"""
    try:
        success = await websocket_manager.display_monitor.apply_profile(profile_name)
        return {
            "success": success,
            "message": f"Profile {profile_name} applied" if success else "Failed to apply profile"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/arrangement")
async def arrange_displays(arrangement: DisplayArrangementRequest):
    """Arrange multiple displays"""
    try:
        success = await websocket_manager.display_monitor.arrange_displays(
            displays=arrangement.displays,
            layout=arrangement.layout,
            spacing=arrangement.spacing,
            sync_enabled=arrangement.sync_enabled
        )
        return {
            "success": success,
            "message": "Display arrangement applied"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/{display_id}/night-mode")
async def toggle_night_mode(
    display_id: int,
    enabled: bool,
    color_temp: Optional[int] = 2700,  # Kelvin
    brightness: Optional[float] = 0.7
):
    """Toggle night mode for a display"""
    try:
        success = await websocket_manager.display_monitor.set_night_mode(
            display_id,
            enabled,
            color_temp,
            brightness
        )
        return {
            "success": success,
            "message": f"Night mode {'enabled' if enabled else 'disabled'}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/sync")
async def sync_displays(
    source_id: int,
    target_ids: List[int],
    sync_type: str = "all"  # all/color/brightness/refresh
):
    """Synchronize multiple displays"""
    try:
        success = await websocket_manager.display_monitor.sync_displays(
            source_id,
            target_ids,
            sync_type
        )
        return {
            "success": success,
            "message": "Displays synchronized"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/{display_id}/color-analysis")
async def analyze_display_color(display_id: int):
    """Analyze display color accuracy"""
    try:
        analysis = await websocket_manager.display_monitor.analyze_color(display_id)
        return {
            "success": True,
            "analysis": {
                "color_gamut": analysis.color_gamut,
                "color_accuracy": analysis.color_accuracy,
                "white_point": analysis.white_point,
                "black_level": analysis.black_level,
                "contrast_ratio": analysis.contrast_ratio,
                "uniformity": analysis.uniformity
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/profiles/validate")
async def validate_profile_settings(profile: DisplayProfileRequest):
    """Validate display profile settings before saving"""
    try:
        # Validate color settings
        if "color_temp" in profile.settings:
            temp = profile.settings["color_temp"]
            if not 2000 <= temp <= 10000:
                raise ValueError("Color temperature must be between 2000K and 10000K")
                
        # Validate brightness/contrast
        for setting in ["brightness", "contrast"]:
            if setting in profile.settings:
                value = profile.settings[setting]
                if not 0 <= value <= 1:
                    raise ValueError(f"{setting} must be between 0 and 1")
                    
        # Validate schedule if auto-switching enabled
        if profile.auto_switch and profile.schedule:
            try:
                start = datetime.strptime(profile.schedule["start"], "%H:%M").time()
                end = datetime.strptime(profile.schedule["end"], "%H:%M").time()
                if start >= end:
                    raise ValueError("Start time must be before end time")
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid schedule format: {e}")
                
        return {
            "success": True,
            "message": "Profile settings are valid"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/profiles/compare")
async def compare_profiles(
    profile_names: List[str],
    metrics: Optional[List[str]] = None
):
    """Compare multiple display profiles"""
    try:
        profiles = []
        for name in profile_names:
            profile = await websocket_manager.display_monitor.get_profile(name)
            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Profile {name} not found"
                )
            profiles.append(profile)
            
        # Compare specified metrics or all common settings
        comparison = {}
        settings_to_compare = metrics or list(profiles[0].settings.keys())
        
        for metric in settings_to_compare:
            comparison[metric] = {
                profile.name: profile.settings.get(metric)
                for profile in profiles
            }
            
        # Calculate differences
        differences = []
        for metric, values in comparison.items():
            unique_values = set(values.values())
            if len(unique_values) > 1:
                differences.append({
                    "metric": metric,
                    "values": values,
                    "variance": max(unique_values) - min(unique_values)
                    if all(isinstance(v, (int, float)) for v in unique_values)
                    else None
                })
                
        return {
            "success": True,
            "profiles": profile_names,
            "comparison": comparison,
            "differences": differences
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/displays/profiles/{profile_name}/export")
async def export_profile(profile_name: str):
    """Export a display profile"""
    try:
        profile = await websocket_manager.display_monitor.get_profile(profile_name)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Profile {profile_name} not found"
            )
            
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "profile": {
                "name": profile.name,
                "settings": profile.settings,
                "auto_switch": profile.auto_switch,
                "schedule": profile.schedule,
                "metadata": {
                    "exported_from": "mac_computer_use",
                    "original_created_at": profile.created_at.isoformat()
                }
            }
        }
        
        return export_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/displays/profiles/import")
async def import_profile(
    import_data: Dict[str, Any],
    rename: Optional[str] = None
):
    """Import a display profile"""
    try:
        # Validate import data
        if "version" not in import_data or "profile" not in import_data:
            raise ValueError("Invalid import data format")
            
        profile_data = import_data["profile"]
        profile_name = rename or profile_data["name"]
        
        # Check for name conflicts
        existing = await websocket_manager.display_monitor.get_profile(profile_name)
        if existing:
            raise ValueError(f"Profile {profile_name} already exists")
            
        # Create new profile
        new_profile = DisplayProfileRequest(
            name=profile_name,
            settings=profile_data["settings"],
            auto_switch=profile_data.get("auto_switch", False),
            schedule=profile_data.get("schedule")
        )
        
        # Validate and save
        await validate_profile_settings(new_profile)
        await websocket_manager.display_monitor.save_profile(
            name=new_profile.name,
            settings=new_profile.settings,
            auto_switch=new_profile.auto_switch,
            schedule=new_profile.schedule
        )
        
        return {
            "success": True,
            "message": f"Profile {profile_name} imported successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tools/list")
async def list_tools() -> Dict[str, Any]:
    """List available tools and their schemas"""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in tool_manager.tools.values()
        ]
    }

@app.post("/api/tools/call/{tool_name}")
async def call_tool(tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Call a specific tool with inputs"""
    try:
        result = await tool_manager.handle_tool_call(tool_name, inputs)
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tools/batch")
async def batch_tool_calls(calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute multiple tool calls in sequence"""
    results = []
    for call in calls:
        tool_name = call["tool"]
        inputs = call["inputs"]
        try:
            result = await tool_manager.handle_tool_call(tool_name, inputs)
            results.append({
                "success": True,
                "tool": tool_name,
                "result": result
            })
        except Exception as e:
            results.append({
                "success": False,
                "tool": tool_name,
                "error": str(e)
            })
            
    return {
        "success": True,
        "results": results
    } 

@app.post("/api/mcp/connect")
async def connect_mcp_source(source_config: Dict[str, Any]) -> Dict[str, Any]:
    """Connect a data source using Model Context Protocol"""
    try:
        context_id = await mcp_integration.connect_data_source(source_config)
        return {
            "success": True,
            "context_id": context_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/mcp/context/{context_id}")
async def get_mcp_context(context_id: str) -> Dict[str, Any]:
    """Get MCP context information"""
    try:
        context = await mcp_integration.get_context(context_id)
        return {
            "success": True,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/models/load")
async def load_model(model_name: str, device: Optional[str] = None):
    """Load a specific model"""
    try:
        await model_manager.load_model(model_name, device)
        return {
            "success": True,
            "message": f"Model {model_name} loaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/models/generate")
async def generate_text(
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    tools: Optional[List[Dict[str, Any]]] = None
):
    """Generate text with loaded model"""
    try:
        response = await model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools
        )
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 