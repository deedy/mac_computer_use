from typing import Optional, Dict, List
import Quartz
import AVFoundation
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class CaptureConfig:
    """Screen capture configuration"""
    display_id: Optional[int] = None  # None = main display
    fps: int = 60
    quality: float = 0.8  # 0.0 to 1.0
    include_cursor: bool = True
    include_audio: bool = False
    output_format: str = "mp4"  # mp4, mov, m4v


class ScreenCapture:
    """Native macOS screen recording"""
    
    def __init__(self):
        self.recording = False
        self.output_dir = Path("recordings")
        self.output_dir.mkdir(exist_ok=True)
        self._setup_capture_session()
        
    def _setup_capture_session(self):
        """Initialize AVFoundation capture session"""
        self.session = AVFoundation.AVCaptureSession.alloc().init()
        self.session.setSessionPreset_(
            AVFoundation.AVCaptureSessionPresetHigh
        )
        
    def start_recording(
        self,
        config: Optional[CaptureConfig] = None,
        output_path: Optional[Path] = None
    ) -> bool:
        """Start screen recording with config"""
        try:
            if self.recording:
                return False
                
            config = config or CaptureConfig()
            
            # Setup output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = (
                    self.output_dir / f"recording_{timestamp}.{config.output_format}"
                )
                
            # Configure screen input
            screen_input = AVFoundation.AVCaptureScreenInput.alloc().init()
            screen_input.setCapturesMouseClicks_(config.include_cursor)
            
            if config.display_id:
                screen_input.setDisplayID_(config.display_id)
                
            self.session.addInput_(screen_input)
            
            # Configure audio if needed
            if config.include_audio:
                audio_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(
                    AVFoundation.AVCaptureDevice.defaultDeviceWithMediaType_(
                        AVFoundation.AVMediaTypeAudio
                    ),
                    None
                )[0]
                self.session.addInput_(audio_input)
                
            # Configure output
            self.output = AVFoundation.AVCaptureMovieFileOutput.alloc().init()
            self.session.addOutput_(self.output)
            
            # Start recording
            self.session.startRunning()
            self.output.startRecordingToOutputFileURL_recordingDelegate_(
                NSURL.fileURLWithPath_(str(output_path)),
                self
            )
            self.recording = True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
            
    def stop_recording(self) -> bool:
        """Stop current recording"""
        try:
            if not self.recording:
                return False
                
            self.output.stopRecording()
            self.session.stopRunning()
            self.recording = False
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
            
    def is_recording(self) -> bool:
        """Check if recording is active"""
        return self.recording
        
    def captureOutput_didFinishRecordingToOutputFileAtURL_fromConnections_error_(
        self, output, url, connections, error
    ):
        """AVFoundation recording delegate callback"""
        if error:
            logger.error(f"Recording failed: {error}")
        else:
            logger.info(f"Recording completed: {url.path()}") 