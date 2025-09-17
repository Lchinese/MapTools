import traceback

from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.geo_utils import GeoUtils
from app.core.matching_service import MatchingService
from app.db.session import SessionLocal
from app.models.matching_task import MatchingTask
from app.utils.logger import logger


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
    db: Session = None
    try:
        db = SessionLocal()
        matching_task = db.query(MatchingTask).filter(MatchingTask.task_id == task_id).first()
        if not matching_task:
            return {
                "success": False,
                "task_id": task_id,
                "error": "任务不存在"
            }
        
        # 初始化匹配服务
        matching_service = MatchingService(
            mapbox_access_token=settings.MAPBOX_ACCESS_TOKEN,
            mapbox_profile=settings.MAPBOX_PROFILE,
            mapbox_max_radius=settings.MAPBOX_MAX_RADIUS,
            mapbox_max_results=settings.MAPBOX_MAX_RESULTS,
            mapbox_max_retries=settings.MAPBOX_MAX_RETRIES,
            mapbox_retry_delay=settings.MAPBOX_RETRY_DELAY
        )
        
        # 解析轨迹点
        trajectory_points = matching_task.trajectory_points
        gps_points = [GeoUtils.parse_gps_point(point) for point in trajectory_points]
        
        # 初始化任务进度
        progress_tracker = TaskProgress(total=len(trajectory_points))
        
        # 执行匹配
        matched_points_data = []
        for index, gps_point in enumerate(gps_points):
            try:
                match_result = matching_service.match_point(gps_point)
                matched_points_data.append(match_result)
                
                # 更新进度
                progress_tracker.update(success=True)
                matching_task.progress = progress_tracker.get_progress()
                db.commit()
                
            except Exception as e:
                logger.warning(f"匹配点 {index} 失败: {str(e)}")
                progress_tracker.update(success=False)
                continue
        
        # 更新任务状态为完成
        matching_task.status = "completed"
        matching_task.matched_points_data = matched_points_data
        matching_task.completed_at = GeoUtils.get_current_time()
        db.commit()
        
        return {
            "success": True,
            "task_id": task_id,
            "matched_points_data": matched_points_data
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
