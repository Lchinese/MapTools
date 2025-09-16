#!/usr/bin/env python3
"""
日志清理脚本
根据日志系统设计文档清理过期日志文件
"""

import os
import sys
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from LoggingSystem.config import LOG_PATHS, ROTATION_CONFIG


def get_file_age(file_path: Path) -> int:
    """获取文件年龄（天数）"""
    if not file_path.exists():
        return 0
    
    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    age = (datetime.now() - file_time).days
    return age


def compress_old_logs(log_dir: Path, days_threshold: int = 7) -> List[Path]:
    """压缩旧日志文件"""
    compressed_files = []
    
    for log_file in log_dir.glob("*.log*"):
        if log_file.suffix == ".gz":
            continue  # 跳过已压缩的文件
            
        age = get_file_age(log_file)
        if age >= days_threshold:
            # 压缩文件
            compressed_file = log_file.with_suffix(log_file.suffix + ".gz")
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            log_file.unlink()
            compressed_files.append(compressed_file)
            print(f"  ✓ 压缩: {log_file} -> {compressed_file}")
    
    return compressed_files


def remove_old_logs(log_dir: Path, retention_days: int = 30) -> List[Path]:
    """删除过期日志文件"""
    removed_files = []
    
    for log_file in log_dir.glob("*.log*"):
        age = get_file_age(log_file)
        if age > retention_days:
            log_file.unlink()
            removed_files.append(log_file)
            print(f"  ✓ 删除: {log_file} (年龄: {age}天)")
    
    return removed_files


def cleanup_log_directory(log_type: str, log_path: Path) -> Tuple[int, int]:
    """清理单个日志目录"""
    print(f"清理 {log_type} 日志目录: {log_path}")
    
    if not log_path.exists():
        print(f"  ⚠ 目录不存在: {log_path}")
        return 0, 0
    
    # 压缩旧日志
    compressed = compress_old_logs(log_path, ROTATION_CONFIG["retention_days"] // 4)
    
    # 删除过期日志
    removed = remove_old_logs(log_path, ROTATION_CONFIG["retention_days"])
    
    # 统计文件数量
    total_files = len(list(log_path.glob("*.log*")))
    total_size = sum(f.stat().st_size for f in log_path.glob("*.log*") if f.is_file())
    
    print(f"  📊 统计: {total_files} 个文件, {total_size / 1024 / 1024:.2f} MB")
    print(f"  ✓ 压缩: {len(compressed)} 个文件")
    print(f"  ✓ 删除: {len(removed)} 个文件")
    
    return len(compressed), len(removed)


def cleanup_all_logs():
    """清理所有日志"""
    print("=" * 50)
    print("MapTools 日志清理")
    print("=" * 50)
    
    total_compressed = 0
    total_removed = 0
    
    for log_type, log_path in LOG_PATHS.items():
        compressed, removed = cleanup_log_directory(log_type, log_path)
        total_compressed += compressed
        total_removed += removed
        print()
    
    print("=" * 50)
    print(f"清理完成: 压缩 {total_compressed} 个文件, 删除 {total_removed} 个文件")
    print("=" * 50)


def show_log_statistics():
    """显示日志统计信息"""
    print("=" * 50)
    print("日志统计信息")
    print("=" * 50)
    
    total_size = 0
    total_files = 0
    
    for log_type, log_path in LOG_PATHS.items():
        if not log_path.exists():
            continue
            
        files = list(log_path.glob("*.log*"))
        size = sum(f.stat().st_size for f in files if f.is_file())
        
        print(f"{log_type:15} | {len(files):3} 文件 | {size / 1024 / 1024:6.2f} MB")
        total_files += len(files)
        total_size += size
    
    print("-" * 50)
    print(f"{'总计':15} | {total_files:3} 文件 | {total_size / 1024 / 1024:6.2f} MB")
    print("=" * 50)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "cleanup":
            cleanup_all_logs()
        elif command == "stats":
            show_log_statistics()
        elif command == "compress":
            # 只压缩，不删除
            for log_type, log_path in LOG_PATHS.items():
                if log_path.exists():
                    compress_old_logs(log_path, 1)  # 压缩1天前的文件
        else:
            print("用法: python log_cleanup.py [cleanup|stats|compress]")
    else:
        # 默认执行清理
        cleanup_all_logs()


if __name__ == "__main__":
    main()
