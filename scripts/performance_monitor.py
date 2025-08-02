#!/usr/bin/env python3
import docker
import psutil
import time
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, container_id: str):
        self.container_id = container_id
        self.client = docker.from_env()
        self.metrics: List[Dict] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self, interval: float = 1.0, duration: Optional[float] = None):
        """Start monitoring container performance metrics"""
        if self._monitoring:
            logger.warning("Monitoring already started")
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval, duration),
            daemon=True
        )
        self._monitor_thread.start()
        logger.debug(f"Started monitoring container {self.container_id}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        logger.debug(f"Stopped monitoring container {self.container_id}")
    
    def _monitor_loop(self, interval: float, duration: Optional[float]):
        """Main monitoring loop"""
        start_time = time.time()
        
        while self._monitoring:
            if duration and (time.time() - start_time) >= duration:
                break
                
            try:
                container = self.client.containers.get(self.container_id)
                stats = container.stats(stream=False)
                
                metric = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'elapsed': time.time() - start_time,
                    'cpu': self._calculate_cpu_percent(stats),
                    'memory': self._calculate_memory_stats(stats),
                    'io': self._calculate_io_stats(stats),
                    'network': self._calculate_network_stats(stats),
                    'pids': self._calculate_pid_stats(stats)
                }
                
                self.metrics.append(metric)
                
            except docker.errors.NotFound:
                logger.debug(f"Container {self.container_id} not found, stopping monitoring")
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                
            time.sleep(interval)
        
        self._monitoring = False
    
    def _calculate_cpu_percent(self, stats: Dict) -> Dict:
        """Calculate CPU usage percentage"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            else:
                cpu_percent = 0.0
                
            # Get throttling information
            throttling_data = stats['cpu_stats'].get('throttling_data', {})
            
            return {
                'percent': round(cpu_percent, 2),
                'throttled_time': throttling_data.get('throttled_time', 0),
                'throttled_periods': throttling_data.get('throttled_periods', 0),
                'total_periods': throttling_data.get('periods', 0)
            }
        except (KeyError, ZeroDivisionError):
            return {'percent': 0.0, 'throttled_time': 0, 'throttled_periods': 0, 'total_periods': 0}
    
    def _calculate_memory_stats(self, stats: Dict) -> Dict:
        """Calculate memory usage statistics"""
        try:
            mem_stats = stats['memory_stats']
            usage = mem_stats['usage']
            limit = mem_stats['limit']
            
            # Get detailed memory breakdown
            mem_details = mem_stats.get('stats', {})
            cache = mem_details.get('cache', 0)
            rss = mem_details.get('rss', 0)
            swap = mem_details.get('swap', 0)
            
            return {
                'usage_mb': round(usage / 1024 / 1024, 2),
                'limit_mb': round(limit / 1024 / 1024, 2),
                'percent': round((usage / limit) * 100.0, 2),
                'cache_mb': round(cache / 1024 / 1024, 2),
                'rss_mb': round(rss / 1024 / 1024, 2),
                'swap_mb': round(swap / 1024 / 1024, 2)
            }
        except (KeyError, ZeroDivisionError):
            return {'usage_mb': 0, 'limit_mb': 0, 'percent': 0, 'cache_mb': 0, 'rss_mb': 0, 'swap_mb': 0}
    
    def _calculate_io_stats(self, stats: Dict) -> Dict:
        """Calculate I/O statistics"""
        try:
            io_stats = stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [])
            
            read_bytes = sum(s.get('value', 0) for s in io_stats if s.get('op') == 'Read')
            write_bytes = sum(s.get('value', 0) for s in io_stats if s.get('op') == 'Write')
            
            # Get I/O operations count
            io_ops = stats.get('blkio_stats', {}).get('io_serviced_recursive', [])
            read_ops = sum(s.get('value', 0) for s in io_ops if s.get('op') == 'Read')
            write_ops = sum(s.get('value', 0) for s in io_ops if s.get('op') == 'Write')
            
            return {
                'read_mb': round(read_bytes / 1024 / 1024, 2),
                'write_mb': round(write_bytes / 1024 / 1024, 2),
                'read_ops': read_ops,
                'write_ops': write_ops
            }
        except KeyError:
            return {'read_mb': 0, 'write_mb': 0, 'read_ops': 0, 'write_ops': 0}
    
    def _calculate_network_stats(self, stats: Dict) -> Dict:
        """Calculate network statistics"""
        try:
            networks = stats.get('networks', {})
            
            rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
            tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
            rx_packets = sum(net.get('rx_packets', 0) for net in networks.values())
            tx_packets = sum(net.get('tx_packets', 0) for net in networks.values())
            
            return {
                'rx_mb': round(rx_bytes / 1024 / 1024, 2),
                'tx_mb': round(tx_bytes / 1024 / 1024, 2),
                'rx_packets': rx_packets,
                'tx_packets': tx_packets
            }
        except KeyError:
            return {'rx_mb': 0, 'tx_mb': 0, 'rx_packets': 0, 'tx_packets': 0}
    
    def _calculate_pid_stats(self, stats: Dict) -> Dict:
        """Calculate process/thread statistics"""
        try:
            pids_stats = stats.get('pids_stats', {})
            current = pids_stats.get('current', 0)
            limit = pids_stats.get('limit', 0)
            
            return {
                'current': current,
                'limit': limit,
                'percent': round((current / limit) * 100.0, 2) if limit > 0 else 0
            }
        except (KeyError, ZeroDivisionError):
            return {'current': 0, 'limit': 0, 'percent': 0}
    
    def get_summary(self) -> Dict:
        """Generate performance summary"""
        if not self.metrics:
            return {}
            
        cpu_values = [m['cpu']['percent'] for m in self.metrics]
        memory_values = [m['memory']['usage_mb'] for m in self.metrics]
        io_read_values = [m['io']['read_mb'] for m in self.metrics]
        io_write_values = [m['io']['write_mb'] for m in self.metrics]
        
        return {
            'container_id': self.container_id,
            'duration': self.metrics[-1]['elapsed'] if self.metrics else 0,
            'samples': len(self.metrics),
            'cpu': {
                'max_percent': max(cpu_values) if cpu_values else 0,
                'avg_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'min_percent': min(cpu_values) if cpu_values else 0,
                'throttled_periods': self.metrics[-1]['cpu']['throttled_periods'] if self.metrics else 0
            },
            'memory': {
                'max_mb': max(memory_values) if memory_values else 0,
                'avg_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
                'min_mb': min(memory_values) if memory_values else 0,
                'peak_percent': max(m['memory']['percent'] for m in self.metrics) if self.metrics else 0
            },
            'io': {
                'total_read_mb': max(io_read_values) if io_read_values else 0,
                'total_write_mb': max(io_write_values) if io_write_values else 0,
                'total_read_ops': self.metrics[-1]['io']['read_ops'] if self.metrics else 0,
                'total_write_ops': self.metrics[-1]['io']['write_ops'] if self.metrics else 0
            },
            'network': {
                'total_rx_mb': self.metrics[-1]['network']['rx_mb'] if self.metrics else 0,
                'total_tx_mb': self.metrics[-1]['network']['tx_mb'] if self.metrics else 0,
                'total_rx_packets': self.metrics[-1]['network']['rx_packets'] if self.metrics else 0,
                'total_tx_packets': self.metrics[-1]['network']['tx_packets'] if self.metrics else 0
            }
        }
    
    def get_metrics(self) -> List[Dict]:
        """Get all collected metrics"""
        return self.metrics.copy()
    
    def save_metrics(self, filename: str):
        """Save metrics to JSON file"""
        data = {
            'summary': self.get_summary(),
            'metrics': self.metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved metrics to {filename}")
    
    def get_alerts(self, thresholds: Optional[Dict] = None) -> List[Dict]:
        """Check for performance alerts based on thresholds"""
        if not self.metrics:
            return []
        
        if thresholds is None:
            thresholds = {
                'cpu_percent': 90.0,
                'memory_percent': 90.0,
                'throttled_periods': 10,
                'swap_mb': 50.0
            }
        
        alerts = []
        summary = self.get_summary()
        
        # CPU alerts
        if summary['cpu']['max_percent'] > thresholds.get('cpu_percent', 90.0):
            alerts.append({
                'type': 'high_cpu',
                'severity': 'warning',
                'message': f"High CPU usage: {summary['cpu']['max_percent']:.1f}%",
                'value': summary['cpu']['max_percent']
            })
        
        if summary['cpu']['throttled_periods'] > thresholds.get('throttled_periods', 10):
            alerts.append({
                'type': 'cpu_throttling',
                'severity': 'warning',
                'message': f"CPU throttling detected: {summary['cpu']['throttled_periods']} periods",
                'value': summary['cpu']['throttled_periods']
            })
        
        # Memory alerts
        if summary['memory']['peak_percent'] > thresholds.get('memory_percent', 90.0):
            alerts.append({
                'type': 'high_memory',
                'severity': 'warning',
                'message': f"High memory usage: {summary['memory']['peak_percent']:.1f}%",
                'value': summary['memory']['peak_percent']
            })
        
        # Check for swap usage
        max_swap = max((m['memory']['swap_mb'] for m in self.metrics), default=0)
        if max_swap > thresholds.get('swap_mb', 50.0):
            alerts.append({
                'type': 'swap_usage',
                'severity': 'warning',
                'message': f"Swap usage detected: {max_swap:.1f}MB",
                'value': max_swap
            })
        
        return alerts

class MultiContainerMonitor:
    """Monitor multiple containers simultaneously"""
    
    def __init__(self):
        self.monitors: Dict[str, PerformanceMonitor] = {}
    
    def add_container(self, container_id: str) -> PerformanceMonitor:
        """Add a container to monitor"""
        if container_id not in self.monitors:
            self.monitors[container_id] = PerformanceMonitor(container_id)
        return self.monitors[container_id]
    
    def start_all(self, interval: float = 1.0, duration: Optional[float] = None):
        """Start monitoring all containers"""
        for monitor in self.monitors.values():
            monitor.start_monitoring(interval, duration)
    
    def stop_all(self):
        """Stop monitoring all containers"""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()
    
    def get_summary_report(self) -> Dict:
        """Get a summary report for all monitored containers"""
        report = {
            'total_containers': len(self.monitors),
            'containers': {}
        }
        
        for container_id, monitor in self.monitors.items():
            report['containers'][container_id] = monitor.get_summary()
        
        # Calculate aggregate metrics
        if self.monitors:
            all_summaries = [m.get_summary() for m in self.monitors.values()]
            report['aggregate'] = {
                'total_cpu_max': sum(s.get('cpu', {}).get('max_percent', 0) for s in all_summaries),
                'total_memory_max': sum(s.get('memory', {}).get('max_mb', 0) for s in all_summaries),
                'total_duration': max(s.get('duration', 0) for s in all_summaries),
                'total_samples': sum(s.get('samples', 0) for s in all_summaries)
            }
        
        return report
    
    def get_all_alerts(self, thresholds: Optional[Dict] = None) -> Dict[str, List[Dict]]:
        """Get alerts for all monitored containers"""
        alerts = {}
        for container_id, monitor in self.monitors.items():
            container_alerts = monitor.get_alerts(thresholds)
            if container_alerts:
                alerts[container_id] = container_alerts
        return alerts

if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Monitor Docker container performance')
    parser.add_argument('container_id', help='Container ID to monitor')
    parser.add_argument('--duration', type=float, default=60, help='Monitoring duration in seconds')
    parser.add_argument('--interval', type=float, default=1.0, help='Sampling interval in seconds')
    parser.add_argument('--output', help='Output file for metrics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        monitor = PerformanceMonitor(args.container_id)
        
        print(f"Starting monitoring of container {args.container_id} for {args.duration}s")
        monitor.start_monitoring(args.interval, args.duration)
        
        # Wait for monitoring to complete
        time.sleep(args.duration + 1)
        monitor.stop_monitoring()
        
        # Get results
        summary = monitor.get_summary()
        alerts = monitor.get_alerts()
        
        print("\nPerformance Summary:")
        print(json.dumps(summary, indent=2))
        
        if alerts:
            print("\nAlerts:")
            for alert in alerts:
                print(f"  {alert['severity'].upper()}: {alert['message']}")
        
        if args.output:
            monitor.save_metrics(args.output)
            print(f"\nMetrics saved to {args.output}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)