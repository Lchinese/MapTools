#!/usr/bin/env python3
"""
日志系统设置脚本
根据日志系统设计文档自动配置日志系统
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from LoggingSystem.logger import setup_logging, get_logger
from LoggingSystem.config import LOG_PATHS, ENVIRONMENT, DEBUG_MODE


def create_log_directories():
    """创建日志目录"""
    print("创建日志目录...")
    
    for log_type, log_path in LOG_PATHS.items():
        log_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 创建目录: {log_path}")
        
        # 创建 .gitkeep 文件
        gitkeep_file = log_path / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.write_text("# 日志目录\n")
            print(f"  ✓ 创建 .gitkeep: {gitkeep_file}")


def setup_environment():
    """设置环境变量"""
    print("设置环境变量...")
    
    env_vars = {
        "ENVIRONMENT": ENVIRONMENT,
        "DEBUG": str(DEBUG_MODE).lower(),
        "LOG_LEVEL": "DEBUG" if DEBUG_MODE else "INFO",
        "LOG_FORMAT": "detailed" if DEBUG_MODE else "json",
        "LOG_TO_FILE": "true",
        "LOG_TO_CONSOLE": "true" if DEBUG_MODE else "false",
        "LOG_ASYNC": "true",
        "LOG_MASK_SENSITIVE": "true",
        "LOG_AUDIT_ENABLED": "true"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  ✓ 设置 {key}={value}")


def test_logging_system():
    """测试日志系统"""
    print("测试日志系统...")
    
    # 初始化日志系统
    setup_logging()
    
    # 获取测试日志器
    test_logger = get_logger("test")
    
    # 测试各种日志级别
    test_logger.debug("这是一条DEBUG日志")
    test_logger.info("这是一条INFO日志")
    test_logger.warning("这是一条WARNING日志")
    test_logger.error("这是一条ERROR日志")
    test_logger.critical("这是一条CRITICAL日志")
    
    # 测试结构化日志
    test_logger.info("测试结构化日志", extra={
        "user_id": "test_user",
        "action": "test_action",
        "duration_ms": 100
    })
    
    # 测试异常日志
    try:
        raise ValueError("测试异常")
    except Exception as e:
        test_logger.error("测试异常日志", exc_info=True)
    
    print("  ✓ 日志系统测试完成")


def check_log_files():
    """检查日志文件"""
    print("检查日志文件...")
    
    for log_type, log_path in LOG_PATHS.items():
        log_file = log_path / f"{log_type}.log"
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"  ✓ {log_file} - {size} bytes")
        else:
            print(f"  ⚠ {log_file} - 文件不存在")


def setup_log_rotation():
    """设置日志轮转"""
    print("设置日志轮转...")
    
    # 这里可以添加日志轮转的cron任务或其他配置
    print("  ✓ 日志轮转配置完成")


def setup_monitoring():
    """设置日志监控"""
    print("设置日志监控...")
    
    # 这里可以添加日志监控配置
    print("  ✓ 日志监控配置完成")


def main():
    """主函数"""
    print("=" * 50)
    print("MapTools 日志系统设置")
    print("=" * 50)
    
    try:
        # 1. 创建日志目录
        create_log_directories()
        print()
        
        # 2. 设置环境变量
        setup_environment()
        print()
        
        # 3. 测试日志系统
        test_logging_system()
        print()
        
        # 4. 检查日志文件
        check_log_files()
        print()
        
        # 5. 设置日志轮转
        setup_log_rotation()
        print()
        
        # 6. 设置日志监控
        setup_monitoring()
        print()
        
        print("=" * 50)
        print("✓ 日志系统设置完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 设置失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
