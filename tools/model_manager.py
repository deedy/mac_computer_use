from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from llama_cpp import Llama
import torch

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for different model backends"""
    name: str
    type: str  # local/api/hybrid
    context_length: int
    supports_tools: bool
    quantization: Optional[str] = None
    device: str = "auto"


class ModelManager:
    """Manages different model backends for computer control"""
    
    def __init__(self):
        self.available_models = {
            "codellama-34b": ModelConfig(
                name="codellama-34b-instruct",
                type="local",
                context_length=16384,
                supports_tools=True,
                quantization="4-bit"
            ),
            "mistral-7b": ModelConfig(
                name="mistralai/Mistral-7B-Instruct-v0.2",
                type="local",
                context_length=8192,
                supports_tools=True,
                quantization="4-bit"
            ),
            "phi-2": ModelConfig(
                name="microsoft/phi-2",
                type="local",
                context_length=2048,
                supports_tools=True,
                quantization="4-bit"
            ),
            "openchat": ModelConfig(
                name="openchat/openchat-3.5",
                type="local",
                context_length=8192,
                supports_tools=True
            )
        }
        self.active_model = None
        self.tokenizer = None
        
    async def load_model(self, model_name: str, device: Optional[str] = None):
        """Load a specific model"""
        try:
            if model_name not in self.available_models:
                raise ValueError(f"Unknown model: {model_name}")
                
            config = self.available_models[model_name]
            
            # Determine device
            if device:
                config.device = device
            elif config.device == "auto":
                config.device = "cuda" if torch.cuda.is_available() else "cpu"
                
            # Load model based on type
            if config.type == "local":
                if config.quantization:
                    # Load quantized model
                    self.active_model = await self._load_quantized(config)
                else:
                    # Load full precision model
                    self.active_model = AutoModelForCausalLM.from_pretrained(
                        config.name,
                        device_map=config.device,
                        trust_remote_code=True
                    )
                    
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(config.name)
                
            logger.info(f"Loaded model {model_name} on {config.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
            
    async def _load_quantized(self, config: ModelConfig):
        """Load a quantized model"""
        try:
            if config.quantization == "4-bit":
                return AutoModelForCausalLM.from_pretrained(
                    config.name,
                    device_map=config.device,
                    load_in_4bit=True,
                    trust_remote_code=True
                )
            elif config.quantization == "8-bit":
                return AutoModelForCausalLM.from_pretrained(
                    config.name,
                    device_map=config.device,
                    load_in_8bit=True,
                    trust_remote_code=True
                )
                
        except Exception as e:
            logger.error(f"Failed to load quantized model: {e}")
            raise
            
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate text with the active model"""
        try:
            if not self.active_model:
                raise ValueError("No model loaded")
                
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.active_model.device)
            
            # Add tool information if supported
            if tools and self.available_models[self.active_model.config.name].supports_tools:
                inputs["tools"] = tools
                
            outputs = self.active_model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True
            )
            
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise 