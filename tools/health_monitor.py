from dataclasses import dataclass
from typing import Dict, List
import psutil
import docker

@dataclass
class ContainerHealth:
    container_id: str
    name: str
    cpu_percent: float
    memory_usage: int
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    status: str

class HealthMonitor:
    """Monitor container and system health"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        
    async def get_container_stats(self) -> List[ContainerHealth]:
        """Get health metrics for all running containers"""
        containers = []
        for container in self.docker_client.containers.list():
            stats = container.stats(stream=False)
            
            health = ContainerHealth(
                container_id=container.id,
                name=container.name,
                cpu_percent=self._calculate_cpu_percent(stats),
                memory_usage=stats["memory_stats"]["usage"],
                network_io={
                    "rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
                    "tx_bytes": stats["networks"]["eth0"]["tx_bytes"]
                },
                disk_io={
                    "read_bytes": stats["blkio_stats"]["io_service_bytes_recursive"][0]["value"],
                    "write_bytes": stats["blkio_stats"]["io_service_bytes_recursive"][1]["value"]
                },
                status=container.status
            )
            containers.append(health)
        return containers
    
    def _calculate_cpu_percent(self, stats: dict) -> float:
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                      stats["precpu_stats"]["system_cpu_usage"]
        return (cpu_delta / system_delta) * 100.0 