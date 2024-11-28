import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CursorIntegration:
    """Integration with Cursor editor for both GUI and CLI modes"""
    
    def __init__(self):
        self.cursor_path = self._find_cursor_installation()
        self.current_mode = "gui"  # or "cli"
        
    def _find_cursor_installation(self) -> Optional[Path]:
        """Find Cursor installation path"""
        possible_paths = [
            Path("/Applications/Cursor.app"),
            Path.home() / "Applications/Cursor.app",
            Path.home() / ".local/share/cursor"  # Linux path
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
        
    async def launch_gui(self, file_path: Optional[str] = None):
        """Launch Cursor in GUI mode"""
        try:
            if not self.cursor_path:
                raise RuntimeError("Cursor installation not found")
                
            cmd = ["open", "-a", str(self.cursor_path)]
            if file_path:
                cmd.extend(["--args", file_path])
                
            subprocess.run(cmd, check=True)
            self.current_mode = "gui"
            
        except Exception as e:
            logger.error(f"Failed to launch Cursor GUI: {e}")
            raise
            
    async def launch_cli(self):
        """Launch Cursor in CLI mode"""
        try:
            if not self.cursor_path:
                raise RuntimeError("Cursor installation not found")
                
            # Extract CLI binary from app bundle
            cli_path = self.cursor_path / "Contents/Resources/app/bin/cursor"
            if not cli_path.exists():
                raise RuntimeError("Cursor CLI not found")
                
            # Launch CLI
            subprocess.run([str(cli_path)], check=True)
            self.current_mode = "cli"
            
        except Exception as e:
            logger.error(f"Failed to launch Cursor CLI: {e}")
            raise
            
    async def configure_cursor(self, settings: Dict[str, Any]):
        """Configure Cursor settings"""
        try:
            # Apply settings based on mode
            if self.current_mode == "gui":
                await self._configure_gui(settings)
            else:
                await self._configure_cli(settings)
                
        except Exception as e:
            logger.error(f"Failed to configure Cursor: {e}")
            raise
            
    async def _configure_gui(self, settings: Dict[str, Any]):
        """Configure GUI-specific settings"""
        # Implement GUI configuration using AppleScript or defaults
        pass
        
    async def _configure_cli(self, settings: Dict[str, Any]):
        """Configure CLI-specific settings"""
        # Implement CLI configuration
        pass 