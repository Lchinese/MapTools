"""
地图匹配业务逻辑服务
处理地图匹配相关的业务逻辑
"""

import sys
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DataModels.Models.trajectory import Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint
from UtilityTools.geo_utils import GeoUtils, Point as GeoPoint
from CoreConfig.database import get_db
from CoreConfig.logging import get_logger
from MatchingAlgorithms import create_matching_algorithm, AlgorithmFactory

logger = get_logger(__name__)


class MatchingService:
    """地图匹配服务类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化地图匹配服务
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    def start_matching_task(self, trajectory_id: str, algorithm: str = "distance_matching", 
                          parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        启动地图匹配任务
        
        Args:
            trajectory_id: 轨迹ID
            algorithm: 匹配算法
            parameters: 算法参数
            
        Returns:
            任务信息字典
        """
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 获取轨迹
            trajectory = db.query(Trajectory).filter(
                Trajectory.trajectory_id == trajectory_id
            ).first()
            
            if not trajectory:
                return {
                    "success": False,
                    "error": "轨迹不存在"
                }
            
            # 创建匹配任务
            task = MatchingTask(
                task_id=str(uuid.uuid4()),
                trajectory_id=trajectory_id,
                user_id=trajectory.user_id,
                algorithm=algorithm,
                parameters=str(parameters) if parameters else None
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            return {
                "success": True,
                "task_id": task.task_id,
                "message": "匹配任务已创建"
            }
            
        except Exception as e:
            logger.error(f"启动匹配任务失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_matching_task(self, task_id: str) -> Optional[MatchingTask]:
        """
        获取匹配任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            匹配任务对象，如果未找到则返回None
        """
        try:
            db = next(get_db())
            task = db.query(MatchingTask).filter(
                MatchingTask.task_id == task_id
            ).first()
            return task
        except Exception as e:
            logger.error(f"获取匹配任务失败: {str(e)}")
            return None
    
    def list_matching_tasks(self, user_id: str, limit: int = 100, offset: int = 0) -> List[MatchingTask]:
        """
        列出用户匹配任务
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            匹配任务列表
        """
        try:
            db = next(get_db())
            tasks = db.query(MatchingTask).filter(
                MatchingTask.user_id == user_id
            ).offset(offset).limit(limit).all()
            return tasks
        except Exception as e:
            logger.error(f"列出匹配任务失败: {str(e)}")
            return []
    
    def get_matching_result(self, task_id: str) -> List[MatchedPoint]:
        """
        获取匹配结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            匹配点列表
        """
        try:
            db = next(get_db())
            matched_points = db.query(MatchedPoint).filter(
                MatchedPoint.matching_task_id == task_id
            ).all()
            return matched_points
        except Exception as e:
            logger.error(f"获取匹配结果失败: {str(e)}")
            return []
    
    def create_gps_point(self, trajectory_point: TrajectoryPoint) -> GeoPoint:
        """
        从轨迹点创建GPS点
        
        Args:
            trajectory_point: 轨迹点
            
        Returns:
            GPS点
        """
        return GeoPoint(
            latitude=trajectory_point.latitude,
            longitude=trajectory_point.longitude,
            timestamp=trajectory_point.timestamp,
            speed=trajectory_point.speed,
            direction=trajectory_point.direction,
            accuracy=trajectory_point.accuracy
        )
    
    def match_point(self, gps_point: GeoPoint) -> Dict[str, Any]:
        """
        匹配单个GPS点（示例实现）
        
        Args:
            gps_point: GPS点
            
        Returns:
            匹配结果
        """
        # 这里应该实现实际的地图匹配逻辑
        # 目前返回一个示例结果
        return {
            "matched_lat": gps_point.latitude,
            "matched_lon": gps_point.longitude,
            "distance": 0.0,
            "confidence": 1.0,
            "road_name": "示例道路",
            "road_type": "示例类型"
        }
    
    def get_available_algorithms(self) -> List[str]:
        """
        获取可用的匹配算法
        
        Returns:
            算法列表
        """
        return AlgorithmFactory.get_available_algorithms()
