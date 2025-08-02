#!/usr/bin/env python3
import docker
import psutil
import time
import json
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    timestamp: str
    elapsed: float
    cpu: Dict
    memory: Dict
    io: Dict
    network: Dict
    system: Dict

@dataclass
class PerformanceAlert:
    """Performance alert configuration"""
    metric_path: str  # e.g., "cpu.percent", "memory.usage_mb"
    threshold: float
    operator: str  # "gt", "lt", "eq"
    duration: int  # seconds to sustain before alerting
    severity: str  # "warning", "critical"
    message: str

class PerformanceMonitor:
    """Enhanced performance monitoring with real-time capabilities"""
    
    def __init__(self, container_id: str = None, interval: float = 1.0):
        self.container_id = container_id
        self.client = docker.from_env() if container_id else None
        self.interval = interval
        self.metrics: List[PerformanceMetric] = []
        self.alerts: List[PerformanceAlert] = []
        self.alert_callbacks: List[Callable] = []
        self.monitoring = False
        self.monitor_thread = None
        self.alert_state: Dict[str, Dict] = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def add_alert(self, alert: PerformanceAlert):
        """Add performance alert configuration"""
        self.alerts.append(alert)
        self.alert_state[alert.metric_path] = {
            'triggered': False,
            'trigger_time': None,
            'last_value': None
        }
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert, float], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def start_monitoring(self, duration: Optional[float] = None):
        """Start continuous performance monitoring"""
        if self.monitoring:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(duration,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"Started monitoring {'container ' + self.container_id if self.container_id else 'system'}")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped monitoring")
    
    def _monitor_loop(self, duration: Optional[float]):
        """Main monitoring loop"""
        start_time = time.time()
        
        while self.monitoring:
            if duration and (time.time() - start_time) >= duration:
                break
            
            try:
                metric = self._collect_metrics()
                if metric:
                    self.metrics.append(metric)
                    self._check_alerts(metric)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
            
            time.sleep(self.interval)
        
        self.monitoring = False
    
    def _collect_metrics(self) -> Optional[PerformanceMetric]:
        """Collect current performance metrics"""
        try:
            timestamp = datetime.utcnow().isoformat()
            elapsed = time.time() - getattr(self, '_start_time', time.time())
            
            if self.container_id:
                return self._collect_container_metrics(timestamp, elapsed)
            else:
                return self._collect_system_metrics(timestamp, elapsed)
                
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
    
    def _collect_container_metrics(self, timestamp: str, elapsed: float) -> Optional[PerformanceMetric]:
        """Collect metrics from Docker container"""
        try:
            container = self.client.containers.get(self.container_id)
            stats = container.stats(stream=False)
            
            return PerformanceMetric(
                timestamp=timestamp,
                elapsed=elapsed,
                cpu=self._calculate_cpu_percent(stats),
                memory=self._calculate_memory_stats(stats),
                io=self._calculate_io_stats(stats),
                network=self._calculate_network_stats(stats),
                system=self._get_host_system_stats()
            )
            
        except docker.errors.NotFound:
            self.logger.warning(f"Container {self.container_id} not found")
            return None
        except Exception as e:
            self.logger.error(f"Error collecting container metrics: {e}")
            return None
    
    def _collect_system_metrics(self, timestamp: str, elapsed: float) -> PerformanceMetric:
        """Collect system-wide metrics"""
        return PerformanceMetric(
            timestamp=timestamp,
            elapsed=elapsed,
            cpu=self._get_system_cpu_stats(),
            memory=self._get_system_memory_stats(),
            io=self._get_system_io_stats(),
            network=self._get_system_network_stats(),
            system=self._get_host_system_stats()
        )
    
    def _calculate_cpu_percent(self, stats: Dict) -> Dict:
        """Calculate CPU usage percentage from container stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            else:
                cpu_percent = 0.0
            
            throttling = stats['cpu_stats'].get('throttling_data', {})
            per_cpu = stats['cpu_stats']['cpu_usage'].get('percpu_usage', [])
            
            return {
                'percent': round(cpu_percent, 2),
                'throttled_time': throttling.get('throttled_time', 0),
                'throttled_periods': throttling.get('throttled_periods', 0),
                'total_periods': throttling.get('periods', 0),
                'cores_used': len([c for c in per_cpu if c > 0]),
                'system_cpu_usage': stats['cpu_stats']['system_cpu_usage'],
                'user_cpu_usage': stats['cpu_stats']['cpu_usage']['usage_in_usermode'],
                'kernel_cpu_usage': stats['cpu_stats']['cpu_usage']['usage_in_kernelmode']
            }
        except (KeyError, ZeroDivisionError) as e:
            self.logger.debug(f"CPU calculation error: {e}")
            return {'percent': 0.0, 'throttled_time': 0, 'throttled_periods': 0}
    
    def _calculate_memory_stats(self, stats: Dict) -> Dict:
        """Calculate memory usage statistics from container stats"""
        try:
            mem_stats = stats['memory_stats']
            usage = mem_stats['usage']
            limit = mem_stats.get('limit', usage)
            
            # Handle different memory stat formats
            cache = 0
            if 'stats' in mem_stats:
                cache = mem_stats['stats'].get('cache', 0)
            
            rss = mem_stats.get('stats', {}).get('rss', usage)
            swap = mem_stats.get('stats', {}).get('swap', 0)
            
            return {
                'usage_mb': round(usage / 1024 / 1024, 2),
                'limit_mb': round(limit / 1024 / 1024, 2),
                'percent': round((usage / limit) * 100.0, 2) if limit > 0 else 0,
                'cache_mb': round(cache / 1024 / 1024, 2),
                'rss_mb': round(rss / 1024 / 1024, 2),
                'swap_mb': round(swap / 1024 / 1024, 2),
                'available_mb': round((limit - usage) / 1024 / 1024, 2) if limit > usage else 0
            }
        except (KeyError, ZeroDivisionError) as e:
            self.logger.debug(f"Memory calculation error: {e}")
            return {'usage_mb': 0, 'limit_mb': 0, 'percent': 0, 'cache_mb': 0}
    
    def _calculate_io_stats(self, stats: Dict) -> Dict:
        """Calculate I/O statistics from container stats"""
        try:
            io_stats = stats.get('blkio_stats', {})
            io_service_bytes = io_stats.get('io_service_bytes_recursive', [])
            io_serviced = io_stats.get('io_serviced_recursive', [])
            
            read_bytes = sum(s['value'] for s in io_service_bytes if s['op'] == 'Read')
            write_bytes = sum(s['value'] for s in io_service_bytes if s['op'] == 'Write')
            read_ops = sum(s['value'] for s in io_serviced if s['op'] == 'Read')
            write_ops = sum(s['value'] for s in io_serviced if s['op'] == 'Write')
            
            return {
                'read_mb': round(read_bytes / 1024 / 1024, 2),
                'write_mb': round(write_bytes / 1024 / 1024, 2),
                'read_ops': read_ops,
                'write_ops': write_ops,
                'total_mb': round((read_bytes + write_bytes) / 1024 / 1024, 2),
                'total_ops': read_ops + write_ops
            }
        except (KeyError, TypeError) as e:
            self.logger.debug(f"I/O calculation error: {e}")
            return {'read_mb': 0, 'write_mb': 0, 'read_ops': 0, 'write_ops': 0}
    
    def _calculate_network_stats(self, stats: Dict) -> Dict:
        """Calculate network statistics from container stats"""
        try:
            networks = stats.get('networks', {})
            
            rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
            tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
            rx_packets = sum(net.get('rx_packets', 0) for net in networks.values())
            tx_packets = sum(net.get('tx_packets', 0) for net in networks.values())
            rx_errors = sum(net.get('rx_errors', 0) for net in networks.values())
            tx_errors = sum(net.get('tx_errors', 0) for net in networks.values())
            
            return {
                'rx_mb': round(rx_bytes / 1024 / 1024, 2),
                'tx_mb': round(tx_bytes / 1024 / 1024, 2),
                'rx_packets': rx_packets,
                'tx_packets': tx_packets,
                'rx_errors': rx_errors,
                'tx_errors': tx_errors,
                'total_mb': round((rx_bytes + tx_bytes) / 1024 / 1024, 2),
                'total_packets': rx_packets + tx_packets,
                'total_errors': rx_errors + tx_errors
            }
        except (KeyError, TypeError) as e:
            self.logger.debug(f"Network calculation error: {e}")
            return {'rx_mb': 0, 'tx_mb': 0, 'rx_packets': 0, 'tx_packets': 0}
    
    def _get_system_cpu_stats(self) -> Dict:
        """Get system CPU statistics using psutil"""
        try:
            cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
            cpu_times = psutil.cpu_times()
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            return {
                'percent': round(cpu_percent, 2),
                'user': round(cpu_times.user, 2),
                'system': round(cpu_times.system, 2),
                'idle': round(cpu_times.idle, 2),
                'iowait': round(getattr(cpu_times, 'iowait', 0), 2),
                'cores': cpu_count,
                'frequency_mhz': round(cpu_freq.current, 2) if cpu_freq else 0,
                'load_1min': round(load_avg[0], 2),
                'load_5min': round(load_avg[1], 2),
                'load_15min': round(load_avg[2], 2)
            }
        except Exception as e:
            self.logger.debug(f"System CPU stats error: {e}")
            return {'percent': 0.0, 'cores': 1}
    
    def _get_system_memory_stats(self) -> Dict:
        """Get system memory statistics using psutil"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'usage_mb': round((mem.total - mem.available) / 1024 / 1024, 2),
                'total_mb': round(mem.total / 1024 / 1024, 2),
                'available_mb': round(mem.available / 1024 / 1024, 2),
                'percent': round(mem.percent, 2),
                'free_mb': round(mem.free / 1024 / 1024, 2),
                'cached_mb': round(getattr(mem, 'cached', 0) / 1024 / 1024, 2),
                'buffers_mb': round(getattr(mem, 'buffers', 0) / 1024 / 1024, 2),
                'swap_total_mb': round(swap.total / 1024 / 1024, 2),
                'swap_used_mb': round(swap.used / 1024 / 1024, 2),
                'swap_percent': round(swap.percent, 2)
            }
        except Exception as e:
            self.logger.debug(f"System memory stats error: {e}")
            return {'usage_mb': 0, 'total_mb': 0, 'percent': 0}
    
    def _get_system_io_stats(self) -> Dict:
        """Get system I/O statistics using psutil"""
        try:
            io_counters = psutil.disk_io_counters()
            if not io_counters:
                return {'read_mb': 0, 'write_mb': 0}
            
            return {
                'read_mb': round(io_counters.read_bytes / 1024 / 1024, 2),
                'write_mb': round(io_counters.write_bytes / 1024 / 1024, 2),
                'read_ops': io_counters.read_count,
                'write_ops': io_counters.write_count,
                'read_time_ms': io_counters.read_time,
                'write_time_ms': io_counters.write_time
            }
        except Exception as e:
            self.logger.debug(f"System I/O stats error: {e}")
            return {'read_mb': 0, 'write_mb': 0}
    
    def _get_system_network_stats(self) -> Dict:
        """Get system network statistics using psutil"""
        try:
            net_io = psutil.net_io_counters()
            if not net_io:
                return {'rx_mb': 0, 'tx_mb': 0}
            
            return {
                'rx_mb': round(net_io.bytes_recv / 1024 / 1024, 2),
                'tx_mb': round(net_io.bytes_sent / 1024 / 1024, 2),
                'rx_packets': net_io.packets_recv,
                'tx_packets': net_io.packets_sent,
                'rx_errors': net_io.errin,
                'tx_errors': net_io.errout,
                'rx_dropped': net_io.dropin,
                'tx_dropped': net_io.dropout
            }
        except Exception as e:
            self.logger.debug(f"System network stats error: {e}")
            return {'rx_mb': 0, 'tx_mb': 0}
    
    def _get_host_system_stats(self) -> Dict:
        """Get host system information"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'uptime_hours': round(uptime.total_seconds() / 3600, 2),
                'boot_time': boot_time.isoformat(),
                'processes': len(psutil.pids()),
                'users': len(psutil.users()) if hasattr(psutil, 'users') else 0,
                'platform': psutil.uname()._asdict() if hasattr(psutil, 'uname') else {}
            }
        except Exception as e:
            self.logger.debug(f"Host system stats error: {e}")
            return {'uptime_hours': 0}
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check performance alerts against current metric"""
        for alert in self.alerts:
            try:
                value = self._get_metric_value(metric, alert.metric_path)
                if value is None:
                    continue
                
                alert_state = self.alert_state[alert.metric_path]
                should_trigger = self._evaluate_alert_condition(value, alert)
                
                if should_trigger and not alert_state['triggered']:
                    # Start timing the alert condition
                    alert_state['trigger_time'] = time.time()
                    alert_state['triggered'] = True
                    
                elif not should_trigger and alert_state['triggered']:
                    # Reset alert state
                    alert_state['triggered'] = False
                    alert_state['trigger_time'] = None
                
                # Check if alert duration threshold is met
                if (alert_state['triggered'] and 
                    alert_state['trigger_time'] and
                    time.time() - alert_state['trigger_time'] >= alert.duration):
                    
                    self._fire_alert(alert, value)
                    # Reset to prevent repeated firing
                    alert_state['trigger_time'] = time.time()
                
                alert_state['last_value'] = value
                
            except Exception as e:
                self.logger.error(f"Error checking alert {alert.metric_path}: {e}")
    
    def _get_metric_value(self, metric: PerformanceMetric, path: str) -> Optional[float]:
        """Extract metric value by path (e.g., 'cpu.percent', 'memory.usage_mb')"""
        try:
            parts = path.split('.')
            value = asdict(metric)
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            
            return float(value) if isinstance(value, (int, float)) else None
        except (ValueError, KeyError, TypeError):
            return None
    
    def _evaluate_alert_condition(self, value: float, alert: PerformanceAlert) -> bool:
        """Evaluate if alert condition is met"""
        if alert.operator == 'gt':
            return value > alert.threshold
        elif alert.operator == 'lt':
            return value < alert.threshold
        elif alert.operator == 'eq':
            return abs(value - alert.threshold) < 0.01
        elif alert.operator == 'gte':
            return value >= alert.threshold
        elif alert.operator == 'lte':
            return value <= alert.threshold
        else:
            return False
    
    def _fire_alert(self, alert: PerformanceAlert, value: float):
        """Fire performance alert"""
        self.logger.warning(f"ALERT [{alert.severity.upper()}]: {alert.message} (value: {value})")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert, value)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def get_summary(self) -> Dict:
        """Generate comprehensive performance summary"""
        if not self.metrics:
            return {}
        
        cpu_values = [m.cpu.get('percent', 0) for m in self.metrics]
        memory_values = [m.memory.get('usage_mb', 0) for m in self.metrics]
        io_read_values = [m.io.get('read_mb', 0) for m in self.metrics]
        io_write_values = [m.io.get('write_mb', 0) for m in self.metrics]
        
        return {
            'collection_info': {
                'start_time': self.metrics[0].timestamp,
                'end_time': self.metrics[-1].timestamp,
                'duration_seconds': self.metrics[-1].elapsed,
                'sample_count': len(self.metrics),
                'sample_interval': self.interval
            },
            'cpu': {
                'max_percent': max(cpu_values) if cpu_values else 0,
                'avg_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'min_percent': min(cpu_values) if cpu_values else 0,
                'p95_percent': self._percentile(cpu_values, 95) if cpu_values else 0,
                'p99_percent': self._percentile(cpu_values, 99) if cpu_values else 0
            },
            'memory': {
                'max_mb': max(memory_values) if memory_values else 0,
                'avg_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
                'min_mb': min(memory_values) if memory_values else 0,
                'p95_mb': self._percentile(memory_values, 95) if memory_values else 0,
                'p99_mb': self._percentile(memory_values, 99) if memory_values else 0
            },
            'io': {
                'total_read_mb': max(io_read_values) if io_read_values else 0,
                'total_write_mb': max(io_write_values) if io_write_values else 0,
                'peak_read_mb': max(io_read_values) if io_read_values else 0,
                'peak_write_mb': max(io_write_values) if io_write_values else 0
            },
            'alerts': {
                'total_configured': len(self.alerts),
                'currently_triggered': sum(1 for state in self.alert_state.values() if state['triggered'])
            }
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def save_metrics(self, filename: str, include_raw: bool = True):
        """Save metrics to JSON file"""
        data = {
            'container_id': self.container_id,
            'monitoring_config': {
                'interval': self.interval,
                'alerts_configured': len(self.alerts)
            },
            'summary': self.get_summary()
        }
        
        if include_raw:
            data['raw_metrics'] = [asdict(m) for m in self.metrics]
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved {len(self.metrics)} metrics to {filename}")
    
    def export_csv(self, filename: str):
        """Export metrics to CSV format"""
        import csv
        
        if not self.metrics:
            return
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'timestamp', 'elapsed', 'cpu_percent', 'memory_mb', 'memory_percent',
                'io_read_mb', 'io_write_mb', 'network_rx_mb', 'network_tx_mb'
            ])
            
            # Data rows
            for metric in self.metrics:
                writer.writerow([
                    metric.timestamp,
                    metric.elapsed,
                    metric.cpu.get('percent', 0),
                    metric.memory.get('usage_mb', 0),
                    metric.memory.get('percent', 0),
                    metric.io.get('read_mb', 0),
                    metric.io.get('write_mb', 0),
                    metric.network.get('rx_mb', 0),
                    metric.network.get('tx_mb', 0)
                ])
        
        self.logger.info(f"Exported metrics to CSV: {filename}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, stopping monitoring...")
        self.stop_monitoring()


# Alert callback functions
def console_alert_callback(alert: PerformanceAlert, value: float):
    """Print alert to console with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    severity_emoji = '🚨' if alert.severity == 'critical' else '⚠️'
    print(f"{timestamp} {severity_emoji} [{alert.severity.upper()}] {alert.message} (value: {value})")

def json_alert_callback(alert: PerformanceAlert, value: float, log_file: str = 'alerts.json'):
    """Log alert to JSON file"""
    alert_record = {
        'timestamp': datetime.utcnow().isoformat(),
        'alert': {
            'metric_path': alert.metric_path,
            'threshold': alert.threshold,
            'operator': alert.operator,
            'severity': alert.severity,
            'message': alert.message
        },
        'value': value
    }
    
    # Append to alerts log file
    try:
        alerts_log = []
        if Path(log_file).exists():
            with open(log_file, 'r') as f:
                alerts_log = json.load(f)
        
        alerts_log.append(alert_record)
        
        with open(log_file, 'w') as f:
            json.dump(alerts_log, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to log alert to {log_file}: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced Performance Monitor for Docker containers and systems'
    )
    parser.add_argument('--container', '-c', help='Docker container ID to monitor')
    parser.add_argument('--duration', '-d', type=float, help='Monitoring duration in seconds')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Collection interval in seconds')
    parser.add_argument('--output', '-o', default='performance-metrics.json', help='Output file')
    parser.add_argument('--csv', help='Also export to CSV file')
    parser.add_argument('--alert-cpu', type=float, help='CPU usage alert threshold (percent)')
    parser.add_argument('--alert-memory', type=float, help='Memory usage alert threshold (MB)')
    parser.add_argument('--alert-duration', type=int, default=5, help='Alert duration threshold (seconds)')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = PerformanceMonitor(
        container_id=args.container,
        interval=args.interval
    )
    
    # Setup alerts
    if args.alert_cpu:
        cpu_alert = PerformanceAlert(
            metric_path='cpu.percent',
            threshold=args.alert_cpu,
            operator='gt',
            duration=args.alert_duration,
            severity='warning',
            message=f'High CPU usage detected (>{args.alert_cpu}%)'
        )
        monitor.add_alert(cpu_alert)
    
    if args.alert_memory:
        memory_alert = PerformanceAlert(
            metric_path='memory.usage_mb',
            threshold=args.alert_memory,
            operator='gt',
            duration=args.alert_duration,
            severity='warning',
            message=f'High memory usage detected (>{args.alert_memory}MB)'
        )
        monitor.add_alert(memory_alert)
    
    # Setup alert callbacks
    if not args.quiet:
        monitor.add_alert_callback(console_alert_callback)
    
    monitor.add_alert_callback(
        lambda alert, value: json_alert_callback(alert, value, 'performance-alerts.json')
    )
    
    try:
        print(f"Starting performance monitoring...")
        if args.container:
            print(f"  Container: {args.container}")
        else:
            print("  Target: System-wide monitoring")
        print(f"  Interval: {args.interval}s")
        if args.duration:
            print(f"  Duration: {args.duration}s")
        print(f"  Output: {args.output}")
        
        monitor.start_monitoring(args.duration)
        
        # Wait for monitoring to complete
        if args.duration:
            time.sleep(args.duration + 1)  # Extra second for cleanup
        else:
            try:
                while monitor.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
        
        monitor.stop_monitoring()
        
        # Save results
        monitor.save_metrics(args.output)
        if args.csv:
            monitor.export_csv(args.csv)
        
        # Print summary
        summary = monitor.get_summary()
        if summary and not args.quiet:
            print(f"\nPerformance Summary:")
            print(f"  Duration: {summary['collection_info']['duration_seconds']:.1f}s")
            print(f"  Samples: {summary['collection_info']['sample_count']}")
            print(f"  CPU - Avg: {summary['cpu']['avg_percent']:.1f}%, Max: {summary['cpu']['max_percent']:.1f}%")
            print(f"  Memory - Avg: {summary['memory']['avg_mb']:.1f}MB, Max: {summary['memory']['max_mb']:.1f}MB")
            if summary['alerts']['total_configured'] > 0:
                print(f"  Alerts: {summary['alerts']['currently_triggered']} active of {summary['alerts']['total_configured']} configured")
    
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)