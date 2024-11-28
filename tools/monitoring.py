"""Monitoring module for metrics collection."""

import time
import asyncio
from typing import Dict, Any
from functools import wraps
import logging
from .logging_config import logger


class Metrics:
    """Application metrics collection and monitoring."""
    
    def __init__(self):
        """Initialize metrics."""
        self._metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "errors": 0,
            "latency": []
        }
    
    def track_api_call(self) -> None:
        """Track API call."""
        self._metrics["api_calls"] += 1
    
    def track_cache_hit(self) -> None:
        """Track cache hit."""
        self._metrics["cache_hits"] += 1
    
    def track_error(self) -> None:
        """Track error."""
        self._metrics["errors"] += 1
    
    def track_latency(self, duration: float) -> None:
        """Track request latency."""
        self._metrics["latency"].append(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self._metrics.copy()
        if metrics["latency"]:
            metrics["avg_latency"] = sum(metrics["latency"]) / len(metrics["latency"])
        else:
            metrics["avg_latency"] = 0
        return metrics
    
    async def initialize(self, port: int = None) -> None:
        """Initialize metrics server if port is provided."""
        logger.info("Metrics initialized")
        
    async def cleanup(self) -> None:
        """Cleanup metrics."""
        self._metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "errors": 0,
            "latency": []
        }
        logger.info("Metrics cleaned up")


def monitor_performance(threshold_ms: float = 1000):
    """Decorator to monitor function performance.
    
    Args:
        threshold_ms: Performance warning threshold in milliseconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Performance warning: {func.__name__} took "
                        f"{duration_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Error in {func.__name__}: {str(e)}. "
                    f"Duration: {duration_ms:.2f}ms"
                )
                raise
                
        return wrapper
    return decorator 