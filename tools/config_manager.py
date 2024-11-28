from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """Application configuration settings"""
    api_key: str = ""
    width: int = 1280
    height: int = 800
    display_num: Optional[int] = None
    theme: str = "dark"
    cursor_settings: Dict[str, Any] = None
    productivity_settings: Dict[str, Any] = None
    cache_enabled: bool = True
    debug_mode: bool = False

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "mac_computer_use"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()
        
    def _load_config(self) -> AppConfig:
        """Load configuration from file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if self.config_file.exists():
                with open(self.config_file) as f:
                    data = json.load(f)
                return AppConfig(**data)
            
            return AppConfig()
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return AppConfig()
            
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(vars(self.config), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            
    def update_config(self, **kwargs):
        """Update configuration settings"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config() 