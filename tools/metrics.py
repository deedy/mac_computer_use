from prometheus_client import Counter, Histogram, Gauge
import psutil

class ActivityMetrics:
    """Activity Monitor metrics for Prometheus"""
    
    # Process metrics
    PROCESS_COUNT = Gauge(
        'process_count_total',
        'Total number of processes',
        ['state']
    )
    
    PROCESS_CPU = Gauge(
        'process_cpu_percent',
        'Process CPU usage percentage',
        ['pid', 'name']
    )
    
    PROCESS_MEMORY = Gauge(
        'process_memory_bytes',
        'Process memory usage in bytes',
        ['pid', 'name']
    )
    
    # System metrics
    CPU_USAGE = Gauge(
        'system_cpu_percent',
        'System CPU usage percentage',
        ['cpu']
    )
    
    MEMORY_USAGE = Gauge(
        'system_memory_bytes',
        'System memory usage in bytes',
        ['type']
    )
    
    DISK_IO = Counter(
        'system_disk_io_bytes',
        'Disk I/O in bytes',
        ['device', 'type']
    )
    
    NETWORK_IO = Counter(
        'system_network_io_bytes',
        'Network I/O in bytes',
        ['interface', 'direction']
    )
    
    @classmethod
    async def collect_metrics(cls):
        """Collect and update all metrics"""
        # Process metrics
        process_states = {'running': 0, 'sleeping': 0, 'stopped': 0, 'zombie': 0}
        
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                process_states[proc.status().lower()] += 1
                cls.PROCESS_CPU.labels(
                    pid=proc.pid,
                    name=proc.name()
                ).set(proc.cpu_percent())
                cls.PROCESS_MEMORY.labels(
                    pid=proc.pid,
                    name=proc.name()
                ).set(proc.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        for state, count in process_states.items():
            cls.PROCESS_COUNT.labels(state=state).set(count)
            
        # CPU metrics
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
            cls.CPU_USAGE.labels(cpu=f'cpu{i}').set(percentage)
            
        # Memory metrics
        mem = psutil.virtual_memory()
        cls.MEMORY_USAGE.labels(type='total').set(mem.total)
        cls.MEMORY_USAGE.labels(type='used').set(mem.used)
        cls.MEMORY_USAGE.labels(type='free').set(mem.available)
        cls.MEMORY_USAGE.labels(type='cached').set(mem.cached)
        
        # Disk I/O metrics
        disk_io = psutil.disk_io_counters(perdisk=True)
        for device, counters in disk_io.items():
            cls.DISK_IO.labels(device=device, type='read').inc(counters.read_bytes)
            cls.DISK_IO.labels(device=device, type='write').inc(counters.write_bytes)
            
        # Network I/O metrics
        net_io = psutil.net_io_counters(pernic=True)
        for interface, counters in net_io.items():
            cls.NETWORK_IO.labels(interface=interface, direction='sent').inc(
                counters.bytes_sent
            )
            cls.NETWORK_IO.labels(interface=interface, direction='received').inc(
                counters.bytes_recv
            ) 