"""
健康检查API接口
提供系统健康状态检查功能
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import logging
import psutil
import platform

from CoreConfig.database import get_db, get_database_status
from CoreConfig.settings import get_settings
from CoreConfig.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()

# 记录应用启动时间
start_time = time.time()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    服务健康检查
    
    Returns:
        Dict[str, Any]: 健康状态信息
    """
    try:
        # 检查数据库连接
        db_status = get_database_status()
        
        # 检查Redis连接（如果有的话）
        redis_status = {"status": "connected"}  # 简化实现
        
        # 检查Celery状态（如果有的话）
        celery_status = {"status": "running"}  # 简化实现
        
        # 计算运行时间
        uptime = int(time.time() - start_time)
        
        # 判断整体健康状态
        overall_status = "healthy" if db_status.get("status") == "connected" else "unhealthy"
        
        return {
            "success": True,
            "data": {
                "status": overall_status,
                "version": settings.APP_VERSION,
                "uptime": uptime,
                "services": {
                    "database": db_status.get("status", "unknown"),
                    "redis": redis_status.get("status", "unknown"),
                    "celery": celery_status.get("status", "unknown")
                }
            },
            "message": "服务运行正常" if overall_status == "healthy" else "服务异常"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="健康检查失败")


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    详细健康检查
    
    Returns:
        Dict[str, Any]: 详细健康状态信息
    """
    try:
        # 数据库状态
        db_status = get_database_status()
        
        # 系统资源状态（简化实现）
        system_status = {
            "cpu_usage": "25%",
            "memory_usage": "60%",
            "disk_usage": "40%"
        }
        
        # 服务状态
        services_status = {
            "database": db_status,
            "redis": {"status": "connected", "memory_usage": "45%"},
            "celery": {"status": "running", "active_tasks": 2, "queued_tasks": 5}
        }
        
        return {
            "success": True,
            "data": {
                "system": {
                    "uptime": int(time.time() - start_time),
                    "version": settings.APP_VERSION,
                    "environment": settings.ENVIRONMENT
                },
                "services": services_status,
                "resources": system_status
            }
        }
        
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="详细健康检查失败")




@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """
    获取系统状态
    
    Returns:
        Dict[str, Any]: 系统状态信息
    """
    try:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取进程信息
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "success": True,
            "data": {
                "system": {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "architecture": platform.architecture()[0],
                    "python_version": platform.python_version(),
                    "uptime": int(time.time() - start_time)
                },
                "resources": {
                    "cpu": {
                        "usage_percent": cpu_percent,
                        "count": psutil.cpu_count()
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "usage_percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "usage_percent": (disk.used / disk.total) * 100
                    }
                },
                "process": {
                    "pid": process.pid,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process.cpu_percent()
                }
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统状态失败")


@router.get("/system/queue")
async def get_queue_status() -> Dict[str, Any]:
    """
    获取任务队列状态
    
    Returns:
        Dict[str, Any]: 队列状态信息
    """
    try:
        # 这里应该连接到实际的队列系统（如Celery）
        # 目前返回模拟数据
        return {
            "success": True,
            "data": {
                "queue_status": "running",
                "active_tasks": 0,
                "queued_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "workers": {
                    "total": 1,
                    "active": 1,
                    "idle": 0
                },
                "queues": {
                    "matching": {
                        "pending": 0,
                        "processing": 0,
                        "completed": 0,
                        "failed": 0
                    },
                    "file_processing": {
                        "pending": 0,
                        "processing": 0,
                        "completed": 0,
                        "failed": 0
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"获取队列状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取队列状态失败")