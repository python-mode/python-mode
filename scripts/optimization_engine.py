#!/usr/bin/env python3
"""
Automated Optimization Engine for Python-mode Test Infrastructure

This module provides intelligent parameter optimization based on historical
performance data, automatically tuning test execution parameters for optimal
performance, reliability, and resource utilization.
"""

import json
import math
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
import logging

# Import our trend analysis module
try:
    from .trend_analysis import TrendAnalyzer, TrendPoint
except ImportError:
    from trend_analysis import TrendAnalyzer, TrendPoint

@dataclass
class OptimizationParameter:
    """Definition of an optimizable parameter"""
    name: str
    current_value: Any
    min_value: Any
    max_value: Any
    step_size: Any
    value_type: str  # 'int', 'float', 'bool', 'enum'
    description: str
    impact_metrics: List[str]  # Which metrics this parameter affects
    constraint_fn: Optional[str] = None  # Python expression for constraints

@dataclass
class OptimizationResult:
    """Result of parameter optimization"""
    parameter_name: str
    old_value: Any
    new_value: Any
    expected_improvement: float
    confidence: float
    reasoning: str
    validation_required: bool = True

@dataclass
class OptimizationRecommendation:
    """Complete optimization recommendation"""
    timestamp: str
    target_configuration: str
    results: List[OptimizationResult]
    overall_improvement: float
    risk_level: str  # 'low', 'medium', 'high'
    validation_plan: Dict[str, Any]
    rollback_plan: Dict[str, Any]

