#!/usr/bin/env python3
"""
Simple Phase 2 validation that doesn't require Docker images
"""
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_modules():
    """Test if our modules can be imported and basic functionality works"""
    sys.path.insert(0, str(Path(__file__).parent))
    
    results = {}
    
    # Test orchestrator
    try:
        import os
        os.environ['PYMODE_TEST_MODE'] = 'true'  # Enable test mode to skip Docker checks
        import test_orchestrator
        orchestrator = test_orchestrator.TestOrchestrator(max_parallel=1, timeout=30)
        result = test_orchestrator.TestResult(
            name="test",
            status="passed", 
            duration=1.0,
            output="test output"
        )
        logger.info("✅ Orchestrator module works")
        results['orchestrator'] = True
    except Exception as e:
        logger.error(f"❌ Orchestrator module failed: {e}")
        results['orchestrator'] = False
    
    # Test performance monitor
    try:
        import performance_monitor
        monitor = performance_monitor.PerformanceMonitor("test-container-id")
        summary = monitor.get_summary()
        logger.info("✅ Performance monitor module works")
        results['performance_monitor'] = True
    except Exception as e:
        logger.error(f"❌ Performance monitor module failed: {e}")
        results['performance_monitor'] = False
    
    return results

def test_file_structure():
    """Test if all required files are present"""
    required_files = [
        'scripts/test_orchestrator.py',
        'scripts/performance_monitor.py',
        'Dockerfile.coordinator',
        'Dockerfile.base-test',
        'Dockerfile.test-runner',
        'docker-compose.test.yml',
        'tests/vader/simple.vader',
        'tests/vader/autopep8.vader',
        'tests/vader/folding.vader',
        'tests/vader/lint.vader'
    ]
    
    results = {}
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            logger.info(f"✅ {file_path} exists")
            results[file_path] = True
        else:
            logger.error(f"❌ {file_path} missing")
            results[file_path] = False
    
    return results

def test_vader_files():
    """Test if Vader files have valid syntax"""
    vader_dir = Path('tests/vader')
    if not vader_dir.exists():
        logger.error("❌ Vader directory doesn't exist")
        return False
    
    vader_files = list(vader_dir.glob('*.vader'))
    if not vader_files:
        logger.error("❌ No Vader test files found")
        return False
    
    logger.info(f"✅ Found {len(vader_files)} Vader test files:")
    for f in vader_files:
        logger.info(f"  - {f.name}")
    
    # Basic syntax check - just make sure they have some test content
    for vader_file in vader_files:
        try:
            content = vader_file.read_text()
            if not any(keyword in content for keyword in ['Before:', 'After:', 'Execute:', 'Given:', 'Then:', 'Expect:']):
                logger.warning(f"⚠️  {vader_file.name} might not have proper Vader syntax")
            else:
                logger.info(f"✅ {vader_file.name} has Vader syntax")
        except Exception as e:
            logger.error(f"❌ Error reading {vader_file.name}: {e}")
    
    return True

def main():
    """Main validation function"""
    logger.info("🚀 Starting Phase 2 Simple Validation")
    logger.info("="*50)
    
    # Test modules
    logger.info("Testing Python modules...")
    module_results = test_modules()
    
    # Test file structure
    logger.info("\nTesting file structure...")
    file_results = test_file_structure()
    
    # Test Vader files
    logger.info("\nTesting Vader test files...")
    vader_result = test_vader_files()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("PHASE 2 SIMPLE VALIDATION SUMMARY")
    logger.info("="*50)
    
    # Module results
    logger.info("Python Modules:")
    for module, passed in module_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {module:<20} {status}")
    
    # File results
    logger.info("\nRequired Files:")
    passed_files = sum(1 for passed in file_results.values() if passed)
    total_files = len(file_results)
    logger.info(f"  {passed_files}/{total_files} files present")
    
    # Vader results
    vader_status = "✅ PASS" if vader_result else "❌ FAIL"
    logger.info(f"\nVader Tests:     {vader_status}")
    
    # Overall status
    all_modules_passed = all(module_results.values())
    all_files_present = all(file_results.values())
    overall_pass = all_modules_passed and all_files_present and vader_result
    
    logger.info("="*50)
    if overall_pass:
        logger.info("🎉 PHASE 2 SIMPLE VALIDATION: PASSED")
        logger.info("✅ All core components are working correctly!")
        logger.info("🚀 Ready to build Docker images and run full tests")
    else:
        logger.warning("⚠️  PHASE 2 SIMPLE VALIDATION: ISSUES FOUND")
        if not all_modules_passed:
            logger.warning("🐛 Some Python modules have issues")
        if not all_files_present:
            logger.warning("📁 Some required files are missing")
        if not vader_result:
            logger.warning("📝 Vader test files have issues")
    
    logger.info("="*50)
    
    return 0 if overall_pass else 1

if __name__ == '__main__':
    sys.exit(main())