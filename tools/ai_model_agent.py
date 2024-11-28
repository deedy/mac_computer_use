from dataclasses import dataclass
from typing import Dict, Optional, List
import logging
from pathlib import Path
import torch

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for AI model management"""
    name: str
    model_type: str
    quantization: Optional[str] = "4-bit"  # 4-bit, 8-bit or None
    context_length: int = 8192
    device: str = "auto"
    temperature: float = 0.7
    max_tokens: int = 1000


class AIModelAgent:
    """Agent for managing AI models and inference"""
    
    def __init__(self):
        self.available_models = {
            "codellama-34b": ModelConfig(
                name="codellama-34b-instruct",
                model_type="code",
                context_length=16384
            ),
            "mistral-7b": ModelConfig(
                name="mistralai/Mistral-7B-v0.2",
                model_type="general",
                context_length=8192
            ),
            "phi-2": ModelConfig(
                name="microsoft/phi-2",
                model_type="general",
                context_length=2048
            ),
            "qwen-7b": ModelConfig(
                name="Qwen/Qwen-7B-Chat",
                model_type="chat",
                context_length=8192
            )
        }
        self.active_models = {}
        
    async def load_model(self, model_name: str, device: Optional[str] = None):
        """Load an AI model with optimal settings"""
        try:
            if model_name not in self.available_models:
                raise ValueError(f"Unknown model: {model_name}")
                
            config = self.available_models[model_name]
            
            # Auto-detect optimal device
            if device:
                config.device = device
            elif config.device == "auto":
                config.device = "mps" if torch.backends.mps.is_available() else \
                              "cuda" if torch.cuda.is_available() else "cpu"
                              
            # Load model with quantization if specified
            if config.quantization == "4-bit":
                model = await self._load_4bit(config)
            elif config.quantization == "8-bit":
                model = await self._load_8bit(config)
            else:
                model = await self._load_full(config)
                
            self.active_models[model_name] = model
            logger.info(f"Loaded {model_name} on {config.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
            
    async def generate(self, 
                      prompt: str,
                      model_name: str,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> str:
        """Generate text using specified model"""
        try:
            if model_name not in self.active_models:
                raise ValueError(f"Model {model_name} not loaded")
                
            config = self.available_models[model_name]
            model = self.active_models[model_name]
            
            response = await model.generate(
                prompt=prompt,
                temperature=temperature or config.temperature,
                max_tokens=max_tokens or config.max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise 