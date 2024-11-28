from typing import Optional, Dict, List, Any
import torch
from transformers import (
    AutoTokenizer, 
    AutoModel,
    AutoModelForSequenceClassification,
    AutoModelForCausalLM,
    pipeline
)
import logging
from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_id: str
    task: str
    loaded_at: datetime
    device: str
    config: Dict[str, Any]
    memory_used: int = 0

class TransformersManager:
    """Manages Hugging Face Transformers models and inference"""
    
    def __init__(self, cache_dir: str = "storage/models"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    async def load_model(self, model_id: str, task: str) -> ModelInfo:
        """Load a model for a specific task"""
        try:
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=self.cache_dir,
                use_fast=True
            )
            
            # Load model based on task
            if task == "text-generation":
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    device_map="auto" if self.device == "cuda" else None
                )
            elif task == "classification":
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    device_map="auto" if self.device == "cuda" else None
                )
            else:
                model = AutoModel.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    device_map="auto" if self.device == "cuda" else None
                )
                
            # Create pipeline
            pipe = pipeline(
                task,
                model=model,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            # Store model info
            model_info = ModelInfo(
                model_id=model_id,
                task=task,
                loaded_at=datetime.now(),
                device=self.device,
                config=model.config.to_dict(),
                memory_used=model.get_memory_footprint() if hasattr(model, 'get_memory_footprint') else 0
            )
            
            self.loaded_models[model_id] = {
                "info": model_info,
                "tokenizer": tokenizer,
                "model": model,
                "pipeline": pipe
            }
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise
            
    async def run_inference(
        self,
        model_id: str,
        inputs: str,
        max_length: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Run inference with a loaded model"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
            
        try:
            pipe = self.loaded_models[model_id]["pipeline"]
            model_info = self.loaded_models[model_id]["info"]
            
            # Run inference based on task
            if model_info.task == "text-generation":
                result = pipe(
                    inputs,
                    max_length=max_length or 100,
                    **kwargs
                )
            else:
                result = pipe(inputs, **kwargs)
                
            return {
                "model_id": model_id,
                "task": model_info.task,
                "input": inputs,
                "output": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Inference failed for model {model_id}: {e}")
            raise
            
    def get_loaded_models(self) -> List[ModelInfo]:
        """Get information about currently loaded models"""
        return [info["info"] for info in self.loaded_models.values()]
        
    async def unload_model(self, model_id: str):
        """Unload a model to free memory"""
        if model_id in self.loaded_models:
            try:
                model = self.loaded_models[model_id]["model"]
                del model
                torch.cuda.empty_cache()
                del self.loaded_models[model_id]
            except Exception as e:
                logger.error(f"Failed to unload model {model_id}: {e}")
                raise 