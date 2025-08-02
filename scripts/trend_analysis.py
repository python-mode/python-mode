#!/usr/bin/env python3
"""
Historical Trend Analysis System for Python-mode Performance Monitoring

This module provides comprehensive trend analysis capabilities for long-term
performance monitoring, including regression detection, baseline management,
and statistical analysis of performance patterns over time.
"""

import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
import logging

@dataclass
class TrendPoint:
    """Single point in a performance trend"""
    timestamp: str
    test_name: str
    configuration: str  # e.g., "python3.11-vim9.0"
    metric_name: str
    value: float
    metadata: Dict[str, Any]

@dataclass
class TrendAnalysis:
    """Results of trend analysis"""
    metric_name: str
    trend_direction: str  # 'improving', 'degrading', 'stable'
    slope: float
    correlation: float
    significance: float  # p-value or confidence
    recent_change_percent: float
    baseline_comparison: Dict[str, float]
    anomalies: List[Dict]
    summary: str

@dataclass
class PerformanceBaseline:
    """Performance baseline for a specific test/configuration"""
    test_name: str
    configuration: str
    metric_name: str
    baseline_value: float
    confidence_interval: Tuple[float, float]
    sample_count: int
    last_updated: str
    stability_score: float

class TrendAnalyzer:
    """Historical trend analysis engine"""
    
    def __init__(self, db_path: str = "performance_trends.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for trend storage"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    configuration TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    configuration TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    baseline_value REAL NOT NULL,
                    confidence_lower REAL NOT NULL,
                    confidence_upper REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    stability_score REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(test_name, configuration, metric_name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trend_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    configuration TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    trigger_value REAL,
                    baseline_value REAL,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT
                )
            ''')
            
            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_perf_data_lookup ON performance_data(test_name, configuration, metric_name, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_baselines_lookup ON baselines(test_name, configuration, metric_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_lookup ON trend_alerts(test_name, configuration, metric_name, resolved)')
            
            conn.commit()
    
    def store_performance_data(self, data_points: List[TrendPoint]):
        """Store performance data points in the database"""
        with sqlite3.connect(self.db_path) as conn:
            for point in data_points:
                conn.execute('''
                    INSERT INTO performance_data 
                    (timestamp, test_name, configuration, metric_name, value, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    point.timestamp,
                    point.test_name,
                    point.configuration,
                    point.metric_name,
                    point.value,
                    json.dumps(point.metadata) if point.metadata else None
                ))
            conn.commit()
        
        self.logger.info(f"Stored {len(data_points)} performance data points")
    
    def import_test_results(self, results_file: str) -> int:
        """Import test results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            data_points = []
            timestamp = datetime.utcnow().isoformat()
            
            for test_path, result in results.items():
                if not isinstance(result, dict):
                    continue
                
                test_name = Path(test_path).stem
                config = self._extract_configuration(result)
                
                # Extract basic metrics
                if 'duration' in result:
                    data_points.append(TrendPoint(
                        timestamp=timestamp,
                        test_name=test_name,
                        configuration=config,
                        metric_name='duration',
                        value=float(result['duration']),
                        metadata={'status': result.get('status', 'unknown')}
                    ))
                
                # Extract performance metrics if available
                if 'metrics' in result and isinstance(result['metrics'], dict):
                    metrics = result['metrics']
                    
                    if 'cpu_percent' in metrics:
                        data_points.append(TrendPoint(
                            timestamp=timestamp,
                            test_name=test_name,
                            configuration=config,
                            metric_name='cpu_percent',
                            value=float(metrics['cpu_percent']),
                            metadata={'status': result.get('status', 'unknown')}
                        ))
                    
                    if 'memory_mb' in metrics:
                        data_points.append(TrendPoint(
                            timestamp=timestamp,
                            test_name=test_name,
                            configuration=config,
                            metric_name='memory_mb',
                            value=float(metrics['memory_mb']),
                            metadata={'status': result.get('status', 'unknown')}
                        ))
            
            if data_points:
                self.store_performance_data(data_points)
            
            return len(data_points)
            
        except Exception as e:
            self.logger.error(f"Failed to import test results from {results_file}: {e}")
            return 0
    
    def _extract_configuration(self, result: Dict) -> str:
        """Extract configuration string from test result"""
        # Try to extract from metadata or use default
        if 'metadata' in result and isinstance(result['metadata'], dict):
            python_ver = result['metadata'].get('python_version', '3.11')
            vim_ver = result['metadata'].get('vim_version', '9.0')
            return f"python{python_ver}-vim{vim_ver}"
        return "default"
    
    def analyze_trends(self, 
                      test_name: Optional[str] = None,
                      configuration: Optional[str] = None,
                      metric_name: Optional[str] = None,
                      days_back: int = 30) -> List[TrendAnalysis]:
        """Analyze performance trends over specified time period"""
        
        # Build query conditions
        conditions = []
        params = []
        
        if test_name:
            conditions.append("test_name = ?")
            params.append(test_name)
        
        if configuration:
            conditions.append("configuration = ?")
            params.append(configuration)
        
        if metric_name:
            conditions.append("metric_name = ?")
            params.append(metric_name)
        
        # Add time constraint
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        conditions.append("timestamp >= ?")
        params.append(cutoff_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT test_name, configuration, metric_name, timestamp, value, metadata
            FROM performance_data 
            WHERE {where_clause}
            ORDER BY test_name, configuration, metric_name, timestamp
        '''
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Group data by test/configuration/metric
        grouped_data = {}
        for row in rows:
            key = (row[0], row[1], row[2])  # test_name, configuration, metric_name
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append({
                'timestamp': row[3],
                'value': row[4],
                'metadata': json.loads(row[5]) if row[5] else {}
            })
        
        # Analyze each group
        analyses = []
        for (test_name, config, metric), data in grouped_data.items():
            if len(data) < 3:  # Need at least 3 points for trend analysis
                continue
            
            analysis = self._analyze_single_trend(test_name, config, metric, data)
            if analysis:
                analyses.append(analysis)
        
        return analyses
    
    def _analyze_single_trend(self, test_name: str, configuration: str, 
                            metric_name: str, data: List[Dict]) -> Optional[TrendAnalysis]:
        """Analyze trend for a single metric"""
        try:
            # Convert timestamps to numeric values for regression
            timestamps = [datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) for d in data]
            values = [d['value'] for d in data]
            
            # Convert timestamps to days since first measurement
            first_time = timestamps[0]
            x_values = [(t - first_time).total_seconds() / 86400 for t in timestamps]  # days
            y_values = values
            
            # Calculate linear regression
            if len(x_values) >= 2:
                slope, correlation = self._calculate_regression(x_values, y_values)
            else:
                slope, correlation = 0, 0
            
            # Determine trend direction
            if abs(slope) < 0.01:  # Very small slope
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'degrading' if metric_name in ['duration', 'memory_mb', 'cpu_percent'] else 'improving'
            else:
                trend_direction = 'improving' if metric_name in ['duration', 'memory_mb', 'cpu_percent'] else 'degrading'
            
            # Calculate recent change (last 7 days vs previous)
            recent_change = self._calculate_recent_change(data, days=7)
            
            # Get baseline comparison
            baseline = self.get_baseline(test_name, configuration, metric_name)
            baseline_comparison = {}
            if baseline:
                current_avg = mean(values[-min(10, len(values)):])  # Last 10 values or all
                baseline_comparison = {
                    'baseline_value': baseline.baseline_value,
                    'current_average': current_avg,
                    'difference_percent': ((current_avg - baseline.baseline_value) / baseline.baseline_value) * 100,
                    'within_confidence': baseline.confidence_interval[0] <= current_avg <= baseline.confidence_interval[1]
                }
            
            # Detect anomalies
            anomalies = self._detect_anomalies(data)
            
            # Calculate significance (correlation significance)
            significance = abs(correlation) if correlation else 0
            
            # Generate summary
            summary = self._generate_trend_summary(
                trend_direction, slope, recent_change, baseline_comparison, len(anomalies)
            )
            
            return TrendAnalysis(
                metric_name=metric_name,
                trend_direction=trend_direction,
                slope=slope,
                correlation=correlation,
                significance=significance,
                recent_change_percent=recent_change,
                baseline_comparison=baseline_comparison,
                anomalies=anomalies,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze trend for {test_name}/{configuration}/{metric_name}: {e}")
            return None
    
    def _calculate_regression(self, x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and correlation coefficient"""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return 0.0, 0.0
            
            x_array = np.array(x_values)
            y_array = np.array(y_values)
            
            # Calculate slope using least squares
            x_mean = np.mean(x_array)
            y_mean = np.mean(y_array)
            
            numerator = np.sum((x_array - x_mean) * (y_array - y_mean))
            denominator = np.sum((x_array - x_mean) ** 2)
            
            if denominator == 0:
                return 0.0, 0.0
            
            slope = numerator / denominator
            
            # Calculate correlation coefficient
            correlation = np.corrcoef(x_array, y_array)[0, 1] if len(x_values) > 1 else 0.0
            if np.isnan(correlation):
                correlation = 0.0
            
            return float(slope), float(correlation)
            
        except Exception:
            return 0.0, 0.0
    
    def _calculate_recent_change(self, data: List[Dict], days: int = 7) -> float:
        """Calculate percentage change in recent period vs previous period"""
        try:
            if len(data) < 4:  # Need at least 4 points
                return 0.0
            
            # Sort by timestamp
            sorted_data = sorted(data, key=lambda x: x['timestamp'])
            
            # Split into recent and previous periods
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            
            recent_values = [d['value'] for d in sorted_data 
                           if d['timestamp'] >= cutoff_iso]
            previous_values = [d['value'] for d in sorted_data 
                             if d['timestamp'] < cutoff_iso]
            
            if not recent_values or not previous_values:
                return 0.0
            
            recent_avg = mean(recent_values)
            previous_avg = mean(previous_values)
            
            if previous_avg == 0:
                return 0.0
            
            return ((recent_avg - previous_avg) / previous_avg) * 100
            
        except Exception:
            return 0.0
    
    def _detect_anomalies(self, data: List[Dict], threshold: float = 2.0) -> List[Dict]:
        """Detect anomalous values using statistical methods"""
        try:
            if len(data) < 5:  # Need minimum data for anomaly detection
                return []
            
            values = [d['value'] for d in data]
            mean_val = mean(values)
            std_val = stdev(values) if len(values) > 1 else 0
            
            if std_val == 0:
                return []
            
            anomalies = []
            for i, d in enumerate(data):
                z_score = abs(d['value'] - mean_val) / std_val
                if z_score > threshold:
                    anomalies.append({
                        'timestamp': d['timestamp'],
                        'value': d['value'],
                        'z_score': z_score,
                        'deviation_percent': ((d['value'] - mean_val) / mean_val) * 100
                    })
            
            return anomalies
            
        except Exception:
            return []
    
    def _generate_trend_summary(self, direction: str, slope: float, 
                              recent_change: float, baseline_comp: Dict, 
                              anomaly_count: int) -> str:
        """Generate human-readable trend summary"""
        summary_parts = []
        
        # Trend direction
        if direction == 'improving':
            summary_parts.append("Performance is improving")
        elif direction == 'degrading':
            summary_parts.append("Performance is degrading")
        else:
            summary_parts.append("Performance is stable")
        
        # Recent change
        if abs(recent_change) > 5:
            change_dir = "increased" if recent_change > 0 else "decreased"
            summary_parts.append(f"recent {change_dir} by {abs(recent_change):.1f}%")
        
        # Baseline comparison
        if baseline_comp and 'difference_percent' in baseline_comp:
            diff_pct = baseline_comp['difference_percent']
            if abs(diff_pct) > 10:
                vs_baseline = "above" if diff_pct > 0 else "below"
                summary_parts.append(f"{abs(diff_pct):.1f}% {vs_baseline} baseline")
        
        # Anomalies
        if anomaly_count > 0:
            summary_parts.append(f"{anomaly_count} anomalies detected")
        
        return "; ".join(summary_parts)
    
    def update_baselines(self, test_name: Optional[str] = None, 
                        configuration: Optional[str] = None,
                        min_samples: int = 10, days_back: int = 30):
        """Update performance baselines based on recent stable data"""
        
        # Get recent stable data
        conditions = ["timestamp >= ?"]
        params = [(datetime.utcnow() - timedelta(days=days_back)).isoformat()]
        
        if test_name:
            conditions.append("test_name = ?")
            params.append(test_name)
        
        if configuration:
            conditions.append("configuration = ?")
            params.append(configuration)
        
        where_clause = " AND ".join(conditions)
        
        query = f'''
            SELECT test_name, configuration, metric_name, value
            FROM performance_data 
            WHERE {where_clause}
            ORDER BY test_name, configuration, metric_name
        '''
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Group by test/configuration/metric
        grouped_data = {}
        for row in rows:
            key = (row[0], row[1], row[2])  # test_name, configuration, metric_name
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(row[3])  # value
        
        # Calculate baselines for each group
        baselines_updated = 0
        for (test_name, config, metric), values in grouped_data.items():
            if len(values) < min_samples:
                continue
            
            # Calculate baseline statistics
            baseline_value = median(values)  # Use median for robustness
            mean_val = mean(values)
            std_val = stdev(values) if len(values) > 1 else 0
            
            # Calculate confidence interval (95%)
            confidence_margin = 1.96 * std_val / np.sqrt(len(values)) if std_val > 0 else 0
            confidence_lower = mean_val - confidence_margin
            confidence_upper = mean_val + confidence_margin
            
            # Calculate stability score (inverse of coefficient of variation)
            stability_score = 1.0 / (std_val / mean_val) if mean_val > 0 and std_val > 0 else 1.0
            stability_score = min(stability_score, 1.0)  # Cap at 1.0
            
            baseline = PerformanceBaseline(
                test_name=test_name,
                configuration=config,
                metric_name=metric,
                baseline_value=baseline_value,
                confidence_interval=(confidence_lower, confidence_upper),
                sample_count=len(values),
                last_updated=datetime.utcnow().isoformat(),
                stability_score=stability_score
            )
            
            # Store baseline in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO baselines 
                    (test_name, configuration, metric_name, baseline_value, 
                     confidence_lower, confidence_upper, sample_count, 
                     stability_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    baseline.test_name,
                    baseline.configuration,
                    baseline.metric_name,
                    baseline.baseline_value,
                    baseline.confidence_interval[0],
                    baseline.confidence_interval[1],
                    baseline.sample_count,
                    baseline.stability_score,
                    baseline.last_updated
                ))
                conn.commit()
            
            baselines_updated += 1
        
        self.logger.info(f"Updated {baselines_updated} performance baselines")
        return baselines_updated
    
    def get_baseline(self, test_name: str, configuration: str, 
                    metric_name: str) -> Optional[PerformanceBaseline]:
        """Get performance baseline for specific test/configuration/metric"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT test_name, configuration, metric_name, baseline_value,
                       confidence_lower, confidence_upper, sample_count,
                       stability_score, last_updated
                FROM baselines 
                WHERE test_name = ? AND configuration = ? AND metric_name = ?
            ''', (test_name, configuration, metric_name))
            
            row = cursor.fetchone()
            if row:
                return PerformanceBaseline(
                    test_name=row[0],
                    configuration=row[1],
                    metric_name=row[2],
                    baseline_value=row[3],
                    confidence_interval=(row[4], row[5]),
                    sample_count=row[6],
                    stability_score=row[7],
                    last_updated=row[8]
                )
        
        return None
    
    def detect_regressions(self, threshold_percent: float = 15.0) -> List[Dict]:
        """Detect performance regressions by comparing recent data to baselines"""
        regressions = []
        
        # Get all baselines
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM baselines')
            baselines = cursor.fetchall()
        
        for baseline_row in baselines:
            test_name, config, metric = baseline_row[1], baseline_row[2], baseline_row[3]
            baseline_value = baseline_row[4]
            
            # Get recent data (last 7 days)
            cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT value FROM performance_data 
                    WHERE test_name = ? AND configuration = ? AND metric_name = ?
                    AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (test_name, config, metric, cutoff_date))
                
                recent_values = [row[0] for row in cursor.fetchall()]
            
            if not recent_values:
                continue
            
            # Calculate recent average
            recent_avg = mean(recent_values)
            
            # Check for regression (assuming higher values are worse for performance metrics)
            if metric in ['duration', 'memory_mb', 'cpu_percent']:
                # For these metrics, increase is bad
                change_percent = ((recent_avg - baseline_value) / baseline_value) * 100
                is_regression = change_percent > threshold_percent
            else:
                # For other metrics, decrease might be bad
                change_percent = ((baseline_value - recent_avg) / baseline_value) * 100
                is_regression = change_percent > threshold_percent
            
            if is_regression:
                regressions.append({
                    'test_name': test_name,
                    'configuration': config,
                    'metric_name': metric,
                    'baseline_value': baseline_value,
                    'recent_average': recent_avg,
                    'change_percent': abs(change_percent),
                    'severity': 'critical' if abs(change_percent) > 30 else 'warning',
                    'detected_at': datetime.utcnow().isoformat()
                })
        
        # Store regression alerts
        if regressions:
            with sqlite3.connect(self.db_path) as conn:
                for regression in regressions:
                    conn.execute('''
                        INSERT INTO trend_alerts 
                        (test_name, configuration, metric_name, alert_type, 
                         severity, message, trigger_value, baseline_value, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        regression['test_name'],
                        regression['configuration'],
                        regression['metric_name'],
                        'regression',
                        regression['severity'],
                        f"Performance regression detected: {regression['change_percent']:.1f}% increase in {regression['metric_name']}",
                        regression['recent_average'],
                        regression['baseline_value'],
                        regression['detected_at']
                    ))
                conn.commit()
        
        self.logger.info(f"Detected {len(regressions)} performance regressions")
        return regressions
    
    def export_trends(self, output_file: str, format: str = 'json',
                     days_back: int = 30) -> Dict:
        """Export trend analysis results"""
        
        # Get all trend analyses
        analyses = self.analyze_trends(days_back=days_back)
        
        # Get recent regressions
        regressions = self.detect_regressions()
        
        # Get summary statistics
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM performance_data 
                WHERE timestamp >= ?
            ''', [(datetime.utcnow() - timedelta(days=days_back)).isoformat()])
            data_points = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) FROM baselines')
            baseline_count = cursor.fetchone()[0]
            
            cursor = conn.execute('''
                SELECT COUNT(*) FROM trend_alerts 
                WHERE resolved = FALSE
            ''')
            active_alerts = cursor.fetchone()[0]
        
        export_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': days_back,
            'summary': {
                'data_points_analyzed': data_points,
                'trends_analyzed': len(analyses),
                'baselines_available': baseline_count,
                'active_regressions': len(regressions),
                'active_alerts': active_alerts
            },
            'trend_analyses': [asdict(analysis) for analysis in analyses],
            'regressions': regressions
        }
        
        # Export based on format
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'test_name', 'configuration', 'metric_name', 'trend_direction',
                    'slope', 'correlation', 'recent_change_percent', 'summary'
                ])
                
                for analysis in analyses:
                    writer.writerow([
                        'N/A',  # test_name not in TrendAnalysis
                        'N/A',  # configuration not in TrendAnalysis
                        analysis.metric_name,
                        analysis.trend_direction,
                        analysis.slope,
                        analysis.correlation,
                        analysis.recent_change_percent,
                        analysis.summary
                    ])
        
        self.logger.info(f"Exported trend analysis to {output_file}")
        return export_data['summary']


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Historical Trend Analysis for Performance Data')
    parser.add_argument('--db', default='performance_trends.db', help='Database file path')
    parser.add_argument('--action', choices=['import', 'analyze', 'baselines', 'regressions', 'export'], 
                       required=True, help='Action to perform')
    
    # Import options
    parser.add_argument('--import-file', help='Test results file to import')
    
    # Analysis options
    parser.add_argument('--test', help='Specific test name to analyze')
    parser.add_argument('--config', help='Specific configuration to analyze')
    parser.add_argument('--metric', help='Specific metric to analyze')
    parser.add_argument('--days', type=int, default=30, help='Days of data to analyze')
    
    # Baseline options
    parser.add_argument('--min-samples', type=int, default=10, help='Minimum samples for baseline')
    
    # Regression options
    parser.add_argument('--threshold', type=float, default=15.0, help='Regression threshold percentage')
    
    # Export options
    parser.add_argument('--output', help='Output file for export')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = TrendAnalyzer(args.db)
    
    try:
        if args.action == 'import':
            if not args.import_file:
                print("Error: --import-file required for import action")
                exit(1)
            
            count = analyzer.import_test_results(args.import_file)
            print(f"Imported {count} data points from {args.import_file}")
        
        elif args.action == 'analyze':
            analyses = analyzer.analyze_trends(
                test_name=args.test,
                configuration=args.config,
                metric_name=args.metric,
                days_back=args.days
            )
            
            print(f"Analyzed {len(analyses)} trends:")
            for analysis in analyses:
                print(f"  {analysis.metric_name}: {analysis.summary}")
        
        elif args.action == 'baselines':
            count = analyzer.update_baselines(
                test_name=args.test,
                configuration=args.config,
                min_samples=args.min_samples,
                days_back=args.days
            )
            print(f"Updated {count} baselines")
        
        elif args.action == 'regressions':
            regressions = analyzer.detect_regressions(args.threshold)
            print(f"Detected {len(regressions)} regressions:")
            for reg in regressions:
                print(f"  {reg['test_name']}/{reg['configuration']}/{reg['metric_name']}: "
                      f"{reg['change_percent']:.1f}% increase")
        
        elif args.action == 'export':
            if not args.output:
                print("Error: --output required for export action")
                exit(1)
            
            summary = analyzer.export_trends(args.output, args.format, args.days)
            print(f"Exported trend analysis:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)