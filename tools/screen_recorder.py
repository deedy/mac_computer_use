from typing import Optional
import subprocess
import logging
from pathlib import Path
from datetime import datetime


logger = logging.getLogger(__name__)


class ScreenRecorder:
    """Native macOS screen recording"""
    
    def __init__(self):
        self.recording = False
        self.output_dir = Path("recordings")
        self.output_dir.mkdir(exist_ok=True)
        
    def start_recording(
        self,
        output_name: Optional[str] = None,
        audio: bool = False
    ) -> bool:
        """Start screen recording"""
        try:
            if self.recording:
                return False
                
            # Generate output path
            if not output_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"recording_{timestamp}.mov"
                
            output_path = self.output_dir / output_name
            
            # Build command
            cmd = ['screencapture', '-v']
            if audio:
                cmd.append('-g')  # Include audio
            cmd.extend(['-V', '60'])  # 60 FPS video
            cmd.append(str(output_path))
            
            # Start recording
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.recording = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
            
    def stop_recording(self) -> bool:
        """Stop screen recording"""
        try:
            if not self.recording:
                return False
                
            self.process.terminate()
            self.recording = False
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
            
    def is_recording(self) -> bool:
        """Check if recording is active"""
        return self.recording 