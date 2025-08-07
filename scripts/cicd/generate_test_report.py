#!/usr/bin/env python3
"""
Test Report Generator for Python-mode
Aggregates test results from multiple test runs and generates comprehensive reports.
"""
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import html


class TestReportGenerator:
    def __init__(self):
        self.results = {}
        self.summary = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'timeout': 0,
            'total_duration': 0.0,
            'configurations': set()
        }
    
    def load_results(self, input_dir: Path):
        """Load test results from JSON files in the input directory."""
        result_files = list(input_dir.glob('**/test-results*.json'))
        
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    
                # Extract configuration from filename
                # Expected format: test-results-python-version-vim-version-suite.json
                parts = result_file.stem.split('-')
                if len(parts) >= 5:
                    config = f"Python {parts[2]}, Vim {parts[3]}, {parts[4].title()}"
                    self.summary['configurations'].add(config)
                else:
                    config = result_file.stem
                
                self.results[config] = data
                
                # Update summary statistics
                for test_name, test_result in data.items():
                    self.summary['total_tests'] += 1
                    self.summary['total_duration'] += test_result.get('duration', 0)
                    
                    status = test_result.get('status', 'unknown')
                    if status == 'passed':
                        self.summary['passed'] += 1
                    elif status == 'failed':
                        self.summary['failed'] += 1
                    elif status == 'timeout':
                        self.summary['timeout'] += 1
                    else:
                        self.summary['errors'] += 1
                        
            except Exception as e:
                print(f"Warning: Could not load {result_file}: {e}")
                continue
    
    def generate_html_report(self, output_file: Path):
        """Generate a comprehensive HTML test report."""
        
        # Convert set to sorted list for display
        configurations = sorted(list(self.summary['configurations']))
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python-mode Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #007acc;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #007acc;
        }}
        .metric h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .metric .value {{
            font-size: 2em;
            font-weight: bold;
            color: #007acc;
        }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .timeout {{ color: #fd7e14; }}
        .error {{ color: #6f42c1; }}
        
        .configuration {{
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 6px;
            overflow: hidden;
        }}
        .config-header {{
            background: #007acc;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
        }}
        .test-results {{
            padding: 0;
        }}
        .test-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
        }}
        .test-item:last-child {{
            border-bottom: none;
        }}
        .test-name {{
            font-weight: 500;
            flex: 1;
        }}
        .test-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-passed {{
            background: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status-timeout {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-error {{
            background: #e2e3e5;
            color: #383d41;
        }}
        .test-duration {{
            margin-left: 10px;
            color: #666;
            font-size: 0.9em;
        }}
        .error-details {{
            background: #f8f9fa;
            padding: 15px;
            margin-top: 10px;
            border-radius: 4px;
            border-left: 4px solid #dc3545;
        }}
        .error-output {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
            background: #fff;
            padding: 10px;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Python-mode Test Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <div class="value">{self.summary['total_tests']}</div>
            </div>
            <div class="metric">
                <h3>Passed</h3>
                <div class="value passed">{self.summary['passed']}</div>
            </div>
            <div class="metric">
                <h3>Failed</h3>
                <div class="value failed">{self.summary['failed']}</div>
            </div>
            <div class="metric">
                <h3>Errors/Timeouts</h3>
                <div class="value error">{self.summary['errors'] + self.summary['timeout']}</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value">{self._calculate_success_rate():.1f}%</div>
            </div>
            <div class="metric">
                <h3>Total Duration</h3>
                <div class="value">{self.summary['total_duration']:.1f}s</div>
            </div>
        </div>
        
        <div class="configurations-section">
            <h2>Test Results by Configuration</h2>
"""
        
        # Add results for each configuration
        for config_name, config_results in self.results.items():
            html_content += f"""
            <div class="configuration">
                <div class="config-header">{html.escape(config_name)}</div>
                <div class="test-results">
"""
            
            for test_name, test_result in config_results.items():
                status = test_result.get('status', 'unknown')
                duration = test_result.get('duration', 0)
                error = test_result.get('error')
                output = test_result.get('output', '')
                
                status_class = f"status-{status}" if status in ['passed', 'failed', 'timeout', 'error'] else 'status-error'
                
                html_content += f"""
                    <div class="test-item">
                        <div class="test-name">{html.escape(test_name)}</div>
                        <div>
                            <span class="test-status {status_class}">{status}</span>
                            <span class="test-duration">{duration:.2f}s</span>
                        </div>
                    </div>
"""
                
                # Add error details if present
                if error or (status in ['failed', 'error'] and output):
                    error_text = error or output
                    html_content += f"""
                    <div class="error-details">
                        <strong>Error Details:</strong>
                        <div class="error-output">{html.escape(error_text[:1000])}{'...' if len(error_text) > 1000 else ''}</div>
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="footer">
            <p>Configurations tested: {', '.join(configurations)}</p>
            <p>Report generated by Python-mode Test Infrastructure</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def generate_markdown_summary(self, output_file: Path):
        """Generate a markdown summary for PR comments."""
        success_rate = self._calculate_success_rate()
        
        # Determine overall status
        if success_rate >= 95:
            status_emoji = "✅"
            status_text = "EXCELLENT"
        elif success_rate >= 80:
            status_emoji = "⚠️"
            status_text = "NEEDS ATTENTION"
        else:
            status_emoji = "❌"
            status_text = "FAILING"
        
        markdown_content = f"""# {status_emoji} Python-mode Test Results

## Summary

| Metric | Value |
|--------|-------|
| **Overall Status** | {status_emoji} {status_text} |
| **Success Rate** | {success_rate:.1f}% |
| **Total Tests** | {self.summary['total_tests']} |
| **Passed** | ✅ {self.summary['passed']} |
| **Failed** | ❌ {self.summary['failed']} |
| **Errors/Timeouts** | ⚠️ {self.summary['errors'] + self.summary['timeout']} |
| **Duration** | {self.summary['total_duration']:.1f}s |

## Configuration Results

"""
        
        for config_name, config_results in self.results.items():
            config_passed = sum(1 for r in config_results.values() if r.get('status') == 'passed')
            config_total = len(config_results)
            config_rate = (config_passed / config_total * 100) if config_total > 0 else 0
            
            config_emoji = "✅" if config_rate >= 95 else "⚠️" if config_rate >= 80 else "❌"
            
            markdown_content += f"- {config_emoji} **{config_name}**: {config_passed}/{config_total} passed ({config_rate:.1f}%)\n"
        
        if self.summary['failed'] > 0 or self.summary['errors'] > 0 or self.summary['timeout'] > 0:
            markdown_content += "\n## Failed Tests\n\n"
            
            for config_name, config_results in self.results.items():
                failed_tests = [(name, result) for name, result in config_results.items() 
                              if result.get('status') in ['failed', 'error', 'timeout']]
                
                if failed_tests:
                    markdown_content += f"### {config_name}\n\n"
                    for test_name, test_result in failed_tests:
                        status = test_result.get('status', 'unknown')
                        error = test_result.get('error', 'No error details available')
                        markdown_content += f"- **{test_name}** ({status}): {error[:100]}{'...' if len(error) > 100 else ''}\n"
                    markdown_content += "\n"
        
        markdown_content += f"""
---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} by Python-mode CI*
"""
        
        with open(output_file, 'w') as f:
            f.write(markdown_content)
    
    def _calculate_success_rate(self) -> float:
        """Calculate the overall success rate."""
        if self.summary['total_tests'] == 0:
            return 0.0
        return (self.summary['passed'] / self.summary['total_tests']) * 100


def main():
    parser = argparse.ArgumentParser(description='Generate test reports for Python-mode')
    parser.add_argument('--input-dir', type=Path, default='.', 
                       help='Directory containing test result files')
    parser.add_argument('--output-file', type=Path, default='test-report.html',
                       help='Output HTML report file')
    parser.add_argument('--summary-file', type=Path, default='test-summary.md',
                       help='Output markdown summary file')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Scanning for test results in: {args.input_dir}")
    
    generator = TestReportGenerator()
    generator.load_results(args.input_dir)
    
    if generator.summary['total_tests'] == 0:
        print("Warning: No test results found!")
        sys.exit(1)
    
    if args.verbose:
        print(f"Found {generator.summary['total_tests']} tests across "
              f"{len(generator.summary['configurations'])} configurations")
    
    # Generate HTML report
    generator.generate_html_report(args.output_file)
    print(f"HTML report generated: {args.output_file}")
    
    # Generate markdown summary
    generator.generate_markdown_summary(args.summary_file)
    print(f"Markdown summary generated: {args.summary_file}")
    
    # Print summary to stdout
    success_rate = generator._calculate_success_rate()
    print(f"\nTest Summary: {generator.summary['passed']}/{generator.summary['total_tests']} "
          f"passed ({success_rate:.1f}%)")
    
    # Exit with error code if tests failed
    if generator.summary['failed'] > 0 or generator.summary['errors'] > 0 or generator.summary['timeout'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()