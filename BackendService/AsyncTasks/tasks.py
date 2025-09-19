"""
异步任务处理模块
处理地图匹配等耗时任务
"""

import traceback
import sys
import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .celery_app import celery_app
from CoreConfig.settings import get_settings
from UtilityTools.geo_utils import GeoUtils
from BusinessServices.matching_service import MatchingService
from CoreConfig.database import get_db
from DataModels.Models.matching import MatchingTask, MatchedPoint
from CoreConfig.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TaskProgress:
    """
    任务进度管理器
    """
    def __init__(self, total: int):
        self.total = total
        self.processed = 0
        self.errors = 0
        
    def update(self, success: bool = True) -> None:
        self.processed += 1
        if not success:
            self.errors += 1
        
    def get_progress(self) -> float:
        return round(self.processed / self.total * 100, 2) if self.total > 0 else 0


@celery_app.task(bind=True)
def process_matching_task(self, task_id: str) -> Dict[str, Any]:
    """
    处理地图匹配任务
    
    Args:
        task_id: 匹配任务ID
        
    Returns:
        处理结果字典
    """
    db = None
    try:
        # 获取数据库会话
        db = next(get_db())
        matching_task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
        if not matching_task:
            return {
                "success": False,
                "task_id": task_id,
                "error": "任务不存在"
            }
        
        # 更新任务状态为运行中
        matching_task.status = "running"
        matching_task.started_at = GeoUtils.get_current_time()
        db.commit()
        
        # 初始化匹配服务
        matching_service = MatchingService()
        
        # 获取轨迹点
        trajectory_points = matching_task.trajectory.points
        if not trajectory_points:
            raise ValueError("轨迹点为空")
        
        # 初始化任务进度
        progress_tracker = TaskProgress(total=len(trajectory_points))
        
        # 执行匹配
        matched_points_data = []
        for index, trajectory_point in enumerate(trajectory_points):
            try:
                # 创建GPS点
                gps_point = matching_service.create_gps_point(trajectory_point)
                
                # 执行匹配
                match_result = matching_service.match_point(gps_point)
                
                # 创建匹配点对象
                matched_point = MatchedPoint(
                    matched_point_id=GeoUtils.generate_uuid(),
                    trajectory_id=matching_task.trajectory_id,
                    matching_task_id=task_id,
                    original_point_id=trajectory_point.point_id,
                    original_latitude=gps_point.latitude,
                    original_longitude=gps_point.longitude,
                    matched_latitude=match_result["matched_lat"],
                    matched_longitude=match_result["matched_lon"],
                    matched_timestamp=GeoUtils.get_current_time(),
                    distance=match_result["distance"],
                    confidence=match_result["confidence"],
                    road_name=match_result.get("road_name", ""),
                    road_type=match_result.get("road_type", "")
                )
                
                matched_points_data.append(matched_point)
                
                # 更新进度
                progress_tracker.update(success=True)
                matching_task.progress = progress_tracker.get_progress()
                db.commit()
                
            except Exception as e:
                logger.warning(f"匹配点 {index} 失败: {str(e)}")
                progress_tracker.update(success=False)
                continue
        
        # 保存匹配点到数据库
        db.add_all(matched_points_data)
        
        # 更新任务状态为完成
        matching_task.status = "completed"
        matching_task.matched_points_count = len(matched_points_data)
        matching_task.unmatched_points_count = len(trajectory_points) - len(matched_points_data)
        matching_task.accuracy = sum([mp.confidence for mp in matched_points_data]) / len(matched_points_data) if matched_points_data else 0
        matching_task.completed_at = GeoUtils.get_current_time()
        db.commit()
        
        return {
            "success": True,
            "task_id": task_id,
            "matched_points_count": len(matched_points_data)
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"处理匹配任务 {task_id} 失败: {str(e)}\n{error_traceback}")
        
        if db:
            # 更新任务状态为失败
            matching_task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
            if matching_task:
                matching_task.status = "failed"
                matching_task.error_message = str(e)
                matching_task.completed_at = GeoUtils.get_current_time()
                db.commit()
        
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e),
            "traceback": error_traceback
        }
    finally:
        if db:
            db.close()


@celery_app.task(bind=True)
def process_batch_matching_tasks(self, task_ids: List[str]) -> Dict[str, Any]:
    """
    批量处理地图匹配任务
    
    Args:
        task_ids: 匹配任务ID列表
        
    Returns:
        处理结果字典
    """
    results = []
    for task_id in task_ids:
        try:
            result = process_matching_task(task_id)
            results.append(result)
        except Exception as e:
            logger.error(f"批量处理任务 {task_id} 失败: {str(e)}")
            results.append({
                "success": False,
                "task_id": task_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "results": results
    }