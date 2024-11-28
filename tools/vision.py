"""Vision module for advanced image analysis and OCR."""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2
from PIL import Image
import Vision
import Quartz
from .base import BaseTool
from .logging_config import logger
from .config import settings


class VisionManager:
    """Manages Vision framework operations."""
    
    def __init__(self) -> None:
        """Initialize Vision framework components."""
        self.request_handler = Vision.VNImageRequestHandler.alloc().init()
        self.text_request = Vision.VNRecognizeTextRequest.alloc().init()
        self.object_request = Vision.VNDetectRectanglesRequest.alloc().init()
        self.color_request = Vision.VNGenerateImageFeaturePrintRequest.alloc().init()
    
    async def analyze_image(
        self, image: np.ndarray
    ) -> Dict[str, Any]:
        """Analyze image using Vision framework.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Convert numpy array to CGImage
            height, width = image.shape[:2]
            bytes_per_row = width * 4
            color_space = Quartz.CGColorSpaceCreateDeviceRGB()
            
            cg_image = Quartz.CGDataProviderCreateWithData(
                None,
                image.tobytes(),
                height * bytes_per_row,
                None
            )
            
            cg_image = Quartz.CGImageCreate(
                width,
                height,
                8,
                32,
                bytes_per_row,
                color_space,
                Quartz.kCGImageAlphaNoneSkipLast,
                cg_image,
                None,
                False,
                Quartz.kCGRenderingIntentDefault
            )
            
            # Perform analysis
            results = {}
            
            # Text recognition
            await self._recognize_text(cg_image, results)
            
            # Object detection
            await self._detect_objects(cg_image, results)
            
            # Color analysis
            await self._analyze_colors(cg_image, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise
    
    async def _recognize_text(
        self,
        image: Any,
        results: Dict[str, Any]
    ) -> None:
        """Perform text recognition.
        
        Args:
            image: CGImage to analyze
            results: Dict to store results
        """
        try:
            self.text_request.setRecognitionLevel_(
                Vision.VNRequestTextRecognitionLevelAccurate
            )
            self.request_handler.performRequests_([self.text_request], error=None)
            
            observations = self.text_request.results()
            
            text_results = []
            for observation in observations:
                text_results.append({
                    'text': observation.text(),
                    'confidence': observation.confidence(),
                    'bounds': observation.boundingBox()
                })
                
            results['text'] = text_results
            
        except Exception as e:
            logger.error(f"Text recognition failed: {e}")
            results['text'] = []
    
    async def _detect_objects(
        self,
        image: Any,
        results: Dict[str, Any]
    ) -> None:
        """Perform object detection.
        
        Args:
            image: CGImage to analyze
            results: Dict to store results
        """
        try:
            self.object_request.setMinimumAspectRatio_(0.2)
            self.object_request.setMaximumAspectRatio_(1.0)
            
            self.request_handler.performRequests_([self.object_request], error=None)
            
            observations = self.object_request.results()
            
            object_results = []
            for observation in observations:
                object_results.append({
                    'confidence': observation.confidence(),
                    'bounds': observation.boundingBox()
                })
                
            results['objects'] = object_results
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            results['objects'] = []
    
    async def _analyze_colors(
        self,
        image: Any,
        results: Dict[str, Any]
    ) -> None:
        """Perform color analysis.
        
        Args:
            image: CGImage to analyze
            results: Dict to store results
        """
        try:
            self.request_handler.performRequests_([self.color_request], error=None)
            
            observations = self.color_request.results()
            
            color_results = []
            for observation in observations:
                color_results.append({
                    'colors': observation.dominantColors(),
                    'contrast': observation.contrast()
                })
                
            results['colors'] = color_results
            
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            results['colors'] = []


class VisionTool(BaseTool):
    """Tool for Vision framework operations."""
    
    def __init__(self) -> None:
        """Initialize Vision tool."""
        super().__init__()
        self.vision_manager = VisionManager()
    
    async def execute(
        self,
        image: Optional[np.ndarray] = None,
        image_path: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute Vision analysis.
        
        Args:
            image: Image as numpy array
            image_path: Path to image file
            **kwargs: Additional arguments
            
        Returns:
            Dict containing analysis results
        """
        try:
            if image is None and image_path is not None:
                # Load image from file
                image = cv2.imread(image_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if image is None:
                raise ValueError("No image provided")
            
            # Perform analysis
            results = await self.vision_manager.analyze_image(image)
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Vision tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            } 