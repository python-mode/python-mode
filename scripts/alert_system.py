#!/usr/bin/env python3
"""
Proactive Alert System for Python-mode Test Infrastructure

This module provides comprehensive alerting capabilities including performance
monitoring, trend-based predictions, failure detection, and multi-channel
notification delivery with intelligent aggregation and escalation.
"""

import json
import smtplib
import requests
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from collections import defaultdict, deque
import logging

# Import our other modules
try:
    from .trend_analysis import TrendAnalyzer
    from .performance_monitor import PerformanceAlert
    from .optimization_engine import OptimizationEngine
except ImportError:
    from trend_analysis import TrendAnalyzer
    from performance_monitor import PerformanceAlert
    from optimization_engine import OptimizationEngine

@dataclass
class Alert:
    """Individual alert definition"""
    id: str
    timestamp: str
    severity: str  # 'info', 'warning', 'critical', 'emergency'
    category: str  # 'performance', 'regression', 'failure', 'optimization', 'system'
    title: str
    message: str
    source: str  # Component that generated the alert
    metadata: Dict[str, Any]
    tags: List[str] = None
    escalation_level: int = 0
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[str] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    description: str
    category: str
    severity: str
    condition: str  # Python expression for alert condition
    threshold: float
    duration: int  # Seconds condition must persist
    cooldown: int  # Seconds before re-alerting
    enabled: bool = True
    tags: List[str] = None
    escalation_rules: List[Dict] = None

@dataclass
class NotificationChannel:
    """Notification delivery channel"""
    id: str
    name: str
    type: str  # 'email', 'webhook', 'slack', 'file', 'console'
    config: Dict[str, Any]
    enabled: bool = True
    severity_filter: List[str] = None  # Only alert for these severities
    category_filter: List[str] = None  # Only alert for these categories

class AlertAggregator:
    """Intelligent alert aggregation to prevent spam"""
    
    def __init__(self, window_size: int = 300):  # 5 minutes
        self.window_size = window_size
        self.alert_buffer = deque()
        self.aggregation_rules = {
            'similar_alerts': {
                'group_by': ['category', 'source'],
                'threshold': 5,  # Aggregate after 5 similar alerts
                'window': 300
            },
            'escalation_alerts': {
                'group_by': ['severity'],
                'threshold': 3,  # Escalate after 3 critical alerts
                'window': 600
            }
        }
    
    def add_alert(self, alert: Alert) -> Optional[Alert]:
        """Add alert and return aggregated alert if threshold met"""
        now = time.time()
        alert_time = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp()
        
        # Add to buffer
        self.alert_buffer.append((alert_time, alert))
        
        # Clean old alerts
        cutoff_time = now - self.window_size
        while self.alert_buffer and self.alert_buffer[0][0] < cutoff_time:
            self.alert_buffer.popleft()
        
        # Check aggregation rules
        for rule_name, rule in self.aggregation_rules.items():
            aggregated = self._check_aggregation_rule(alert, rule)
            if aggregated:
                return aggregated
        
        return None
    
    def _check_aggregation_rule(self, current_alert: Alert, rule: Dict) -> Optional[Alert]:
        """Check if aggregation rule is triggered"""
        group_keys = rule['group_by']
        threshold = rule['threshold']
        window = rule['window']
        
        # Find similar alerts in window
        cutoff_time = time.time() - window
        similar_alerts = []
        
        for alert_time, alert in self.alert_buffer:
            if alert_time < cutoff_time:
                continue
            
            # Check if alert matches grouping criteria
            matches = True
            for key in group_keys:
                if getattr(alert, key, None) != getattr(current_alert, key, None):
                    matches = False
                    break
            
            if matches:
                similar_alerts.append(alert)
        
        # Check if threshold is met
        if len(similar_alerts) >= threshold:
            return self._create_aggregated_alert(similar_alerts, rule)
        
        return None
    
    def _create_aggregated_alert(self, alerts: List[Alert], rule: Dict) -> Alert:
        """Create aggregated alert from multiple similar alerts"""
        first_alert = alerts[0]
        count = len(alerts)
        
        # Determine aggregated severity (highest)
        severity_order = ['info', 'warning', 'critical', 'emergency']
        max_severity = max(alerts, key=lambda a: severity_order.index(a.severity)).severity
        
        # Create aggregated alert
        return Alert(
            id=f"agg_{first_alert.category}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            severity=max_severity,
            category=first_alert.category,
            title=f"Multiple {first_alert.category} alerts",
            message=f"{count} similar alerts in the last {rule['window']}s: {first_alert.title}",
            source="alert_aggregator",
            metadata={
                'aggregated_count': count,
                'original_alerts': [a.id for a in alerts],
                'aggregation_rule': rule
            },
            tags=['aggregated'] + (first_alert.tags or [])
        )

