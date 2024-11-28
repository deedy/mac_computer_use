import Vision
from Foundation import NSImage
from typing import List, Dict
import cv2
import numpy as np

class LiveTextExtractor:
    """Extract text from images using Live Text"""
    
    def extract_text(self, image_path: str) -> List[Dict]:
        """Extract text and data from image"""
        # Load image
        image = NSImage.alloc().initWithContentsOfFile_(image_path)
        if not image:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # Create Vision request
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)
        
        # Process image
        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
            image.TIFFRepresentation(),
            None
        )
        handler.performRequests_error_([request], None)
        
        # Extract results
        results = []
        for observation in request.results():
            results.append({
                'text': observation.text(),
                'confidence': observation.confidence(),
                'bounds': observation.boundingBox(),
                'recognized_languages': observation.recognizedLanguages()
            })
        return results
        
    def detect_data_types(self, image_path: str) -> List[Dict]:
        """Detect data types (phones, URLs, etc) in image"""
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)
        
        image = cv2.imread(image_path)
        handler = Vision.VNImageRequestHandler.alloc().initWithCVPixelBuffer_options_(
            image, None
        )
        
        handler.performRequests_error_([request], None)
        
        data_types = []
        for observation in request.results():
            for candidate in observation.topCandidates_(1):
                data_types.extend([{
                    'type': dt.dataType(),
                    'value': dt.value(),
                    'confidence': dt.confidence()
                } for dt in candidate.dataTypes()])
                
        return data_types 