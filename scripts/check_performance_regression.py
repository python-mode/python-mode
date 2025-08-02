#!/usr/bin/env python3
"""
Performance Regression Checker for Python-mode
Compares current test performance against baseline metrics to detect regressions.
"""
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import statistics


@dataclass
class PerformanceMetric:
    name: str
    baseline_value: float
    current_value: float
    threshold_percent: float
    
    @property
    def change_percent(self) -> float:
        if self.baseline_value == 0:
            return 0.0
        return ((self.current_value - self.baseline_value) / self.baseline_value) * 100
    
    @property
    def is_regression(self) -> bool:
        return self.change_percent > self.threshold_percent
    
    @property
    def status(self) -> str:
        if self.is_regression:
            return "REGRESSION"
        elif self.change_percent < -5:  # 5% improvement
            return "IMPROVEMENT"
        else:
            return "STABLE"


class PerformanceChecker:
    def __init__(self, threshold_percent: float = 10.0):
        self.threshold_percent = threshold_percent
        self.metrics: List[PerformanceMetric] = []
        self.baseline_data = {}
        self.current_data = {}
    
    def load_baseline(self, baseline_file: Path):
        """Load baseline performance metrics."""
        try:
            with open(baseline_file, 'r') as f:
                self.baseline_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Baseline file not found: {baseline_file}")
            print("This may be the first run - current results will become the baseline.")
            self.baseline_data = {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in baseline file: {e}")
            sys.exit(1)
    
    def load_current(self, current_file: Path):
        """Load current test results with performance data."""
        try:
            with open(current_file, 'r') as f:
                self.current_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: Current results file not found: {current_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in current results file: {e}")
            sys.exit(1)
    
    def analyze_performance(self):
        """Analyze performance differences between baseline and current results."""
        
        # Extract performance metrics from both datasets
        baseline_metrics = self._extract_metrics(self.baseline_data)
        current_metrics = self._extract_metrics(self.current_data)
        
        # Compare metrics
        all_metric_names = set(baseline_metrics.keys()) | set(current_metrics.keys())
        
        for metric_name in all_metric_names:
            baseline_value = baseline_metrics.get(metric_name, 0.0)
            current_value = current_metrics.get(metric_name, 0.0)
            
            # Skip if both values are zero
            if baseline_value == 0 and current_value == 0:
                continue
            
            metric = PerformanceMetric(
                name=metric_name,
                baseline_value=baseline_value,
                current_value=current_value,
                threshold_percent=self.threshold_percent
            )
            
            self.metrics.append(metric)
    
    def _extract_metrics(self, data: Dict) -> Dict[str, float]:
        """Extract performance metrics from test results."""
        metrics = {}
        
        for test_name, test_result in data.items():
            # Basic timing metrics
            duration = test_result.get('duration', 0.0)
            if duration > 0:
                metrics[f"{test_name}_duration"] = duration
            
            # Resource usage metrics from container stats
            if 'metrics' in test_result and test_result['metrics']:
                test_metrics = test_result['metrics']
                
                if 'cpu_percent' in test_metrics:
                    metrics[f"{test_name}_cpu_percent"] = test_metrics['cpu_percent']
                
                if 'memory_mb' in test_metrics:
                    metrics[f"{test_name}_memory_mb"] = test_metrics['memory_mb']
                
                if 'memory_percent' in test_metrics:
                    metrics[f"{test_name}_memory_percent"] = test_metrics['memory_percent']
        
        # Calculate aggregate metrics
        durations = [v for k, v in metrics.items() if k.endswith('_duration')]
        if durations:
            metrics['total_duration'] = sum(durations)
            metrics['avg_test_duration'] = statistics.mean(durations)
            metrics['max_test_duration'] = max(durations)
        
        cpu_percentages = [v for k, v in metrics.items() if k.endswith('_cpu_percent')]
        if cpu_percentages:
            metrics['avg_cpu_percent'] = statistics.mean(cpu_percentages)
            metrics['max_cpu_percent'] = max(cpu_percentages)
        
        memory_usage = [v for k, v in metrics.items() if k.endswith('_memory_mb')]
        if memory_usage:
            metrics['avg_memory_mb'] = statistics.mean(memory_usage)
            metrics['max_memory_mb'] = max(memory_usage)
        
        return metrics
    
    def generate_report(self) -> Tuple[bool, str]:
        """Generate performance regression report."""
        
        if not self.metrics:
            return True, "No performance metrics to compare."
        
        # Sort metrics by change percentage (worst first)
        self.metrics.sort(key=lambda m: m.change_percent, reverse=True)
        
        # Count regressions and improvements
        regressions = [m for m in self.metrics if m.is_regression]
        improvements = [m for m in self.metrics if m.change_percent < -5]
        stable = [m for m in self.metrics if not m.is_regression and m.change_percent >= -5]
        
        # Generate report
        report_lines = []
        report_lines.append("# Performance Regression Report")
        report_lines.append("")
        
        # Summary
        has_regressions = len(regressions) > 0
        status_emoji = "❌" if has_regressions else "✅"
        report_lines.append(f"## Summary {status_emoji}")
        report_lines.append("")
        report_lines.append(f"- **Threshold**: {self.threshold_percent}% regression")
        report_lines.append(f"- **Regressions**: {len(regressions)}")
        report_lines.append(f"- **Improvements**: {len(improvements)}")
        report_lines.append(f"- **Stable**: {len(stable)}")
        report_lines.append("")
        
        # Detailed results
        if regressions:
            report_lines.append("## ❌ Performance Regressions")
            report_lines.append("")
            report_lines.append("| Metric | Baseline | Current | Change | Status |")
            report_lines.append("|--------|----------|---------|--------|--------|")
            
            for metric in regressions:
                report_lines.append(
                    f"| {metric.name} | {metric.baseline_value:.2f} | "
                    f"{metric.current_value:.2f} | {metric.change_percent:+.1f}% | "
                    f"{metric.status} |"
                )
            report_lines.append("")
        
        if improvements:
            report_lines.append("## ✅ Performance Improvements")
            report_lines.append("")
            report_lines.append("| Metric | Baseline | Current | Change | Status |")
            report_lines.append("|--------|----------|---------|--------|--------|")
            
            for metric in improvements[:10]:  # Show top 10 improvements
                report_lines.append(
                    f"| {metric.name} | {metric.baseline_value:.2f} | "
                    f"{metric.current_value:.2f} | {metric.change_percent:+.1f}% | "
                    f"{metric.status} |"
                )
            report_lines.append("")
        
        # Key metrics summary
        key_metrics = [m for m in self.metrics if any(key in m.name for key in 
                      ['total_duration', 'avg_test_duration', 'max_test_duration', 
                       'avg_cpu_percent', 'max_memory_mb'])]
        
        if key_metrics:
            report_lines.append("## 📊 Key Metrics")
            report_lines.append("")
            report_lines.append("| Metric | Baseline | Current | Change | Status |")
            report_lines.append("|--------|----------|---------|--------|--------|")
            
            for metric in key_metrics:
                status_emoji = "❌" if metric.is_regression else "✅" if metric.change_percent < -5 else "➖"
                report_lines.append(
                    f"| {status_emoji} {metric.name} | {metric.baseline_value:.2f} | "
                    f"{metric.current_value:.2f} | {metric.change_percent:+.1f}% | "
                    f"{metric.status} |"
                )
            report_lines.append("")
        
        report_text = "\n".join(report_lines)
        return not has_regressions, report_text
    
    def save_current_as_baseline(self, baseline_file: Path):
        """Save current results as new baseline for future comparisons."""
        try:
            with open(baseline_file, 'w') as f:
                json.dump(self.current_data, f, indent=2)
            print(f"Current results saved as baseline: {baseline_file}")
        except Exception as e:
            print(f"Error saving baseline: {e}")


def main():
    parser = argparse.ArgumentParser(description='Check for performance regressions')
    parser.add_argument('--baseline', type=Path, required=True,
                       help='Baseline performance metrics file')
    parser.add_argument('--current', type=Path, required=True,
                       help='Current test results file')
    parser.add_argument('--threshold', type=float, default=10.0,
                       help='Regression threshold percentage (default: 10%%)')
    parser.add_argument('--output', type=Path, default='performance-report.md',
                       help='Output report file')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update baseline with current results if no regressions')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Checking performance with {args.threshold}% threshold")
        print(f"Baseline: {args.baseline}")
        print(f"Current: {args.current}")
    
    checker = PerformanceChecker(threshold_percent=args.threshold)
    
    # Load data
    checker.load_baseline(args.baseline)
    checker.load_current(args.current)
    
    # Analyze performance
    checker.analyze_performance()
    
    # Generate report
    passed, report = checker.generate_report()
    
    # Save report
    with open(args.output, 'w') as f:
        f.write(report)
    
    if args.verbose:
        print(f"Report saved to: {args.output}")
    
    # Print summary
    print(report)
    
    # Update baseline if requested and no regressions
    if args.update_baseline and passed:
        checker.save_current_as_baseline(args.baseline)
    
    # Exit with appropriate code
    if not passed:
        print("\n❌ Performance regressions detected!")
        sys.exit(1)
    else:
        print("\n✅ No performance regressions detected.")
        sys.exit(0)


if __name__ == '__main__':
    main()