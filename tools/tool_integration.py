from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ToolDefinition:
    """Definition for a tool that Claude can use"""
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolIntegrationManager:
    """Manages integration with Claude's universal tool system"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {
            "optimize_system": ToolDefinition(
                name="optimize_system",
                description="""
                Optimize system performance based on workload type and requirements.
                Use this tool when the user wants to optimize their MacBook Pro's performance
                for specific tasks like development, creative work, or gaming.
                """,
                input_schema={
                    "type": "object",
                    "properties": {
                        "workload_type": {
                            "type": "string",
                            "enum": ["development", "creative", "gaming"],
                            "description": "Type of workload to optimize for"
                        },
                        "power_mode": {
                            "type": "string",
                            "enum": ["high_power", "balanced", "battery"],
                            "description": "Power mode to use"
                        },
                        "thermal_priority": {
                            "type": "string",
                            "enum": ["performance", "quiet", "balanced"],
                            "description": "Thermal management priority"
                        }
                    },
                    "required": ["workload_type"]
                }
            ),
            "configure_displays": ToolDefinition(
                name="configure_displays",
                description="""
                Configure display settings for internal and external displays.
                Handles resolution, refresh rate, color profile, and scaling settings.
                Optimizes for the MacBook Pro's 5600M GPU capabilities.
                """,
                input_schema={
                    "type": "object",
                    "properties": {
                        "display_config": {
                            "type": "object",
                            "properties": {
                                "resolution": {"type": "string"},
                                "refresh_rate": {"type": "integer"},
                                "color_profile": {"type": "string"},
                                "scaling": {"type": "number"}
                            }
                        },
                        "external_displays": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "resolution": {"type": "string"},
                                    "refresh_rate": {"type": "integer"},
                                    "color_profile": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            ),
            "monitor_performance": ToolDefinition(
                name="monitor_performance",
                description="""
                Monitor real-time system performance metrics including CPU, GPU, 
                memory, and thermal data. Specific to 2019 MacBook Pro with i9-9880H
                and Radeon Pro 5600M.
                """,
                input_schema={
                    "type": "object",
                    "properties": {
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "cpu_stats",
                                    "gpu_stats",
                                    "memory_stats",
                                    "thermal_stats",
                                    "power_stats"
                                ]
                            }
                        },
                        "interval": {
                            "type": "integer",
                            "description": "Monitoring interval in seconds"
                        }
                    }
                }
            ),
            "mcp_connect": ToolDefinition(
                name="mcp_connect",
                description="""
                Connect to data sources using Anthropic's Model Context Protocol.
                Allows Claude to maintain context while accessing multiple data sources.
                """,
                input_schema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Data source identifier"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional source metadata"
                        }
                    },
                    "required": ["source"]
                }
            )
        }
        
    async def handle_tool_call(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call from Claude"""
        try:
            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")
                
            tool = self.tools[tool_name]
            
            # Validate inputs against schema
            self._validate_inputs(tool, inputs)
            
            # Execute the appropriate tool
            if tool_name == "optimize_system":
                return await self._handle_optimize_system(inputs)
            elif tool_name == "configure_displays":
                return await self._handle_configure_displays(inputs)
            elif tool_name == "monitor_performance":
                return await self._handle_monitor_performance(inputs)
            elif tool_name == "mcp_connect":
                return await self._handle_mcp_connect(inputs)
                
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def _handle_optimize_system(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle optimize_system tool calls"""
        workload = inputs["workload_type"]
        power_mode = inputs.get("power_mode", "balanced")
        
        # Configure system based on workload
        if workload == "development":
            await self._optimize_for_development(power_mode)
        elif workload == "creative":
            await self._optimize_for_creative(power_mode)
        elif workload == "gaming":
            await self._optimize_for_gaming(power_mode)
            
        return {
            "success": True,
            "workload": workload,
            "power_mode": power_mode,
            "timestamp": datetime.now().isoformat()
        } 