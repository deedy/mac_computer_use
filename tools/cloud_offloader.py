from dataclasses import dataclass
import logging
from typing import Dict
import psutil
import GPUtil
from datetime import datetime
from tools.credentials_manager import CredentialsManager

logger = logging.getLogger(__name__)


@dataclass
class CloudService:
    """Cloud service configuration"""
    name: str
    service_type: str  # compute/inference/storage
    cost_per_hour: float
    performance_rating: float
    latency_ms: int
    bandwidth_gbps: float


class CloudOffloader:
    """Optimizes workload distribution between local and cloud resources"""
    
    def __init__(self):
        self.creds_manager = CredentialsManager()
        # Configure available cloud services
        self.services = {
            "aws_g5": CloudService(
                name="AWS G5.2xlarge",
                service_type="compute",
                cost_per_hour=1.212,
                performance_rating=0.95,
                latency_ms=15,
                bandwidth_gbps=25
            ),
            "openai_gpt4": CloudService(
                name="OpenAI GPT-4",
                service_type="inference",
                cost_per_hour=0.03,
                performance_rating=0.98,
                latency_ms=200,
                bandwidth_gbps=1
            ),
            "hf_inference": CloudService(
                name="HuggingFace Inference",
                service_type="inference", 
                cost_per_hour=0.008,
                performance_rating=0.85,
                latency_ms=100,
                bandwidth_gbps=5
            )
        }
        
        # Configure local hardware capabilities
        self.local_capabilities = {
            "cpu": {
                "model": "Intel Core i9-9880H",
                "cores": 8,
                "threads": 16,
                "base_clock": 2.4,
                "boost_clock": 5.0,
                "tdp": 45
            },
            "gpu": {
                "model": "AMD Radeon Pro 5600M",
                "memory": 8192,
                "compute_units": 40,
                "memory_bandwidth": 394,
                "tdp": 50
            },
            "memory": {
                "total": 64 * 1024,  # MB
                "speed": 2667,
                "channels": 2,
                "bandwidth": 42.7 * 2  # GB/s per channel
            }
        }
        
    async def route_workload(self, workload_type: str, requirements: Dict):
        """Route workload to optimal execution environment"""
        try:
            # Get current system metrics
            metrics = await self._get_system_metrics()
            
            # Calculate local execution score
            local_score = self._calculate_local_score(
                workload_type,
                requirements,
                metrics
            )
            
            # Calculate cloud service scores
            cloud_scores = {}
            for service_name, service in self.services.items():
                if service.service_type != requirements.get("service_type"):
                    continue
                    
                score = self._calculate_cloud_score(
                    service,
                    requirements,
                    metrics
                )
                cloud_scores[service_name] = score
                
            # Select optimal execution environment
            if local_score > max(cloud_scores.values(), default=0):
                return await self._execute_locally(workload_type, requirements)
                
            # Find best cloud service
            best_service = max(cloud_scores.items(), key=lambda x: x[1])[0]
            return await self._execute_in_cloud(
                self.services[best_service],
                workload_type,
                requirements
            )
            
        except Exception as e:
            logger.error(f"Workload routing failed: {e}")
            raise
            
    def _calculate_local_score(self, workload_type: str, requirements: Dict, metrics: Dict) -> float:
        """Calculate score for local execution"""
        try:
            # Base score from hardware capabilities
            if workload_type == "ml_inference":
                base_score = (
                    self.local_capabilities["gpu"]["compute_units"] / 40 * 0.4 +
                    self.local_capabilities["gpu"]["memory"] / 8192 * 0.3 +
                    self.local_capabilities["memory"]["total"] / 65536 * 0.3
                )
            else:
                base_score = (
                    self.local_capabilities["cpu"]["cores"] / 8 * 0.4 +
                    self.local_capabilities["memory"]["total"] / 65536 * 0.3 +
                    self.local_capabilities["gpu"]["memory"] / 8192 * 0.3
                )
                
            # Adjust for current resource usage
            cpu_available = 1 - metrics["cpu_usage"] / 100
            gpu_available = 1 - metrics["gpu_usage"] / 100
            memory_available = 1 - metrics["memory_usage"] / 100
            
            availability_score = (
                cpu_available * 0.4 +
                gpu_available * 0.3 +
                memory_available * 0.3
            )
            
            return base_score * availability_score
            
        except Exception as e:
            logger.error(f"Local score calculation failed: {e}")
            return 0.0
            
    def _calculate_cloud_score(self, service: CloudService, requirements: Dict, metrics: Dict) -> float:
        """Calculate score for cloud service"""
        try:
            # Performance score
            perf_score = service.performance_rating
            
            # Cost score (inverse of cost)
            cost_score = 1 / (service.cost_per_hour + 0.001)  # Avoid division by zero
            
            # Network score
            network_score = (
                (1000 - service.latency_ms) / 1000 * 0.5 +
                service.bandwidth_gbps / 25 * 0.5  # Normalize to 25 Gbps
            )
            
            # Weight factors based on requirements
            perf_weight = requirements.get("performance_priority", 0.4)
            cost_weight = requirements.get("cost_priority", 0.3)
            network_weight = requirements.get("network_priority", 0.3)
            
            return (
                perf_score * perf_weight +
                cost_score * cost_weight +
                network_score * network_weight
            )
            
        except Exception as e:
            logger.error(f"Cloud score calculation failed: {e}")
            return 0.0 
        
    async def _execute_in_cloud(self, service: CloudService, workload_type: str, requirements: Dict):
        """Execute workload in cloud"""
        try:
            # Get credentials
            creds = self.creds_manager.get_credentials(service.name.split("_")[0])
            if not creds:
                raise ValueError(f"No credentials found for {service.name}")
                
            # Configure client based on service
            if "aws" in service.name:
                client = self._get_aws_client(creds)
            elif "openai" in service.name:
                client = self._get_openai_client(creds)
            elif "hf" in service.name:
                client = self._get_hf_client(creds)
                
            # Execute workload
            return await self._run_cloud_workload(client, workload_type, requirements)
            
        except Exception as e:
            logger.error(f"Cloud execution failed: {e}")
            raise