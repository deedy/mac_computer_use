"""Local Models module for offline LLM support."""

import os
from typing import Dict, Any
from pathlib import Path
import torch
from llama_cpp import Llama
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)
import anthropic
import streamlit as st
from .base import BaseTool
from .logging_config import logger
from .config import settings


class ModelManager:
    """Manages local model operations."""
    
    def __init__(self) -> None:
        """Initialize model manager."""
        self.models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize Anthropic client with key from session state or settings
        api_key = (
            st.session_state.api_keys["anthropic"]
            if hasattr(st.session_state, "api_keys")
            else settings.ANTHROPIC_API_KEY
        )
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def load_model(
        self,
        model_name: str,
        model_type: str = "hf"
    ) -> None:
        """Load a model.
        
        Args:
            model_name: Name or path of model
            model_type: Type of model (hf, llama, or anthropic)
        """
        try:
            if model_name in self.models:
                return
                
            if model_type == "anthropic":
                # No loading needed for Anthropic models
                self.models[model_name] = self.anthropic_client
            elif model_type == "llama":
                await self._load_llama_model(model_name)
            elif model_type == "hf":
                await self._load_hf_model(model_name)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
                
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    async def _load_hf_model(self, model_name: str) -> None:
        """Load a Hugging Face model."""
        try:
            # Load tokenizer
            self.tokenizers[model_name] = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # Load model without quantization
            self.models[model_name] = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
        except Exception as e:
            logger.error(f"Failed to load HF model {model_name}: {e}")
            raise
    
    async def _load_llama_model(self, model_path: str) -> None:
        """Load a llama.cpp model."""
        try:
            self.models[model_path] = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=min(8, os.cpu_count() or 1)
            )
            
        except Exception as e:
            logger.error(f"Failed to load llama model {model_path}: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        model_name: str,
        model_type: str = "hf",
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any
    ) -> str:
        """Generate text using specified model."""
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not loaded")
                
            model = self.models[model_name]
            
            if model_type == "anthropic":
                # Generate with Anthropic API
                message = await model.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
                
            elif isinstance(model, Llama):
                # Generate with llama.cpp
                output = model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    **kwargs
                )
                return output["choices"][0]["text"]
                
            else:
                # Generate with Hugging Face model
                tokenizer = self.tokenizers[model_name]
                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048
                ).to(model.device)
                
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    **kwargs
                )
                
                return tokenizer.decode(
                    outputs[0],
                    skip_special_tokens=True
                )[len(prompt):]
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise


class LocalModelTool(BaseTool):
    """Tool for local model operations."""
    
    def __init__(self) -> None:
        """Initialize local model tool."""
        super().__init__()
        self.model_manager = ModelManager()
    
    async def execute(
        self,
        prompt: str,
        model_name: str,
        model_type: str = "hf",
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute model generation.
        
        Args:
            prompt: Input prompt
            model_name: Name of model to use
            model_type: Type of model
            **kwargs: Additional parameters
            
        Returns:
            Dict containing generation results
        """
        try:
            # Load model if needed
            await self.model_manager.load_model(model_name, model_type)
            
            # Generate text
            output = await self.model_manager.generate(
                prompt,
                model_name,
                model_type,
                **kwargs
            )
            
            return {
                'success': True,
                'output': output
            }
            
        except Exception as e:
            logger.error(f"Local model tool execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }