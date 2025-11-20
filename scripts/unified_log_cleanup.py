#!/usr/bin/env python3
"""
统一日志清理脚本
处理Python和Java统一后的日志文件
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

# 从BackendService导入配置
backend_root = project_root / "BackendService"
sys.path.insert(0, str(backend_root))

try:
    from CoreConfig.settings import get_settings
    settings = get_settings()
except ImportError:
    # 如果无法导入配置，使用默认值
    class Settings:
        LOG_BACKUP_COUNT = 10
    settings = Settings()

# 定义统一的日志路径
SHARED_LOG_DIR = Path("shared_logs")

LOG_PATHS = {
    "Python应用日志": SHARED_LOG_DIR / "app",
    "Python错误日志": SHARED_LOG_DIR / "error",
    "Python审计日志": SHARED_LOG_DIR / "audit",
    "Python性能日志": SHARED_LOG_DIR / "performance",
    "Python匹配日志": SHARED_LOG_DIR / "matching",
    "PythonAPI日志": SHARED_LOG_DIR / "api",
    "Python业务日志": SHARED_LOG_DIR / "business",
    "PythonCelery日志": SHARED_LOG_DIR / "celery",
    "Python工具日志": SHARED_LOG_DIR / "utils",
    "Java应用日志": SHARED_LOG_DIR / "app",
    "Java错误日志": SHARED_LOG_DIR / "error",
    "Java轨迹日志": SHARED_LOG_DIR / "trajectory",
    "Java业务日志": SHARED_LOG_DIR / "business"
}

# 轮转配置
ROTATION_CONFIG = {
    "retention_days": settings.LOG_BACKUP_COUNT * 7,  # 根据备份数量计算保留天数
    "compress_days": 7  # 7天前的日志进行压缩
}


def get_file_age(file_path: Path) -> int:
    """获取文件年龄（天数）"""
    if not file_path.exists():
        return 0
    
    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    age = (datetime.now() - file_time).days
    return age


def format_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def compress_old_logs(log_dir: Path, days_threshold: int = 7, dry_run: bool = False) -> List[Path]:
    """压缩旧日志文件"""
    compressed_files = []
    
    try:
        for log_file in log_dir.glob("*.log*"):
            if log_file.suffix == ".gz":
                continue  # 跳过已压缩的文件
                
            try:
                age = get_file_age(log_file)
                if age >= days_threshold:
                    # 压缩文件
                    compressed_file = log_file.with_suffix(log_file.suffix + ".gz")
                    
                    if not dry_run:
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # 删除原文件
                        log_file.unlink()
                    
                    compressed_files.append(compressed_file)
                    file_size = log_file.stat().st_size if log_file.exists() else 0
                    action = "将压缩" if dry_run else "压缩"
                    print(f"  ✓ {action}: {log_file.name} ({format_size(file_size)}) -> {compressed_file.name}")
            except Exception as e:
                print(f"  ✗ 压缩失败 {log_file}: {e}")
                
    except Exception as e:
        print(f"  ✗ 遍历目录失败 {log_dir}: {e}")
        
    return compressed_files


def remove_old_logs(log_dir: Path, retention_days: int = 30, dry_run: bool = False) -> List[Path]:
    """删除过期日志文件"""
    removed_files = []
    
    try:
        for log_file in log_dir.glob("*.log*"):
            try:
                age = get_file_age(log_file)
                if age > retention_days:
                    file_size = log_file.stat().st_size if log_file.exists() else 0
                    if not dry_run:
                        log_file.unlink()
                    removed_files.append(log_file)
                    action = "将删除" if dry_run else "删除"
                    print(f"  ✓ {action}: {log_file.name} ({format_size(file_size)}, {age}天)")
            except Exception as e:
                print(f"  ✗ 删除失败 {log_file}: {e}")
                
    except Exception as e:
        print(f"  ✗ 遍历目录失败 {log_dir}: {e}")
        
    return removed_files


def cleanup_log_directory(log_type: str, log_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """清理单个日志目录"""
    action = "预演" if dry_run else "清理"
    print(f"{action} {log_type} 日志目录: {log_path}")
    
    # 确保目录存在
    log_path.mkdir(parents=True, exist_ok=True)
    
    if not any(log_path.iterdir()):
        print(f"  ⚠ 目录为空: {log_path}")
        return 0, 0
    
    # 压缩旧日志
    compressed = compress_old_logs(log_path, ROTATION_CONFIG["compress_days"], dry_run)
    
    # 删除过期日志
    removed = remove_old_logs(log_path, ROTATION_CONFIG["retention_days"], dry_run)
    
    if not dry_run:
        # 统计文件数量
        total_files = len(list(log_path.glob("*.log*")))
        total_size = sum(f.stat().st_size for f in log_path.glob("*.log*") if f.is_file())
        
        print(f"  📊 统计: {total_files} 个文件, {format_size(total_size)}")
    
    print(f"  ✓ 压缩: {len(compressed)} 个文件")
    print(f"  ✓ 删除: {len(removed)} 个文件")
    
    return len(compressed), len(removed)


def cleanup_all_logs(dry_run: bool = False):
    """清理所有日志"""
    action = "预演" if dry_run else "执行"
    print("=" * 60)
    print(f"MapTools 统一日志清理 - {action}")
    print("=" * 60)
    
    total_compressed = 0
    total_removed = 0
    
    for log_type, log_path in LOG_PATHS.items():
        compressed, removed = cleanup_log_directory(log_type, log_path, dry_run)
        total_compressed += compressed
        total_removed += removed
        print()
    
    print("=" * 60)
    print(f"清理完成: 压缩 {total_compressed} 个文件, 删除 {total_removed} 个文件")
    if dry_run:
        print("注意: 这只是预演，尚未实际执行操作。")
    print("=" * 60)


def show_log_statistics():
    """显示日志统计信息"""
    print("=" * 60)
    print("统一日志统计信息")
    print("=" * 60)
    
    total_size = 0
    total_files = 0
    
    for log_type, log_path in LOG_PATHS.items():
        if not log_path.exists():
            continue
            
        files = list(log_path.glob("*.log*"))
        size = sum(f.stat().st_size for f in files if f.is_file())
        
        print(f"{log_type:20} | {len(files):3} 文件 | {format_size(size):>8}")
        total_files += len(files)
        total_size += size
    
    print("-" * 60)
    print(f"{'总计':20} | {total_files:3} 文件 | {format_size(total_size):>8}")
    print("=" * 60)


def show_help():
    """显示帮助信息"""
    help_text = """
