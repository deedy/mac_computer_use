"""Configuration settings for the application."""

from typing import Optional
from dataclasses import dataclass
import os
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class Settings:
    """Application settings"""
    ANTHROPIC_API_KEY: str
    API_REGION: str = "us-west-2"
    GCP_PROJECT: Optional[str] = None
    CACHE_TTL: int = 3600
    RATE_LIMIT: int = 100
    LOG_LEVEL: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        return cls(
            ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY", ""),
            API_REGION=os.getenv("API_REGION", "us-west-2"),
            GCP_PROJECT=os.getenv("GCP_PROJECT"),
            CACHE_TTL=int(os.getenv("CACHE_TTL", "3600")),
            RATE_LIMIT=int(os.getenv("RATE_LIMIT", "100")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def get_endpoint(self) -> str:
        """Get API endpoint based on region"""
        if self.API_REGION == "us-west-2":
            return "https://api.anthropic.com"
        return f"https://{self.API_REGION}.anthropic.aws.com"
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save settings to file"""
        if path is None:
            path = (
                Path.home() / ".config" / "mac_computer_use" / "settings.json"
            )
            
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)
            
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        """Load settings from file"""
        if path is None:
            path = (
                Path.home() / ".config" / "mac_computer_use" / "settings.json"
            )
            
        if not path.exists():
            return cls.from_env()
            
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return cls.from_env()

# Global settings instance
settings = Settings.from_env() 