"""
测试运行脚本
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_unit_tests():
    """运行单元测试"""
    print("运行单元测试...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "Tests/unit/", 
        "-v", 
        "--tb=short"
    ]
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_integration_tests():
    """运行集成测试"""
    print("运行集成测试...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "Tests/integration/", 
        "-v", 
        "--tb=short"
    ]
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_all_tests():
    """运行所有测试"""
    print("运行所有测试...")
    cmd = [
        sys.executable, "-m", "pytest", 
        "Tests/", 
        "-v", 
        "--tb=short",
        "--cov=BackendService",
        "--cov-report=html",
        "--cov-report=term"
    ]
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python run_tests.py [unit|integration|all]")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "unit":
        success = run_unit_tests()
    elif test_type == "integration":
        success = run_integration_tests()
    elif test_type == "all":
        success = run_all_tests()
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