用法: python unified_log_cleanup.py [命令] [选项]

命令:
  cleanup         清理日志文件（默认命令）
  stats           显示日志统计信息
  compress        压缩旧日志文件
  help            显示此帮助信息

选项:
  --dry-run       预演模式，显示将要执行的操作但不实际执行
  --help, -h      显示帮助信息

示例:
  python unified_log_cleanup.py              # 执行日志清理
  python unified_log_cleanup.py cleanup --dry-run  # 预演日志清理
  python unified_log_cleanup.py stats        # 显示日志统计信息
  python unified_log_cleanup.py compress     # 压缩旧日志文件
    """
    print(help_text)
    sys.exit(0)


def main():
    """主函数"""
    dry_run = False
    command = "cleanup"  # 默认命令
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--dry-run":
                dry_run = True
            elif arg in ["cleanup", "stats", "compress", "help"]:
                command = arg
            elif arg in ["--help", "-h"]:
                show_help()
                return
            else:
                print("未知参数:", arg)
                show_help()
                return
    
    if command == "cleanup":
        cleanup_all_logs(dry_run)
    elif command == "stats":
        show_log_statistics()
    elif command == "compress":
        # 只压缩，不删除
        for log_type, log_path in LOG_PATHS.items():
            if log_path.exists():
                compress_old_logs(log_path, 1, dry_run)  # 压缩1天前的文件
    elif command == "help":
        show_help()


if __name__ == "__main__":
    main()
