from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Mock model information"""
    model_id: str
    task: str
    loaded_at: datetime
    device: str
    config: Dict[str, Any]
    memory_used: int = 0

class MockTransformersManager:
    """Mock version of TransformersManager for testing"""
    
    def __init__(self, cache_dir: str = "storage/models"):
        self.loaded_models = {}
        self.device = "cpu"  # Always use CPU for testing
        
    async def load_model(self, model_id: str, task: str) -> ModelInfo:
        """Mock loading a model"""
        logger.info(f"Mock loading model {model_id} for task {task}")
        
        model_info = ModelInfo(
            model_id=model_id,
            task=task,
            loaded_at=datetime.now(),
            device=self.device,
            config={"mock_config": True},
            memory_used=1000000  # 1MB mock memory usage
        )
        
        self.loaded_models[model_id] = {
            "info": model_info,
            "mock_responses": {
                "text-generation": "This is a mock generated text response.",
                "classification": {"label": "positive", "score": 0.95},
                "default": "Mock model output"
            }
        }
        
        return model_info
        
    async def run_inference(
        self,
        model_id: str,
        inputs: str,
        max_length: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock inference"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
            
        model_info = self.loaded_models[model_id]["info"]
        mock_responses = self.loaded_models[model_id]["mock_responses"]
        
        return {
            "model_id": model_id,
            "task": model_info.task,
            "input": inputs,
            "output": mock_responses.get(
                model_info.task,
                mock_responses["default"]
            ),
            "timestamp": datetime.now().isoformat()
        }
        
    def get_loaded_models(self) -> List[ModelInfo]:
        """Get mock loaded models"""
        return [info["info"] for info in self.loaded_models.values()]
        
    async def unload_model(self, model_id: str):
        """Mock unloading a model"""
        if model_id in self.loaded_models:
            logger.info(f"Mock unloading model {model_id}")
            del self.loaded_models[model_id] 