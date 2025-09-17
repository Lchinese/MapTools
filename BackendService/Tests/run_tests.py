"""
测试运行脚本
"""

import sys
import os
import subprocess
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_unit_tests(use_pytest=True):
    """运行单元测试"""
    print("运行单元测试...")
    if use_pytest and check_pytest_installed():
        cmd = [
            sys.executable, "-m", "pytest", 
            "Tests/unit/", 
            "-v", 
            "--tb=short"
        ]
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    else:
        # 直接使用unittest运行测试
        loader = unittest.TestLoader()
        suite = loader.discover('Tests/unit', pattern='test_*.py', top_level_dir='.')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

def run_integration_tests(use_pytest=True):
    """运行集成测试"""
    print("运行集成测试...")
    if use_pytest and check_pytest_installed():
        cmd = [
            sys.executable, "-m", "pytest", 
            "Tests/integration/", 
            "-v", 
            "--tb=short"
        ]
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    else:
        # 直接使用unittest运行测试
        loader = unittest.TestLoader()
        suite = loader.discover('Tests/integration', pattern='test_*.py', top_level_dir='.')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

def run_all_tests(use_pytest=True):
    """运行所有测试"""
    if use_pytest and check_pytest_installed():
        print("运行所有测试...")
        cmd = [
            sys.executable, "-m", "pytest", 
            "Tests/", 
            "-v", 
            "--tb=short"
            # "--cov=BackendService",
            # "--cov-report=html",
            # "--cov-report=term"
        ]
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    else:
        # 直接使用unittest运行所有测试
        print("运行所有测试 (使用unittest)...")
        loader = unittest.TestLoader()
        suite = loader.discover('Tests', pattern='test_*.py', top_level_dir='.')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()

def check_pytest_installed():
    """检查pytest是否已安装"""
    try:
        import pytest
        return True
    except ImportError:
        print("未安装pytest，将使用unittest运行测试")
        return False

def main():
    """主函数"""
    use_pytest = True
    test_type = "unit"
    
    for arg in sys.argv[1:]:
        if arg == "--no-pytest":
            use_pytest = False
        else:
            test_type = arg.lower()
    
    if test_type not in ["unit", "integration", "all"]:
        print("用法: python run_tests.py [unit|integration|all] [--no-pytest]")
        sys.exit(1)
    
    print(f"使用 {'pytest' if use_pytest and check_pytest_installed() else 'unittest'} 运行测试")
    
    if test_type == "unit":
        success = run_unit_tests(use_pytest)
    elif test_type == "integration":
        success = run_integration_tests(use_pytest)
    elif test_type == "all":
        success = run_all_tests(use_pytest)
    else:
        print("无效的测试类型。请使用: unit, integration, 或 all")
        sys.exit(1)
    
    if success:
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()