class AlertSystem:
    """Comprehensive alert management system"""
    
    def __init__(self, config_file: str = "alert_config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.trend_analyzer = TrendAnalyzer()
        self.optimization_engine = OptimizationEngine()
        self.aggregator = AlertAggregator()
        
        # Load configuration
        self.alert_rules = {}
        self.notification_channels = {}
        self.load_configuration()
        
        # Alert storage
        self.active_alerts = {}
        self.alert_history = []
        self.rule_state = {}  # Track rule state for duration/cooldown
        
        # Background processing
        self.running = False
        self.processor_thread = None
        self.alert_queue = deque()
        
        # Load persistent state
        self.load_alert_state()
    
    def load_configuration(self):
        """Load alert system configuration"""
        default_config = self._get_default_configuration()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Load alert rules
                for rule_data in config.get('alert_rules', []):
                    rule = AlertRule(**rule_data)
                    self.alert_rules[rule.id] = rule
                
                # Load notification channels
                for channel_data in config.get('notification_channels', []):
                    channel = NotificationChannel(**channel_data)
                    self.notification_channels[channel.id] = channel
                    
            except Exception as e:
                self.logger.error(f"Failed to load alert configuration: {e}")
                self._create_default_configuration()
        else:
            self._create_default_configuration()
    
    def _get_default_configuration(self) -> Dict:
        """Get default alert configuration"""
        return {
            'alert_rules': [
                {
                    'id': 'high_test_duration',
                    'name': 'High Test Duration',
                    'description': 'Alert when test duration exceeds threshold',
                    'category': 'performance',
                    'severity': 'warning',
                    'condition': 'duration > threshold',
                    'threshold': 120.0,
                    'duration': 60,
                    'cooldown': 300,
                    'tags': ['performance', 'duration']
                },
                {
                    'id': 'test_failure_rate',
                    'name': 'High Test Failure Rate',
                    'description': 'Alert when test failure rate is high',
                    'category': 'failure',
                    'severity': 'critical',
                    'condition': 'failure_rate > threshold',
                    'threshold': 0.15,
                    'duration': 300,
                    'cooldown': 600,
                    'tags': ['failure', 'reliability']
                },
                {
                    'id': 'memory_usage_high',
                    'name': 'High Memory Usage',
                    'description': 'Alert when memory usage is consistently high',
                    'category': 'performance',
                    'severity': 'warning',
                    'condition': 'memory_mb > threshold',
                    'threshold': 200.0,
                    'duration': 180,
                    'cooldown': 300,
                    'tags': ['memory', 'resources']
                },
                {
                    'id': 'performance_regression',
                    'name': 'Performance Regression Detected',
                    'description': 'Alert when performance regression is detected',
                    'category': 'regression',
                    'severity': 'critical',
                    'condition': 'regression_severity > threshold',
                    'threshold': 20.0,
                    'duration': 0,  # Immediate
                    'cooldown': 1800,
                    'tags': ['regression', 'performance']
                }
            ],
            'notification_channels': [
                {
                    'id': 'console',
                    'name': 'Console Output',
                    'type': 'console',
                    'config': {},
                    'severity_filter': ['warning', 'critical', 'emergency']
                },
                {
                    'id': 'log_file',
                    'name': 'Log File',
                    'type': 'file',
                    'config': {'file_path': 'alerts.log'},
                    'severity_filter': None  # All severities
                }
            ]
        }
    
    def _create_default_configuration(self):
        """Create default configuration file"""
        default_config = self._get_default_configuration()
        
        # Convert to proper format
        self.alert_rules = {}
        for rule_data in default_config['alert_rules']:
            rule = AlertRule(**rule_data)
            self.alert_rules[rule.id] = rule
        
        self.notification_channels = {}
        for channel_data in default_config['notification_channels']:
            channel = NotificationChannel(**channel_data)
            self.notification_channels[channel.id] = channel
        
        self.save_configuration()
    
    def save_configuration(self):
        """Save current configuration to file"""
        config = {
            'alert_rules': [asdict(rule) for rule in self.alert_rules.values()],
            'notification_channels': [asdict(channel) for channel in self.notification_channels.values()]
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_alert_state(self):
        """Load persistent alert state"""
        state_file = self.config_file.parent / "alert_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                # Load active alerts
                for alert_data in state.get('active_alerts', []):
                    alert = Alert(**alert_data)
                    self.active_alerts[alert.id] = alert
                
                # Load rule state
                self.rule_state = state.get('rule_state', {})
                
            except Exception as e:
                self.logger.error(f"Failed to load alert state: {e}")
    
    def save_alert_state(self):
        """Save persistent alert state"""
        state = {
            'active_alerts': [asdict(alert) for alert in self.active_alerts.values()],
            'rule_state': self.rule_state,
            'last_saved': datetime.utcnow().isoformat()
        }
        
        state_file = self.config_file.parent / "alert_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def start_monitoring(self):
        """Start background alert processing"""
        if self.running:
            return
        
        self.running = True
        self.processor_thread = threading.Thread(target=self._alert_processor, daemon=True)
        self.processor_thread.start()
        self.logger.info("Alert system monitoring started")
    
    def stop_monitoring(self):
        """Stop background alert processing"""
        self.running = False
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5)
        self.save_alert_state()
        self.logger.info("Alert system monitoring stopped")
    
    def _alert_processor(self):
        """Background thread for processing alerts"""
        while self.running:
            try:
                # Process queued alerts
                while self.alert_queue:
                    alert = self.alert_queue.popleft()
                    self._process_alert(alert)
                
                # Check alert rules against current data
                self._evaluate_alert_rules()
                
                # Clean up resolved alerts
                self._cleanup_resolved_alerts()
                
                # Save state periodically
                self.save_alert_state()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in alert processor: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _process_alert(self, alert: Alert):
        """Process individual alert"""
        # Check for aggregation
        aggregated = self.aggregator.add_alert(alert)
        if aggregated:
            # Use aggregated alert instead
            alert = aggregated
        
        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        self._send_notifications(alert)
        
        self.logger.info(f"Processed alert: {alert.title} [{alert.severity}]")
    
    def _evaluate_alert_rules(self):
        """Evaluate all alert rules against current data"""
        current_time = time.time()
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Get rule state
                state = self.rule_state.get(rule_id, {
                    'triggered': False,
                    'trigger_time': None,
                    'last_alert': 0,
                    'current_value': None
                })
                
                # Evaluate rule condition
                metrics = self._get_current_metrics()
                should_trigger = self._evaluate_rule_condition(rule, metrics)
                
                if should_trigger:
                    if not state['triggered']:
                        # Start timing the condition
                        state['triggered'] = True
                        state['trigger_time'] = current_time
                        state['current_value'] = metrics.get('value', 0)
                        
                    elif (current_time - state['trigger_time']) >= rule.duration:
                        # Duration threshold met, check cooldown
                        if (current_time - state['last_alert']) >= rule.cooldown:
                            # Fire alert
                            alert = self._create_rule_alert(rule, metrics)
                            self.add_alert(alert)
                            state['last_alert'] = current_time
                else:
                    # Reset trigger state
                    state['triggered'] = False
                    state['trigger_time'] = None
                
                self.rule_state[rule_id] = state
                
            except Exception as e:
                self.logger.error(f"Error evaluating rule {rule_id}: {e}")
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics for rule evaluation"""
        metrics = {}
        
        try:
            # Get recent trend analysis data
            analyses = self.trend_analyzer.analyze_trends(days_back=1)
            
            for analysis in analyses:
                metrics[f"{analysis.metric_name}_trend"] = analysis.slope
                metrics[f"{analysis.metric_name}_change"] = analysis.recent_change_percent
                
                if analysis.baseline_comparison:
                    metrics[f"{analysis.metric_name}_current"] = analysis.baseline_comparison.get('current_average', 0)
                    metrics[f"{analysis.metric_name}_baseline_diff"] = analysis.baseline_comparison.get('difference_percent', 0)
            
            # Get regression data
            regressions = self.trend_analyzer.detect_regressions()
            metrics['regression_count'] = len(regressions)
            
            if regressions:
                max_regression = max(regressions, key=lambda r: r['change_percent'])
                metrics['max_regression_percent'] = max_regression['change_percent']
            
            # Add some synthetic metrics for demonstration
            metrics.update({
                'duration': 45.0,  # Would come from actual test data
                'memory_mb': 150.0,
                'failure_rate': 0.05,
                'success_rate': 0.95
            })
            
        except Exception as e:
            self.logger.error(f"Error getting current metrics: {e}")
        
        return metrics
    
    def _evaluate_rule_condition(self, rule: AlertRule, metrics: Dict[str, float]) -> bool:
        """Evaluate if rule condition is met"""
        try:
            # Create evaluation context
            context = {
                'threshold': rule.threshold,
                'metrics': metrics,
                **metrics  # Add metrics as direct variables
            }
            
            # Evaluate condition (simplified - in production use safer evaluation)
            result = eval(rule.condition, {"__builtins__": {}}, context)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{rule.condition}': {e}")
            return False
    
    def _create_rule_alert(self, rule: AlertRule, metrics: Dict[str, float]) -> Alert:
        """Create alert from rule"""
        return Alert(
            id=f"rule_{rule.id}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            severity=rule.severity,
            category=rule.category,
            title=rule.name,
            message=f"{rule.description}. Current value: {metrics.get('value', 'N/A')}",
            source=f"rule:{rule.id}",
            metadata={
                'rule_id': rule.id,
                'threshold': rule.threshold,
                'current_metrics': metrics
            },
            tags=rule.tags or []
        )
    
    def _cleanup_resolved_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        cutoff_iso = cutoff_time.isoformat()
        
        # Remove old resolved alerts from active list
        to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_iso:
                to_remove.append(alert_id)
        
        for alert_id in to_remove:
            del self.active_alerts[alert_id]
    
    def add_alert(self, alert: Alert):
        """Add alert to processing queue"""
        self.alert_queue.append(alert)
        
        if not self.running:
            # Process immediately if not running background processor
            self._process_alert(alert)
    
    def create_performance_alert(self, metric_name: str, current_value: float,
                               threshold: float, severity: str = 'warning') -> Alert:
        """Create performance-related alert"""
        return Alert(
            id=f"perf_{metric_name}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            severity=severity,
            category='performance',
            title=f"Performance Alert: {metric_name}",
            message=f"{metric_name} is {current_value}, exceeding threshold of {threshold}",
            source='performance_monitor',
            metadata={
                'metric_name': metric_name,
                'current_value': current_value,
                'threshold': threshold
            },
            tags=['performance', metric_name]
        )
    
    def create_regression_alert(self, test_name: str, metric_name: str,
                              baseline_value: float, current_value: float,
                              change_percent: float) -> Alert:
        """Create regression alert"""
        severity = 'critical' if change_percent > 30 else 'warning'
        
        return Alert(
            id=f"regression_{test_name}_{metric_name}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            severity=severity,
            category='regression',
            title=f"Performance Regression: {test_name}",
            message=f"{metric_name} regressed by {change_percent:.1f}% "
                   f"(baseline: {baseline_value}, current: {current_value})",
            source='trend_analyzer',
            metadata={
                'test_name': test_name,
                'metric_name': metric_name,
                'baseline_value': baseline_value,
                'current_value': current_value,
                'change_percent': change_percent
            },
            tags=['regression', test_name, metric_name]
        )
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        for channel_id, channel in self.notification_channels.items():
            if not channel.enabled:
                continue
            
            # Check severity filter
            if channel.severity_filter and alert.severity not in channel.severity_filter:
                continue
            
            # Check category filter
            if channel.category_filter and alert.category not in channel.category_filter:
                continue
            
            try:
                self._send_notification(channel, alert)
            except Exception as e:
                self.logger.error(f"Failed to send notification via {channel_id}: {e}")
    
    def _send_notification(self, channel: NotificationChannel, alert: Alert):
        """Send notification through specific channel"""
        if channel.type == 'console':
            self._send_console_notification(alert)
        
        elif channel.type == 'file':
            self._send_file_notification(channel, alert)
        
        elif channel.type == 'email':
            self._send_email_notification(channel, alert)
        
        elif channel.type == 'webhook':
            self._send_webhook_notification(channel, alert)
        
        elif channel.type == 'slack':
            self._send_slack_notification(channel, alert)
        
        else:
            self.logger.warning(f"Unknown notification channel type: {channel.type}")
    
    def _send_console_notification(self, alert: Alert):
        """Send alert to console"""
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨',
            'emergency': '🔥'
        }
        
        emoji = severity_emoji.get(alert.severity, '❓')
        timestamp = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
        
        print(f"{timestamp} {emoji} [{alert.severity.upper()}] {alert.title}")
        print(f"    {alert.message}")
        if alert.tags:
            print(f"    Tags: {', '.join(alert.tags)}")
    
    def _send_file_notification(self, channel: NotificationChannel, alert: Alert):
        """Send alert to log file"""
        file_path = Path(channel.config.get('file_path', 'alerts.log'))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = {
            'timestamp': alert.timestamp,
            'severity': alert.severity,
            'category': alert.category,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'tags': alert.tags
        }
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _send_email_notification(self, channel: NotificationChannel, alert: Alert):
        """Send alert via email"""
        config = channel.config
        
        msg = MimeMultipart()
        msg['From'] = config['from_email']
        msg['To'] = config['to_email']
        msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"
        
        body = f"""
Alert Details:
- Severity: {alert.severity}
- Category: {alert.category}
- Source: {alert.source}
- Time: {alert.timestamp}
- Message: {alert.message}

Tags: {', '.join(alert.tags or [])}

Alert ID: {alert.id}
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(config['smtp_server'], config.get('smtp_port', 587))
        if config.get('use_tls', True):
            server.starttls()
        if 'username' in config and 'password' in config:
            server.login(config['username'], config['password'])
        
        server.send_message(msg)
        server.quit()
    
    def _send_webhook_notification(self, channel: NotificationChannel, alert: Alert):
        """Send alert via webhook"""
        config = channel.config
        
        payload = {
            'alert': asdict(alert),
            'timestamp': alert.timestamp,
            'severity': alert.severity,
            'title': alert.title,
            'message': alert.message
        }
        
        headers = {'Content-Type': 'application/json'}
        if 'headers' in config:
            headers.update(config['headers'])
        
        response = requests.post(
            config['url'],
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
    
    def _send_slack_notification(self, channel: NotificationChannel, alert: Alert):
        """Send alert to Slack"""
        config = channel.config
        
        color_map = {
            'info': '#36a64f',
            'warning': '#ff9500',
            'critical': '#ff4444',
            'emergency': '#990000'
        }
        
        payload = {
            'channel': config.get('channel', '#alerts'),
            'username': config.get('username', 'AlertBot'),
            'attachments': [{
                'color': color_map.get(alert.severity, '#cccccc'),
                'title': alert.title,
                'text': alert.message,
                'fields': [
                    {'title': 'Severity', 'value': alert.severity, 'short': True},
                    {'title': 'Category', 'value': alert.category, 'short': True},
                    {'title': 'Source', 'value': alert.source, 'short': True},
                    {'title': 'Tags', 'value': ', '.join(alert.tags or []), 'short': True}
                ],
                'timestamp': int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())
            }]
        }
        
        response = requests.post(
            config['webhook_url'],
            json=payload,
            timeout=30
        )
        response.raise_for_status()
    
    def acknowledge_alert(self, alert_id: str, user: str = 'system') -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].metadata['acknowledged_by'] = user
            self.active_alerts[alert_id].metadata['acknowledged_at'] = datetime.utcnow().isoformat()
            self.save_alert_state()
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = 'system', 
                     resolution_note: str = '') -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow().isoformat()
            alert.metadata['resolved_by'] = user
            alert.metadata['resolution_note'] = resolution_note
            self.save_alert_state()
            return True
        return False
    
    def get_active_alerts(self, severity: Optional[str] = None,
                         category: Optional[str] = None) -> List[Alert]:
        """Get list of active alerts with optional filtering"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        if category:
            alerts = [alert for alert in alerts if alert.category == category]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def export_alert_report(self, output_file: str, days_back: int = 7) -> Dict:
        """Export alert report"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        cutoff_iso = cutoff_date.isoformat()
        
        # Filter alerts within time range
        recent_alerts = [alert for alert in self.alert_history 
                        if alert.timestamp >= cutoff_iso]
        
        # Calculate statistics
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for alert in recent_alerts:
            severity_counts[alert.severity] += 1
            category_counts[alert.category] += 1
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': days_back,
            'summary': {
                'total_alerts': len(recent_alerts),
                'active_alerts': len(self.get_active_alerts()),
                'resolved_alerts': len([a for a in recent_alerts if a.resolved]),
                'acknowledged_alerts': len([a for a in recent_alerts if a.acknowledged])
            },
            'severity_breakdown': dict(severity_counts),
            'category_breakdown': dict(category_counts),
            'recent_alerts': [asdict(alert) for alert in recent_alerts[-50:]],  # Last 50
            'alert_rules': {
                'total_rules': len(self.alert_rules),
                'enabled_rules': len([r for r in self.alert_rules.values() if r.enabled]),
                'rules': [asdict(rule) for rule in self.alert_rules.values()]
            },
            'notification_channels': {
                'total_channels': len(self.notification_channels),
                'enabled_channels': len([c for c in self.notification_channels.values() if c.enabled]),
                'channels': [asdict(channel) for channel in self.notification_channels.values()]
            }
        }
        
        # Save report
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Exported alert report to {output_file}")
        return report['summary']


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Proactive Alert System')
    parser.add_argument('--config', default='alert_config.json', help='Configuration file')
    parser.add_argument('--action', choices=['monitor', 'test', 'report', 'list'], 
                       required=True, help='Action to perform')
    
    # Monitor options
    parser.add_argument('--duration', type=int, help='Monitoring duration in seconds')
    
    # Test options
    parser.add_argument('--test-alert', choices=['performance', 'regression', 'failure'],
                       help='Test alert type to generate')
    
    # Report options  
    parser.add_argument('--output', help='Output file for reports')
    parser.add_argument('--days', type=int, default=7, help='Days of history to include')
    
    # List options
    parser.add_argument('--severity', help='Filter by severity')
    parser.add_argument('--category', help='Filter by category')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        alert_system = AlertSystem(args.config)
        
        if args.action == 'monitor':
            print("Starting alert monitoring...")
            alert_system.start_monitoring()
            
            try:
                if args.duration:
                    time.sleep(args.duration)
                else:
                    while True:
                        time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping alert monitoring...")
            finally:
                alert_system.stop_monitoring()
        
        elif args.action == 'test':
            if args.test_alert == 'performance':
                alert = alert_system.create_performance_alert('duration', 150.0, 120.0, 'warning')
            elif args.test_alert == 'regression':
                alert = alert_system.create_regression_alert('test_folding', 'duration', 45.0, 67.5, 50.0)
            else:
                alert = Alert(
                    id=f"test_{int(time.time())}",
                    timestamp=datetime.utcnow().isoformat(),
                    severity='critical',
                    category='failure',
                    title='Test Failure Alert',
                    message='This is a test alert generated for demonstration',
                    source='test_script',
                    metadata={'test': True},
                    tags=['test', 'demo']
                )
            
            print(f"Generating test alert: {alert.title}")
            alert_system.add_alert(alert)
            time.sleep(2)  # Allow processing
        
        elif args.action == 'report':
            output_file = args.output or f"alert_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summary = alert_system.export_alert_report(output_file, args.days)
            
            print(f"Alert report generated:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        
        elif args.action == 'list':
            alerts = alert_system.get_active_alerts(args.severity, args.category)
            
            print(f"Active alerts ({len(alerts)}):")
            for alert in alerts:
                status = " [ACK]" if alert.acknowledged else ""
                print(f"  {alert.timestamp} [{alert.severity}] {alert.title}{status}")
                print(f"    {alert.message}")
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)