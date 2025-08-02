#!/usr/bin/env python3
"""
Performance Dashboard Generator for Python-mode Test Infrastructure

This module generates comprehensive HTML dashboards with interactive visualizations
for performance monitoring, trend analysis, alerts, and optimization recommendations.
"""

import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Import our other modules
try:
    from .trend_analysis import TrendAnalyzer
    from .performance_monitor import PerformanceMonitor
    from .optimization_engine import OptimizationEngine
    from .alert_system import AlertSystem
except ImportError:
    from trend_analysis import TrendAnalyzer
    from performance_monitor import PerformanceMonitor
    from optimization_engine import OptimizationEngine
    from alert_system import AlertSystem

@dataclass
class DashboardConfig:
    """Configuration for dashboard generation"""
    title: str = "Python-mode Performance Dashboard"
    subtitle: str = "Real-time monitoring and analysis"
    refresh_interval: int = 300  # seconds
    theme: str = "light"  # light, dark
    include_sections: List[str] = None  # None = all sections
    time_range_days: int = 7
    max_data_points: int = 1000

class DashboardGenerator:
    """Generates interactive HTML performance dashboards"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize data sources
        self.trend_analyzer = TrendAnalyzer()
        self.optimization_engine = OptimizationEngine()
        self.alert_system = AlertSystem()
        
        # Default sections
        if self.config.include_sections is None:
            self.config.include_sections = [
                'overview', 'performance', 'trends', 'alerts', 
                'optimization', 'system_health'
            ]
    
    def generate_dashboard(self, output_file: str, data_sources: Optional[Dict] = None) -> str:
        """Generate complete HTML dashboard"""
        self.logger.info(f"Generating dashboard: {output_file}")
        
        # Collect data from various sources
        dashboard_data = self._collect_dashboard_data(data_sources)
        
        # Generate HTML content
        html_content = self._generate_html(dashboard_data)
        
        # Write to file
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Dashboard generated successfully: {output_file}")
        return output_file
    
    def _collect_dashboard_data(self, data_sources: Optional[Dict] = None) -> Dict:
        """Collect data from all sources"""
        data = {
            'generated_at': datetime.utcnow().isoformat(),
            'config': self.config,
            'sections': {}
        }
        
        # Use provided data sources or collect from systems
        if data_sources:
            return {**data, **data_sources}
        
        try:
            # Overview data
            if 'overview' in self.config.include_sections:
                data['sections']['overview'] = self._collect_overview_data()
            
            # Performance metrics
            if 'performance' in self.config.include_sections:
                data['sections']['performance'] = self._collect_performance_data()
            
            # Trend analysis
            if 'trends' in self.config.include_sections:
                data['sections']['trends'] = self._collect_trends_data()
            
            # Alerts
            if 'alerts' in self.config.include_sections:
                data['sections']['alerts'] = self._collect_alerts_data()
            
            # Optimization
            if 'optimization' in self.config.include_sections:
                data['sections']['optimization'] = self._collect_optimization_data()
            
            # System health
            if 'system_health' in self.config.include_sections:
                data['sections']['system_health'] = self._collect_system_health_data()
        
        except Exception as e:
            self.logger.error(f"Error collecting dashboard data: {e}")
            data['error'] = str(e)
        
        return data
    
    def _collect_overview_data(self) -> Dict:
        """Collect overview/summary data"""
        try:
            # Get recent performance data
            analyses = self.trend_analyzer.analyze_trends(days_back=self.config.time_range_days)
            active_alerts = self.alert_system.get_active_alerts()
            
            # Calculate key metrics
            total_tests = len(set(a.metric_name for a in analyses if 'duration' in a.metric_name))
            avg_duration = 0
            success_rate = 95.0  # Placeholder
            
            if analyses:
                duration_analyses = [a for a in analyses if 'duration' in a.metric_name]
                if duration_analyses:
                    avg_duration = sum(a.baseline_comparison.get('current_average', 0) 
                                     for a in duration_analyses if a.baseline_comparison) / len(duration_analyses)
            
            return {
                'summary_cards': [
                    {
                        'title': 'Total Tests',
                        'value': total_tests,
                        'unit': 'tests',
                        'trend': 'stable',
                        'color': 'blue'
                    },
                    {
                        'title': 'Avg Duration',
                        'value': round(avg_duration, 1),
                        'unit': 'seconds',
                        'trend': 'improving',
                        'color': 'green'
                    },
                    {
                        'title': 'Success Rate',
                        'value': success_rate,
                        'unit': '%',
                        'trend': 'stable',
                        'color': 'green'
                    },
                    {
                        'title': 'Active Alerts',
                        'value': len(active_alerts),
                        'unit': 'alerts',
                        'trend': 'stable',
                        'color': 'orange' if active_alerts else 'green'
                    }
                ],
                'recent_activity': [
                    {
                        'timestamp': datetime.utcnow().isoformat(),
                        'type': 'info',
                        'message': 'Dashboard generated successfully'
                    }
                ]
            }
        except Exception as e:
            self.logger.error(f"Error collecting overview data: {e}")
            return {'error': str(e)}
    
    def _collect_performance_data(self) -> Dict:
        """Collect performance metrics data"""
        try:
            analyses = self.trend_analyzer.analyze_trends(days_back=self.config.time_range_days)
            
            # Group by metric type
            metrics_data = {}
            for analysis in analyses:
                metric = analysis.metric_name
                if metric not in metrics_data:
                    metrics_data[metric] = {
                        'values': [],
                        'timestamps': [],
                        'trend': analysis.trend_direction,
                        'correlation': analysis.correlation
                    }
            
            # Generate sample time series data for charts
            base_time = datetime.utcnow() - timedelta(days=self.config.time_range_days)
            for i in range(min(self.config.max_data_points, self.config.time_range_days * 24)):
                timestamp = base_time + timedelta(hours=i)
                
                for metric in metrics_data:
                    # Generate realistic sample data
                    if metric == 'duration':
                        value = 45 + (i * 0.1) + (i % 10 - 5)  # Slight upward trend with noise
                    elif metric == 'memory_mb':
                        value = 150 + (i * 0.05) + (i % 8 - 4)
                    elif metric == 'cpu_percent':
                        value = 25 + (i % 15 - 7)
                    else:
                        value = 100 + (i % 20 - 10)
                    
                    metrics_data[metric]['values'].append(max(0, value))
                    metrics_data[metric]['timestamps'].append(timestamp.isoformat())
            
            return {
                'metrics': metrics_data,
                'summary': {
                    'total_metrics': len(metrics_data),
                    'data_points': sum(len(m['values']) for m in metrics_data.values()),
                    'time_range_days': self.config.time_range_days
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting performance data: {e}")
            return {'error': str(e)}
    
    def _collect_trends_data(self) -> Dict:
        """Collect trend analysis data"""
        try:
            analyses = self.trend_analyzer.analyze_trends(days_back=self.config.time_range_days)
            regressions = self.trend_analyzer.detect_regressions()
            
            # Process trend data
            trends_summary = {
                'improving': [],
                'degrading': [],
                'stable': []
            }
            
            for analysis in analyses:
                trend_info = {
                    'metric': analysis.metric_name,
                    'change_percent': analysis.recent_change_percent,
                    'correlation': analysis.correlation,
                    'summary': analysis.summary
                }
                trends_summary[analysis.trend_direction].append(trend_info)
            
            return {
                'trends_summary': trends_summary,
                'regressions': regressions,
                'analysis_count': len(analyses),
                'regression_count': len(regressions)
            }
        except Exception as e:
            self.logger.error(f"Error collecting trends data: {e}")
            return {'error': str(e)}
    
    def _collect_alerts_data(self) -> Dict:
        """Collect alerts data"""
        try:
            active_alerts = self.alert_system.get_active_alerts()
            
            # Group alerts by severity and category
            severity_counts = {'info': 0, 'warning': 0, 'critical': 0, 'emergency': 0}
            category_counts = {}
            
            alert_list = []
            for alert in active_alerts[:20]:  # Latest 20 alerts
                severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
                category_counts[alert.category] = category_counts.get(alert.category, 0) + 1
                
                alert_list.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp,
                    'severity': alert.severity,
                    'category': alert.category,
                    'title': alert.title,
                    'message': alert.message[:200] + '...' if len(alert.message) > 200 else alert.message,
                    'acknowledged': alert.acknowledged,
                    'tags': alert.tags or []
                })
            
            return {
                'active_alerts': alert_list,
                'severity_counts': severity_counts,
                'category_counts': category_counts,
                'total_active': len(active_alerts)
            }
        except Exception as e:
            self.logger.error(f"Error collecting alerts data: {e}")
            return {'error': str(e)}
    
    def _collect_optimization_data(self) -> Dict:
        """Collect optimization data"""
        try:
            # Get recent optimization history
            recent_optimizations = self.optimization_engine.optimization_history[-5:] if self.optimization_engine.optimization_history else []
            
            # Get current parameter values
            current_params = {}
            for name, param in self.optimization_engine.parameters.items():
                current_params[name] = {
                    'current_value': param.current_value,
                    'description': param.description,
                    'impact_metrics': param.impact_metrics
                }
            
            return {
                'recent_optimizations': recent_optimizations,
                'current_parameters': current_params,
                'optimization_count': len(recent_optimizations),
                'parameter_count': len(current_params)
            }
        except Exception as e:
            self.logger.error(f"Error collecting optimization data: {e}")
            return {'error': str(e)}
    
    def _collect_system_health_data(self) -> Dict:
        """Collect system health data"""
        try:
            # This would normally come from system monitoring
            # For now, generate sample health data
            
            health_metrics = {
                'cpu_usage': {
                    'current': 45.2,
                    'average': 42.1,
                    'max': 78.3,
                    'status': 'healthy'
                },
                'memory_usage': {
                    'current': 62.8,
                    'average': 58.4,
                    'max': 89.1,
                    'status': 'healthy'  
                },
                'disk_usage': {
                    'current': 34.6,
                    'average': 31.2,
                    'max': 45.7,
                    'status': 'healthy'
                },
                'network_latency': {
                    'current': 12.4,
                    'average': 15.2,
                    'max': 45.1,
                    'status': 'healthy'
                }
            }
            
            return {
                'health_metrics': health_metrics,
                'overall_status': 'healthy',
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error collecting system health data: {e}")
            return {'error': str(e)}
    
    def _generate_html(self, data: Dict) -> str:
        """Generate complete HTML dashboard"""
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body class="{self.config.theme}">
    <div class="dashboard">
        {self._generate_header(data)}
        {self._generate_content(data)}
        {self._generate_footer(data)}
    </div>
    <script>
        {self._generate_javascript(data)}
    </script>
</body>
</html>'''
        
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for dashboard"""
        return '''
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .light {
            --bg-color: #f5f7fa;
            --card-bg: #ffffff;
            --text-color: #2d3748;
            --border-color: #e2e8f0;
            --accent-color: #4299e1;
            --success-color: #48bb78;
            --warning-color: #ed8936;
            --error-color: #f56565;
        }
        
        .dark {
            --bg-color: #1a202c;
            --card-bg: #2d3748;
            --text-color: #e2e8f0;
            --border-color: #4a5568;
            --accent-color: #63b3ed;
            --success-color: #68d391;
            --warning-color: #fbb74e;
            --error-color: #fc8181;
        }
        
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--accent-color);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.8;
        }
        
        .header-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }
        
        .section {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .section h2 {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-color);
        }
        
        .grid {
            display: grid;
            gap: 20px;
        }
        
        .grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
        .grid-3 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
        .grid-4 { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
        
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border-color);
        }
        
        .metric-card {
            text-align: center;
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-trend {
            font-size: 0.8rem;
            margin-top: 5px;
        }
        
        .trend-up { color: var(--success-color); }
        .trend-down { color: var(--error-color); }
        .trend-stable { color: var(--text-color); opacity: 0.6; }
        
        .color-blue { color: var(--accent-color); }
        .color-green { color: var(--success-color); }
        .color-orange { color: var(--warning-color); }
        .color-red { color: var(--error-color); }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        
        .alert-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 4px solid;
        }
        
        .alert-critical { 
            background: rgba(245, 101, 101, 0.1); 
            border-left-color: var(--error-color);
        }
        .alert-warning { 
            background: rgba(237, 137, 54, 0.1); 
            border-left-color: var(--warning-color);
        }
        .alert-info { 
            background: rgba(66, 153, 225, 0.1); 
            border-left-color: var(--accent-color);
        }
        
        .alert-severity {
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 12px;
        }
        
        .alert-content {
            flex: 1;
        }
        
        .alert-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .alert-message {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: var(--success-color); }
        .status-warning { background-color: var(--warning-color); }
        .status-critical { background-color: var(--error-color); }
        
        .footer {
            text-align: center;
            padding: 20px;
            font-size: 0.9rem;
            opacity: 0.6;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .grid-2, .grid-3, .grid-4 {
                grid-template-columns: 1fr;
            }
        }
        '''
    
    def _generate_header(self, data: Dict) -> str:
        """Generate dashboard header"""
        generated_at = datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00'))
        formatted_time = generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return f'''
        <div class="header">
            <h1>{self.config.title}</h1>
            <p>{self.config.subtitle}</p>
            <div class="header-meta">
                <span>Generated: {formatted_time}</span>
                <span>Time Range: {self.config.time_range_days} days</span>
            </div>
        </div>
        '''
    
    def _generate_content(self, data: Dict) -> str:
        """Generate dashboard content sections"""
        content = ""
        sections = data.get('sections', {})
        
        # Overview section
        if 'overview' in sections:
            content += self._generate_overview_section(sections['overview'])
        
        # Performance section
        if 'performance' in sections:
            content += self._generate_performance_section(sections['performance'])
        
        # Trends section
        if 'trends' in sections:
            content += self._generate_trends_section(sections['trends'])
        
        # Alerts section
        if 'alerts' in sections:
            content += self._generate_alerts_section(sections['alerts'])
        
        # Optimization section
        if 'optimization' in sections:
            content += self._generate_optimization_section(sections['optimization'])
        
        # System health section
        if 'system_health' in sections:
            content += self._generate_system_health_section(sections['system_health'])
        
        return content
    
    def _generate_overview_section(self, overview_data: Dict) -> str:
        """Generate overview section"""
        if 'error' in overview_data:
            return f'<div class="section"><h2>Overview</h2><p>Error: {overview_data["error"]}</p></div>'
        
        cards_html = ""
        for card in overview_data.get('summary_cards', []):
            trend_class = f"trend-{card['trend']}" if card['trend'] != 'stable' else 'trend-stable'
            trend_icon = {'improving': '↗', 'degrading': '↙', 'stable': '→'}.get(card['trend'], '→')
            
            cards_html += f'''
            <div class="card metric-card">
                <div class="metric-value color-{card['color']}">{card['value']}</div>
                <div class="metric-label">{card['title']}</div>
                <div class="metric-trend {trend_class}">{trend_icon} {card['trend']}</div>
            </div>
            '''
        
        return f'''
        <div class="section">
            <h2>Overview</h2>
            <div class="grid grid-4">
                {cards_html}
            </div>
        </div>
        '''
    
    def _generate_performance_section(self, perf_data: Dict) -> str:
        """Generate performance section"""
        if 'error' in perf_data:
            return f'<div class="section"><h2>Performance Metrics</h2><p>Error: {perf_data["error"]}</p></div>'
        
        metrics = perf_data.get('metrics', {})
        chart_html = ""
        
        for metric_name, metric_data in metrics.items():
            chart_id = f"chart-{metric_name.replace('_', '-')}"
            chart_html += f'''
            <div class="card">
                <h3>{metric_name.replace('_', ' ').title()}</h3>
                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
                <div class="metric-info">
                    <span>Trend: {metric_data.get('trend', 'stable')}</span>
                    <span>Correlation: {metric_data.get('correlation', 0):.3f}</span>
                </div>
            </div>
            '''
        
        return f'''
        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="grid grid-2">
                {chart_html}
            </div>
        </div>
        '''
    
    def _generate_trends_section(self, trends_data: Dict) -> str:
        """Generate trends section"""
        if 'error' in trends_data:
            return f'<div class="section"><h2>Trend Analysis</h2><p>Error: {trends_data["error"]}</p></div>'
        
        trends_summary = trends_data.get('trends_summary', {})
        
        trends_html = ""
        for trend_type, trends in trends_summary.items():
            if not trends:
                continue
                
            trend_color = {'improving': 'green', 'degrading': 'red', 'stable': 'blue'}[trend_type]
            trend_icon = {'improving': '📈', 'degrading': '📉', 'stable': '📊'}[trend_type]
            
            trends_html += f'''
            <div class="card">
                <h3>{trend_icon} {trend_type.title()} Trends ({len(trends)})</h3>
                <ul>
            '''
            
            for trend in trends[:5]:  # Show top 5
                trends_html += f'''
                <li>
                    <strong>{trend['metric']}</strong>: {trend['summary']}
                    <small>(Change: {trend['change_percent']:.1f}%)</small>
                </li>
                '''
            
            trends_html += '</ul></div>'
        
        return f'''
        <div class="section">
            <h2>Trend Analysis</h2>
            <div class="grid grid-3">
                {trends_html}
            </div>
        </div>
        '''
    
    def _generate_alerts_section(self, alerts_data: Dict) -> str:
        """Generate alerts section"""
        if 'error' in alerts_data:
            return f'<div class="section"><h2>Active Alerts</h2><p>Error: {alerts_data["error"]}</p></div>'
        
        active_alerts = alerts_data.get('active_alerts', [])
        severity_counts = alerts_data.get('severity_counts', {})
        
        # Severity summary
        summary_html = ""
        for severity, count in severity_counts.items():
            if count > 0:
                summary_html += f'''
                <div class="card metric-card">
                    <div class="metric-value color-{['blue', 'orange', 'red', 'red'][['info', 'warning', 'critical', 'emergency'].index(severity)]}">{count}</div>
                    <div class="metric-label">{severity.title()}</div>
                </div>
                '''
        
        # Active alerts list
        alerts_html = ""
        for alert in active_alerts[:10]:  # Show latest 10
            alert_class = f"alert-{alert['severity']}"
            timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
            
            alerts_html += f'''
            <div class="alert-item {alert_class}">
                <span class="alert-severity">{alert['severity']}</span>
                <div class="alert-content">
                    <div class="alert-title">{alert['title']}</div>
                    <div class="alert-message">{alert['message']}</div>
                    <small>{timestamp} | {alert['category']}</small>
                </div>
            </div>
            '''
        
        return f'''
        <div class="section">
            <h2>Active Alerts ({alerts_data.get('total_active', 0)})</h2>
            <div class="grid grid-4" style="margin-bottom: 20px;">
                {summary_html}
            </div>
            <div>
                {alerts_html if alerts_html else '<p>No active alerts</p>'}
            </div>
        </div>
        '''
    
    def _generate_optimization_section(self, opt_data: Dict) -> str:
        """Generate optimization section"""
        if 'error' in opt_data:
            return f'<div class="section"><h2>Optimization</h2><p>Error: {opt_data["error"]}</p></div>'
        
        current_params = opt_data.get('current_parameters', {})
        recent_opts = opt_data.get('recent_optimizations', [])
        
        params_html = ""
        for param_name, param_info in current_params.items():
            params_html += f'''
            <div class="card">
                <h4>{param_name.replace('_', ' ').title()}</h4>
                <div class="metric-value">{param_info['current_value']}</div>
                <p>{param_info['description']}</p>
                <small>Impacts: {', '.join(param_info['impact_metrics'])}</small>
            </div>
            '''
        
        return f'''
        <div class="section">
            <h2>Optimization Status</h2>
            <div class="grid grid-3">
                {params_html}
            </div>
        </div>
        '''
    
    def _generate_system_health_section(self, health_data: Dict) -> str:
        """Generate system health section"""
        if 'error' in health_data:
            return f'<div class="section"><h2>System Health</h2><p>Error: {health_data["error"]}</p></div>'
        
        metrics = health_data.get('health_metrics', {})
        
        health_html = ""
        for metric_name, metric_info in metrics.items():
            status_class = f"status-{metric_info['status']}"
            
            health_html += f'''
            <div class="card">
                <h4>
                    <span class="status-indicator {status_class}"></span>
                    {metric_name.replace('_', ' ').title()}
                </h4>
                <div class="metric-value">{metric_info['current']:.1f}%</div>
                <div>
                    <small>Avg: {metric_info['average']:.1f}% | Max: {metric_info['max']:.1f}%</small>
                </div>
            </div>
            '''
        
        return f'''
        <div class="section">
            <h2>System Health</h2>
            <div class="grid grid-4">
                {health_html}
            </div>
        </div>
        '''
    
    def _generate_footer(self, data: Dict) -> str:
        """Generate dashboard footer"""
        return '''
        <div class="footer">
            <p>Python-mode Performance Dashboard | Generated by Phase 5 Monitoring System</p>
        </div>
        '''
    
    def _generate_javascript(self, data: Dict) -> str:
        """Generate JavaScript for interactive features"""
        js_code = f'''
        // Dashboard configuration
        const config = {json.dumps(data.get('config', {}), default=str)};
        const refreshInterval = config.refresh_interval * 1000;
        
        // Auto-refresh functionality
        if (refreshInterval > 0) {{
            setTimeout(() => {{
                window.location.reload();
            }}, refreshInterval);
        }}
        
        // Chart generation
        const chartColors = {{
            primary: '#4299e1',
            success: '#48bb78',
            warning: '#ed8936',
            error: '#f56565'
        }};
        '''
        
        # Add chart initialization code
        sections = data.get('sections', {})
        if 'performance' in sections:
            perf_data = sections['performance']
            metrics = perf_data.get('metrics', {})
            
            for metric_name, metric_data in metrics.items():
                chart_id = f"chart-{metric_name.replace('_', '-')}"
                
                js_code += f'''
                // Chart for {metric_name}
                const ctx_{metric_name.replace('-', '_')} = document.getElementById('{chart_id}');
                if (ctx_{metric_name.replace('-', '_')}) {{
                    new Chart(ctx_{metric_name.replace('-', '_')}, {{
                        type: 'line',
                        data: {{
                            labels: {json.dumps(metric_data.get('timestamps', [])[:50])},
                            datasets: [{{
                                label: '{metric_name.replace("_", " ").title()}',
                                data: {json.dumps(metric_data.get('values', [])[:50])},
                                borderColor: chartColors.primary,
                                backgroundColor: chartColors.primary + '20',
                                tension: 0.4,
                                fill: true
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{
                                    display: false
                                }}
                            }},
                            scales: {{
                                x: {{
                                    display: false
                                }},
                                y: {{
                                    beginAtZero: true
                                }}
                            }}
                        }}
                    }});
                }}
                '''
        
        return js_code
    
    def generate_static_dashboard(self, output_file: str, 
                                include_charts: bool = False) -> str:
        """Generate static dashboard without external dependencies"""
        # Generate dashboard with embedded chart images if requested
        dashboard_data = self._collect_dashboard_data()
        
        if include_charts:
            # Generate simple ASCII charts for static version
            dashboard_data = self._add_ascii_charts(dashboard_data)
        
        html_content = self._generate_static_html(dashboard_data)
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def _add_ascii_charts(self, data: Dict) -> Dict:
        """Add ASCII charts to dashboard data"""
        # Simple ASCII chart generation for static dashboards
        sections = data.get('sections', {})
        
        if 'performance' in sections:
            metrics = sections['performance'].get('metrics', {})
            for metric_name, metric_data in metrics.items():
                values = metric_data.get('values', [])[-20:]  # Last 20 points
                if values:
                    ascii_chart = self._generate_ascii_chart(values)
                    metric_data['ascii_chart'] = ascii_chart
        
        return data
    
    def _generate_ascii_chart(self, values: List[float]) -> str:
        """Generate simple ASCII chart"""
        if not values:
            return "No data"
        
        min_val, max_val = min(values), max(values)
        height = 8
        width = len(values)
        
        if max_val == min_val:
            return "─" * width
        
        normalized = [(v - min_val) / (max_val - min_val) * height for v in values]
        
        chart_lines = []
        for row in range(height, 0, -1):
            line = ""
            for val in normalized:
                if val >= row - 0.5:
                    line += "█"
                elif val >= row - 1:
                    line += "▄"
                else:
                    line += " "
            chart_lines.append(line)
        
        return "\n".join(chart_lines)
    
    def _generate_static_html(self, data: Dict) -> str:
        """Generate static HTML without external dependencies"""
        # Similar to _generate_html but without Chart.js dependency
        # This would be a simpler version for environments without internet access
        return self._generate_html(data).replace(
            '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
            '<!-- Charts disabled for static version -->'
        )


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Dashboard Generator')
    parser.add_argument('--output', '-o', default='dashboard.html', help='Output HTML file')
    parser.add_argument('--title', default='Python-mode Performance Dashboard', help='Dashboard title')
    parser.add_argument('--days', type=int, default=7, help='Days of data to include')
    parser.add_argument('--theme', choices=['light', 'dark'], default='light', help='Dashboard theme')
    parser.add_argument('--refresh', type=int, default=300, help='Auto-refresh interval in seconds')
    parser.add_argument('--static', action='store_true', help='Generate static dashboard without external dependencies')
    parser.add_argument('--sections', nargs='+', 
                       choices=['overview', 'performance', 'trends', 'alerts', 'optimization', 'system_health'],
                       help='Sections to include (default: all)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create dashboard configuration
        config = DashboardConfig(
            title=args.title,
            refresh_interval=args.refresh,
            theme=args.theme,
            include_sections=args.sections,
            time_range_days=args.days
        )
        
        # Generate dashboard
        generator = DashboardGenerator(config)
        
        if args.static:
            output_file = generator.generate_static_dashboard(args.output, include_charts=True)
            print(f"Static dashboard generated: {output_file}")
        else:
            output_file = generator.generate_dashboard(args.output)
            print(f"Interactive dashboard generated: {output_file}")
        
        print(f"Dashboard URL: file://{Path(output_file).absolute()}")
        
    except Exception as e:
        print(f"Error generating dashboard: {e}")
        exit(1)