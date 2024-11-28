import asyncio
import av
import numpy as np
from PIL import Image
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
import cv2
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MediaFile:
    """Represents a captured media file"""
    file_path: Path
    media_type: str  # 'audio', 'video', 'image'
    timestamp: datetime
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    file_size: int = 0

class MediaManager:
    """Handles audio, video and image capture/uploads"""
    
    def __init__(self, storage_dir: str = "storage/media"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._setup_directories()
        
    def _setup_directories(self):
        """Create media type subdirectories"""
        (self.storage_dir / "audio").mkdir(exist_ok=True)
        (self.storage_dir / "video").mkdir(exist_ok=True)
        (self.storage_dir / "images").mkdir(exist_ok=True)
        
    async def record_audio(self, duration: int = 10, sample_rate: int = 44100) -> MediaFile:
        """Record audio from microphone"""
        timestamp = datetime.now()
        filename = f"audio_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        file_path = self.storage_dir / "audio" / filename
        
        try:
            # Record audio
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=2,
                dtype='float32'
            )
            sd.wait()
            
            # Save to file
            sf.write(file_path, recording, sample_rate)
            
            return MediaFile(
                file_path=file_path,
                media_type="audio",
                timestamp=timestamp,
                duration=duration,
                file_size=file_path.stat().st_size
            )
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            raise
            
    async def capture_video(self, duration: int = 10, fps: int = 30) -> MediaFile:
        """Record video from webcam"""
        timestamp = datetime.now()
        filename = f"video_{timestamp.strftime('%Y%m%d_%H%M%S')}.mp4"
        file_path = self.storage_dir / "video" / filename
        
        try:
            cap = cv2.VideoCapture(0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            output = av.open(str(file_path), 'w')
            stream = output.add_stream('h264', fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = 'yuv420p'
            
            frames = duration * fps
            for _ in range(frames):
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert frame to video packet
                frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
                packet = stream.encode(frame)
                output.mux(packet)
                
                await asyncio.sleep(1/fps)  # Control capture rate
                
            # Clean up
            cap.release()
            output.close()
            
            return MediaFile(
                file_path=file_path,
                media_type="video",
                timestamp=timestamp,
                duration=duration,
                resolution=(width, height),
                file_size=file_path.stat().st_size
            )
            
        except Exception as e:
            logger.error(f"Video capture failed: {e}")
            raise
            
    async def capture_image(self) -> MediaFile:
        """Capture image from webcam"""
        timestamp = datetime.now()
        filename = f"image_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        file_path = self.storage_dir / "images" / filename
        
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise RuntimeError("Failed to capture image")
                
            # Save image
            cv2.imwrite(str(file_path), frame)
            
            height, width = frame.shape[:2]
            return MediaFile(
                file_path=file_path,
                media_type="image",
                timestamp=timestamp,
                resolution=(width, height),
                file_size=file_path.stat().st_size
            )
            
        except Exception as e:
            logger.error(f"Image capture failed: {e}")
            raise
            
    async def save_uploaded_file(self, file_data: bytes, filename: str) -> MediaFile:
        """Save an uploaded file"""
        timestamp = datetime.now()
        
        # Determine media type from extension
        ext = Path(filename).suffix.lower()
        if ext in {'.wav', '.mp3', '.ogg', '.m4a'}:
            media_type = "audio"
        elif ext in {'.mp4', '.mov', '.avi', '.mkv'}:
            media_type = "video"
        elif ext in {'.jpg', '.jpeg', '.png', '.gif'}:
            media_type = "image"
        else:
            raise ValueError(f"Unsupported file type: {ext}")
            
        file_path = self.storage_dir / media_type / filename
        
        try:
            # Save file
            file_path.write_bytes(file_data)
            
            # Get media properties
            duration = None
            resolution = None
            
            if media_type == "video":
                container = av.open(str(file_path))
                stream = container.streams.video[0]
                duration = float(container.duration) / av.time_base
                resolution = (stream.width, stream.height)
                container.close()
            elif media_type == "image":
                img = Image.open(file_path)
                resolution = img.size
                img.close()
            elif media_type == "audio":
                info = sf.info(file_path)
                duration = float(info.duration)
                
            return MediaFile(
                file_path=file_path,
                media_type=media_type,
                timestamp=timestamp,
                duration=duration,
                resolution=resolution,
                file_size=file_path.stat().st_size
            )
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            if file_path.exists():
                file_path.unlink()
            raise
            
    def list_media_files(self, media_type: Optional[str] = None) -> List[MediaFile]:
        """List all media files, optionally filtered by type"""
        media_files = []
        
        if media_type:
            search_dirs = [self.storage_dir / media_type]
        else:
            search_dirs = [self.storage_dir / t for t in ["audio", "video", "images"]]
            
        for directory in search_dirs:
            if not directory.exists():
                continue
                
            for file_path in directory.iterdir():
                try:
                    media_files.append(MediaFile(
                        file_path=file_path,
                        media_type=directory.name.rstrip('s'),  # remove plural
                        timestamp=datetime.fromtimestamp(file_path.stat().st_mtime),
                        file_size=file_path.stat().st_size
                    ))
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    
        return sorted(media_files, key=lambda x: x.timestamp, reverse=True) 