class OptimizationEngine:
    """Automated parameter optimization engine"""
    
    def __init__(self, trend_analyzer: Optional[TrendAnalyzer] = None, 
                 config_file: str = "optimization_config.json"):
        self.trend_analyzer = trend_analyzer or TrendAnalyzer()
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Load optimization configuration
        self.parameters = self._load_optimization_config()
        self.optimization_history = []
        self.load_optimization_history()
    
    def _load_optimization_config(self) -> Dict[str, OptimizationParameter]:
        """Load optimization parameter definitions"""
        default_config = {
            "test_timeout": OptimizationParameter(
                name="test_timeout",
                current_value=60,
                min_value=15,
                max_value=300,
                step_size=5,
                value_type="int",
                description="Individual test timeout in seconds",
                impact_metrics=["duration", "success_rate", "timeout_rate"],
                constraint_fn="value >= 15 and value <= 300"
            ),
            "parallel_jobs": OptimizationParameter(
                name="parallel_jobs",
                current_value=4,
                min_value=1,
                max_value=16,
                step_size=1,
                value_type="int",
                description="Number of parallel test jobs",
                impact_metrics=["total_duration", "cpu_percent", "memory_mb"],
                constraint_fn="value >= 1 and value <= 16"
            ),
            "memory_limit": OptimizationParameter(
                name="memory_limit",
                current_value=256,
                min_value=128,
                max_value=1024,
                step_size=64,
                value_type="int",
                description="Container memory limit in MB",
                impact_metrics=["memory_mb", "oom_rate", "success_rate"],
                constraint_fn="value >= 128 and value <= 1024"
            ),
            "collection_interval": OptimizationParameter(
                name="collection_interval",
                current_value=1.0,
                min_value=0.1,
                max_value=5.0,
                step_size=0.1,
                value_type="float",
                description="Performance metrics collection interval in seconds",
                impact_metrics=["monitoring_overhead", "data_granularity"],
                constraint_fn="value >= 0.1 and value <= 5.0"
            ),
            "retry_attempts": OptimizationParameter(
                name="retry_attempts",
                current_value=2,
                min_value=0,
                max_value=5,
                step_size=1,
                value_type="int",
                description="Number of retry attempts for failed tests",
                impact_metrics=["success_rate", "total_duration", "flaky_test_rate"],
                constraint_fn="value >= 0 and value <= 5"
            ),
            "cache_enabled": OptimizationParameter(
                name="cache_enabled",
                current_value=True,
                min_value=False,
                max_value=True,
                step_size=None,
                value_type="bool",
                description="Enable Docker layer caching",
                impact_metrics=["build_duration", "cache_hit_rate"],
                constraint_fn=None
            )
        }
        
        # Load from file if exists, otherwise use defaults
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Convert loaded data back to OptimizationParameter objects
                loaded_params = {}
                for name, data in config_data.items():
                    if isinstance(data, dict) and 'name' in data:
                        loaded_params[name] = OptimizationParameter(**data)
                
                # Merge with defaults (use loaded if available, defaults otherwise)
                for name, param in default_config.items():
                    if name in loaded_params:
                        # Update current_value from loaded config
                        param.current_value = loaded_params[name].current_value
                    loaded_params[name] = param
                
                return loaded_params
                
            except Exception as e:
                self.logger.warning(f"Failed to load optimization config: {e}, using defaults")
        
        return default_config
    
    def save_optimization_config(self):
        """Save current optimization configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert OptimizationParameter objects to dicts for JSON serialization
        config_data = {}
        for name, param in self.parameters.items():
            config_data[name] = asdict(param)
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_optimization_history(self):
        """Load optimization history from file"""
        history_file = self.config_file.parent / "optimization_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self.optimization_history = history_data.get('history', [])
            except Exception as e:
                self.logger.warning(f"Failed to load optimization history: {e}")
    
    def save_optimization_history(self):
        """Save optimization history to file"""
        history_file = self.config_file.parent / "optimization_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_file, 'w') as f:
            json.dump({
                'last_updated': datetime.utcnow().isoformat(),
                'history': self.optimization_history
            }, f, indent=2)
    
    def analyze_parameter_impact(self, parameter_name: str, 
                               days_back: int = 30) -> Dict[str, float]:
        """Analyze the impact of a parameter on performance metrics"""
        if parameter_name not in self.parameters:
            return {}
        
        param = self.parameters[parameter_name]
        impact_scores = {}
        
        # Get historical data for impact metrics
        for metric in param.impact_metrics:
            try:
                # Get trend analysis for this metric
                analyses = self.trend_analyzer.analyze_trends(
                    metric_name=metric,
                    days_back=days_back
                )
                
                if analyses:
                    # Calculate average correlation and trend strength
                    correlations = [abs(a.correlation) for a in analyses if a.correlation]
                    trend_strengths = [abs(a.slope) for a in analyses if a.slope]
                    
                    if correlations:
                        impact_scores[metric] = {
                            'correlation': mean(correlations),
                            'trend_strength': mean(trend_strengths) if trend_strengths else 0,
                            'sample_count': len(analyses)
                        }
                
            except Exception as e:
                self.logger.debug(f"Failed to analyze impact for {metric}: {e}")
        
        return impact_scores
    
    def optimize_parameter(self, parameter_name: str, 
                          target_metrics: Optional[List[str]] = None,
                          optimization_method: str = "hill_climbing") -> OptimizationResult:
        """Optimize a single parameter using specified method"""
        
        if parameter_name not in self.parameters:
            raise ValueError(f"Unknown parameter: {parameter_name}")
        
        param = self.parameters[parameter_name]
        target_metrics = target_metrics or param.impact_metrics
        
        # Get current baseline performance
        baseline_performance = self._get_baseline_performance(target_metrics)
        
        if optimization_method == "hill_climbing":
            return self._hill_climbing_optimization(param, target_metrics, baseline_performance)
        elif optimization_method == "bayesian":
            return self._bayesian_optimization(param, target_metrics, baseline_performance)
        elif optimization_method == "grid_search":
            return self._grid_search_optimization(param, target_metrics, baseline_performance)
        else:
            raise ValueError(f"Unknown optimization method: {optimization_method}")
    
    def _get_baseline_performance(self, metrics: List[str]) -> Dict[str, float]:
        """Get current baseline performance for specified metrics"""
        baseline = {}
        
        for metric in metrics:
            # Get recent performance data
            analyses = self.trend_analyzer.analyze_trends(
                metric_name=metric,
                days_back=7  # Recent baseline
            )
            
            if analyses:
                # Use the most recent analysis
                recent_analysis = analyses[0]
                if recent_analysis.baseline_comparison:
                    baseline[metric] = recent_analysis.baseline_comparison.get('current_average', 0)
                else:
                    baseline[metric] = 0
            else:
                baseline[metric] = 0
        
        return baseline
    
    def _hill_climbing_optimization(self, param: OptimizationParameter, 
                                  target_metrics: List[str],
                                  baseline: Dict[str, float]) -> OptimizationResult:
        """Optimize parameter using hill climbing algorithm"""
        
        current_value = param.current_value
        best_value = current_value
        best_score = self._calculate_optimization_score(target_metrics, baseline)
        
        # Try different step sizes and directions
        step_directions = [1, -1] if param.value_type in ['int', 'float'] else [None]
        
        for direction in step_directions:
            if direction is None:  # Boolean parameter
                candidate_value = not current_value if param.value_type == 'bool' else current_value
            else:
                if param.value_type == 'int':
                    candidate_value = current_value + (direction * param.step_size)
                elif param.value_type == 'float':
                    candidate_value = current_value + (direction * param.step_size)
                else:
                    continue
            
            # Check constraints
            if not self._validate_parameter_value(param, candidate_value):
                continue
            
            # Estimate performance with this value
            estimated_performance = self._estimate_performance(param.name, candidate_value, target_metrics)
            candidate_score = self._calculate_optimization_score(target_metrics, estimated_performance)
            
            if candidate_score > best_score:
                best_score = candidate_score
                best_value = candidate_value
        
        # Calculate expected improvement
        improvement = ((best_score - self._calculate_optimization_score(target_metrics, baseline)) / 
                      max(self._calculate_optimization_score(target_metrics, baseline), 0.001)) * 100
        
        # Generate reasoning
        reasoning = self._generate_optimization_reasoning(param, current_value, best_value, improvement)
        
        return OptimizationResult(
            parameter_name=param.name,
            old_value=current_value,
            new_value=best_value,
            expected_improvement=improvement,
            confidence=min(abs(improvement) / 10.0, 1.0),  # Simple confidence heuristic
            reasoning=reasoning,
            validation_required=abs(improvement) > 5.0
        )
    
    def _bayesian_optimization(self, param: OptimizationParameter,
                             target_metrics: List[str],
                             baseline: Dict[str, float]) -> OptimizationResult:
        """Optimize parameter using simplified Bayesian optimization"""
        
        # For simplicity, this implements a gaussian process-like approach
        # In a full implementation, you'd use libraries like scikit-optimize
        
        current_value = param.current_value
        
        # Generate candidate values
        candidates = self._generate_candidate_values(param, num_candidates=10)
        
        best_value = current_value
        best_score = self._calculate_optimization_score(target_metrics, baseline)
        best_uncertainty = 0.5
        
        for candidate in candidates:
            if not self._validate_parameter_value(param, candidate):
                continue
            
            # Estimate performance and uncertainty
            estimated_performance = self._estimate_performance(param.name, candidate, target_metrics)
            score = self._calculate_optimization_score(target_metrics, estimated_performance)
            
            # Simple uncertainty estimation based on distance from current value
            if param.value_type in ['int', 'float']:
                distance = abs(candidate - current_value) / max(abs(param.max_value - param.min_value), 1)
                uncertainty = min(distance, 1.0)
            else:
                uncertainty = 0.5
            
            # Acquisition function: score + exploration bonus
            acquisition = score + (uncertainty * 0.1)  # Small exploration bonus
            
            if acquisition > best_score + best_uncertainty * 0.1:
                best_score = score
                best_value = candidate
                best_uncertainty = uncertainty
        
        # Calculate expected improvement
        baseline_score = self._calculate_optimization_score(target_metrics, baseline)
        improvement = ((best_score - baseline_score) / max(baseline_score, 0.001)) * 100
        
        reasoning = self._generate_optimization_reasoning(param, current_value, best_value, improvement)
        
        return OptimizationResult(
            parameter_name=param.name,
            old_value=current_value,
            new_value=best_value,
            expected_improvement=improvement,
            confidence=1.0 - best_uncertainty,
            reasoning=reasoning,
            validation_required=abs(improvement) > 3.0
        )
    
    def _grid_search_optimization(self, param: OptimizationParameter,
                                target_metrics: List[str],
                                baseline: Dict[str, float]) -> OptimizationResult:
        """Optimize parameter using grid search"""
        
        current_value = param.current_value
        
        # Generate grid of candidate values
        candidates = self._generate_candidate_values(param, num_candidates=20)
        
        best_value = current_value
        best_score = self._calculate_optimization_score(target_metrics, baseline)
        
        for candidate in candidates:
            if not self._validate_parameter_value(param, candidate):
                continue
            
            estimated_performance = self._estimate_performance(param.name, candidate, target_metrics)
            score = self._calculate_optimization_score(target_metrics, estimated_performance)
            
            if score > best_score:
                best_score = score
                best_value = candidate
        
        # Calculate expected improvement
        baseline_score = self._calculate_optimization_score(target_metrics, baseline)
        improvement = ((best_score - baseline_score) / max(baseline_score, 0.001)) * 100
        
        reasoning = self._generate_optimization_reasoning(param, current_value, best_value, improvement)
        
        return OptimizationResult(
            parameter_name=param.name,
            old_value=current_value,
            new_value=best_value,
            expected_improvement=improvement,
            confidence=0.8,  # Grid search provides good confidence
            reasoning=reasoning,
            validation_required=abs(improvement) > 2.0
        )
    
    def _generate_candidate_values(self, param: OptimizationParameter, 
                                 num_candidates: int = 10) -> List[Any]:
        """Generate candidate values for parameter optimization"""
        
        if param.value_type == 'bool':
            return [True, False]
        
        elif param.value_type == 'int':
            min_val, max_val = int(param.min_value), int(param.max_value)
            step = max(int(param.step_size), 1)
            
            if num_candidates >= (max_val - min_val) // step:
                # Generate all possible values
                return list(range(min_val, max_val + 1, step))
            else:
                # Generate evenly spaced candidates
                candidates = []
                for i in range(num_candidates):
                    val = min_val + (i * (max_val - min_val) // (num_candidates - 1))
                    candidates.append(val)
                return candidates
        
        elif param.value_type == 'float':
            min_val, max_val = float(param.min_value), float(param.max_value)
            candidates = []
            for i in range(num_candidates):
                val = min_val + (i * (max_val - min_val) / (num_candidates - 1))
                candidates.append(round(val, 2))
            return candidates
        
        else:
            return [param.current_value]
    
    def _validate_parameter_value(self, param: OptimizationParameter, value: Any) -> bool:
        """Validate parameter value against constraints"""
        
        # Basic type and range checks
        if param.value_type == 'int' and not isinstance(value, int):
            return False
        elif param.value_type == 'float' and not isinstance(value, (int, float)):
            return False
        elif param.value_type == 'bool' and not isinstance(value, bool):
            return False
        
        # Range checks
        if param.value_type in ['int', 'float']:
            if value < param.min_value or value > param.max_value:
                return False
        
        # Custom constraint function
        if param.constraint_fn:
            try:
                # Simple constraint evaluation (in production, use safer evaluation)
                return eval(param.constraint_fn.replace('value', str(value)))
            except:
                return False
        
        return True
    
    def _estimate_performance(self, param_name: str, value: Any, 
                            target_metrics: List[str]) -> Dict[str, float]:
        """Estimate performance metrics for given parameter value"""
        
        # This is a simplified estimation model
        # In practice, you'd use machine learning models trained on historical data
        
        estimated = {}
        
        for metric in target_metrics:
            # Get historical baseline
            baseline = self._get_baseline_performance([metric]).get(metric, 1.0)
            
            # Apply parameter-specific estimation logic
            if param_name == "test_timeout":
                if metric == "duration":
                    # Longer timeout might allow more thorough testing but could increase duration
                    factor = 1.0 + (value - 60) * 0.001  # Small linear relationship
                elif metric == "success_rate":
                    # Longer timeout generally improves success rate
                    factor = 1.0 + max(0, (value - 30) * 0.01)
                else:
                    factor = 1.0
            
            elif param_name == "parallel_jobs":
                if metric == "total_duration":
                    # More jobs reduce total duration but with diminishing returns
                    factor = 1.0 / (1.0 + math.log(max(value, 1)) * 0.5)
                elif metric == "cpu_percent":
                    # More jobs increase CPU usage
                    factor = 1.0 + (value - 1) * 0.1
                elif metric == "memory_mb":
                    # More jobs increase memory usage
                    factor = 1.0 + (value - 1) * 0.2
                else:
                    factor = 1.0
            
            elif param_name == "memory_limit":
                if metric == "memory_mb":
                    # Higher limit allows more memory usage but doesn't guarantee it
                    factor = min(1.0, value / 256.0)  # Normalize to baseline 256MB
                elif metric == "success_rate":
                    # Higher memory limit improves success rate for memory-intensive tests
                    factor = 1.0 + max(0, (value - 128) * 0.001)
                else:
                    factor = 1.0
            
            else:
                factor = 1.0  # Default: no change
            
            estimated[metric] = baseline * factor
        
        return estimated
    
    def _calculate_optimization_score(self, metrics: List[str], 
                                    performance: Dict[str, float]) -> float:
        """Calculate optimization score based on performance metrics"""
        
        if not performance:
            return 0.0
        
        # Metric weights (higher weight = more important)
        metric_weights = {
            'duration': -2.0,  # Lower is better
            'total_duration': -2.0,  # Lower is better
            'cpu_percent': -1.0,  # Lower is better
            'memory_mb': -1.0,  # Lower is better
            'success_rate': 3.0,  # Higher is better
            'timeout_rate': -1.5,  # Lower is better
            'oom_rate': -2.0,  # Lower is better
            'flaky_test_rate': -1.0,  # Lower is better
            'cache_hit_rate': 1.0,  # Higher is better
            'build_duration': -1.0,  # Lower is better
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            if metric in performance:
                weight = metric_weights.get(metric, 0.0)
                value = performance[metric]
                
                # Normalize value (simple approach)
                if weight > 0:  # Higher is better
                    normalized_value = min(value / 100.0, 1.0)  # Cap at 1.0
                else:  # Lower is better
                    normalized_value = max(1.0 - (value / 100.0), 0.0)  # Invert
                
                score += weight * normalized_value
                total_weight += abs(weight)
        
        return score / max(total_weight, 1.0)  # Normalize by total weight
    
    def _generate_optimization_reasoning(self, param: OptimizationParameter,
                                       old_value: Any, new_value: Any,
                                       improvement: float) -> str:
        """Generate human-readable reasoning for optimization result"""
        
        if old_value == new_value:
            return f"Current {param.name} value ({old_value}) is already optimal"
        
        change_desc = f"from {old_value} to {new_value}"
        
        if improvement > 5:
            impact = "significant improvement"
        elif improvement > 1:
            impact = "moderate improvement"
        elif improvement > 0:
            impact = "minor improvement"
        elif improvement > -1:
            impact = "negligible change"
        else:
            impact = "potential degradation"
        
        # Add parameter-specific reasoning
        specific_reasoning = ""
        if param.name == "test_timeout":
            if new_value > old_value:
                specific_reasoning = "allowing more time for complex tests to complete"
            else:
                specific_reasoning = "reducing wait time for stuck processes"
        
        elif param.name == "parallel_jobs":
            if new_value > old_value:
                specific_reasoning = "increasing parallelism to reduce total execution time"
            else:
                specific_reasoning = "reducing parallelism to decrease resource contention"
        
        elif param.name == "memory_limit":
            if new_value > old_value:
                specific_reasoning = "providing more memory for memory-intensive tests"
            else:
                specific_reasoning = "optimizing memory usage to reduce overhead"
        
        return f"Adjusting {param.name} {change_desc} is expected to provide {impact}" + \
               (f" by {specific_reasoning}" if specific_reasoning else "")
    
    def optimize_configuration(self, configuration: str = "default",
                             optimization_method: str = "hill_climbing") -> OptimizationRecommendation:
        """Optimize entire configuration"""
        
        timestamp = datetime.utcnow().isoformat()
        results = []
        
        # Optimize each parameter
        for param_name in self.parameters:
            try:
                result = self.optimize_parameter(param_name, optimization_method=optimization_method)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to optimize {param_name}: {e}")
        
        # Calculate overall improvement
        improvements = [r.expected_improvement for r in results if r.expected_improvement > 0]
        overall_improvement = mean(improvements) if improvements else 0
        
        # Assess risk level
        high_impact_count = sum(1 for r in results if abs(r.expected_improvement) > 10)
        validation_required_count = sum(1 for r in results if r.validation_required)
        
        if high_impact_count > 2 or validation_required_count > 3:
            risk_level = "high"
        elif high_impact_count > 0 or validation_required_count > 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate validation plan
        validation_plan = {
            "approach": "gradual_rollout",
            "phases": [
                {
                    "name": "validation_tests",
                    "parameters": [r.parameter_name for r in results if r.validation_required],
                    "duration": "2-4 hours",
                    "success_criteria": "No performance regressions > 5%"
                },
                {
                    "name": "partial_deployment",
                    "parameters": [r.parameter_name for r in results],
                    "duration": "1-2 days",
                    "success_criteria": "Overall improvement confirmed"
                }
            ]
        }
        
        # Generate rollback plan
        rollback_plan = {
            "triggers": [
                "Performance regression > 15%",
                "Test success rate drops > 5%",
                "Critical test failures"
            ],
            "procedure": "Revert to previous parameter values",
            "estimated_time": "< 30 minutes",
            "previous_values": {r.parameter_name: r.old_value for r in results}
        }
        
        recommendation = OptimizationRecommendation(
            timestamp=timestamp,
            target_configuration=configuration,
            results=results,
            overall_improvement=overall_improvement,
            risk_level=risk_level,
            validation_plan=validation_plan,
            rollback_plan=rollback_plan
        )
        
        # Store in history
        self.optimization_history.append(asdict(recommendation))
        self.save_optimization_history()
        
        self.logger.info(f"Generated optimization recommendation with {overall_improvement:.1f}% expected improvement")
        
        return recommendation
    
    def apply_optimization(self, recommendation: OptimizationRecommendation,
                          dry_run: bool = True) -> Dict[str, Any]:
        """Apply optimization recommendation"""
        
        if dry_run:
            self.logger.info("Dry run mode - no changes will be applied")
        
        applied_changes = []
        failed_changes = []
        
        for result in recommendation.results:
            try:
                if result.parameter_name in self.parameters:
                    old_value = self.parameters[result.parameter_name].current_value
                    
                    if not dry_run:
                        # Apply the change
                        self.parameters[result.parameter_name].current_value = result.new_value
                        self.save_optimization_config()
                    
                    applied_changes.append({
                        'parameter': result.parameter_name,
                        'old_value': old_value,
                        'new_value': result.new_value,
                        'expected_improvement': result.expected_improvement
                    })
                    
                    self.logger.info(f"{'Would apply' if dry_run else 'Applied'} {result.parameter_name}: "
                                   f"{old_value} -> {result.new_value}")
                
            except Exception as e:
                failed_changes.append({
                    'parameter': result.parameter_name,
                    'error': str(e)
                })
                self.logger.error(f"Failed to apply {result.parameter_name}: {e}")
        
        return {
            'dry_run': dry_run,
            'applied_changes': applied_changes,
            'failed_changes': failed_changes,
            'recommendation': asdict(recommendation)
        }
    
    def export_optimization_report(self, output_file: str) -> Dict:
        """Export comprehensive optimization report"""
        
        # Get recent optimization history
        recent_optimizations = self.optimization_history[-10:] if self.optimization_history else []
        
        # Calculate optimization statistics
        if recent_optimizations:
            improvements = [opt['overall_improvement'] for opt in recent_optimizations 
                          if opt.get('overall_improvement', 0) > 0]
            avg_improvement = mean(improvements) if improvements else 0
            total_optimizations = len(recent_optimizations)
        else:
            avg_improvement = 0
            total_optimizations = 0
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_parameters': len(self.parameters),
                'recent_optimizations': total_optimizations,
                'average_improvement': avg_improvement,
                'optimization_engine_version': '1.0.0'
            },
            'current_parameters': {
                name: {
                    'current_value': param.current_value,
                    'description': param.description,
                    'impact_metrics': param.impact_metrics
                }
                for name, param in self.parameters.items()
            },
            'optimization_history': recent_optimizations,
            'parameter_analysis': {}
        }
        
        # Add parameter impact analysis
        for param_name in self.parameters:
            impact = self.analyze_parameter_impact(param_name)
            if impact:
                report['parameter_analysis'][param_name] = impact
        
        # Save report
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Exported optimization report to {output_file}")
        return report['summary']


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Optimization Engine for Test Parameters')
    parser.add_argument('--config', default='optimization_config.json', help='Configuration file')
    parser.add_argument('--action', choices=['analyze', 'optimize', 'apply', 'report'], 
                       required=True, help='Action to perform')
    
    # Analysis options
    parser.add_argument('--parameter', help='Specific parameter to analyze/optimize')
    parser.add_argument('--days', type=int, default=30, help='Days of historical data to analyze')
    
    # Optimization options
    parser.add_argument('--method', choices=['hill_climbing', 'bayesian', 'grid_search'],
                       default='hill_climbing', help='Optimization method')
    parser.add_argument('--configuration', default='default', help='Target configuration name')
    
    # Application options
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without applying changes')
    parser.add_argument('--recommendation-file', help='Recommendation file to apply')
    
    # Report options
    parser.add_argument('--output', help='Output file for reports')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        engine = OptimizationEngine(config_file=args.config)
        
        if args.action == 'analyze':
            if args.parameter:
                impact = engine.analyze_parameter_impact(args.parameter, args.days)
                print(f"Parameter impact analysis for {args.parameter}:")
                for metric, data in impact.items():
                    print(f"  {metric}: correlation={data['correlation']:.3f}, "
                          f"trend_strength={data['trend_strength']:.3f}")
            else:
                print("Error: --parameter required for analyze action")
        
        elif args.action == 'optimize':
            if args.parameter:
                result = engine.optimize_parameter(args.parameter, optimization_method=args.method)
                print(f"Optimization result for {args.parameter}:")
                print(f"  Current: {result.old_value}")
                print(f"  Recommended: {result.new_value}")
                print(f"  Expected improvement: {result.expected_improvement:.1f}%")
                print(f"  Confidence: {result.confidence:.1f}")
                print(f"  Reasoning: {result.reasoning}")
            else:
                recommendation = engine.optimize_configuration(args.configuration, args.method)
                print(f"Configuration optimization for {args.configuration}:")
                print(f"  Overall improvement: {recommendation.overall_improvement:.1f}%")
                print(f"  Risk level: {recommendation.risk_level}")
                print(f"  Parameters to change: {len(recommendation.results)}")
                
                # Save recommendation
                rec_file = f"optimization_recommendation_{args.configuration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(rec_file, 'w') as f:
                    json.dump(asdict(recommendation), f, indent=2)
                print(f"  Recommendation saved to: {rec_file}")
        
        elif args.action == 'apply':
            if not args.recommendation_file:
                print("Error: --recommendation-file required for apply action")
                exit(1)
            
            with open(args.recommendation_file, 'r') as f:
                rec_data = json.load(f)
                recommendation = OptimizationRecommendation(**rec_data)
            
            result = engine.apply_optimization(recommendation, dry_run=args.dry_run)
            
            print(f"Optimization application ({'dry run' if args.dry_run else 'live'}):")
            print(f"  Changes applied: {len(result['applied_changes'])}")
            print(f"  Changes failed: {len(result['failed_changes'])}")
            
            for change in result['applied_changes']:
                print(f"    {change['parameter']}: {change['old_value']} -> {change['new_value']}")
        
        elif args.action == 'report':
            output_file = args.output or f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summary = engine.export_optimization_report(output_file)
            
            print(f"Optimization report generated:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)