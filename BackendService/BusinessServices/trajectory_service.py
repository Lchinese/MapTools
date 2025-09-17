"""
轨迹业务逻辑服务
处理轨迹相关的业务逻辑
"""

import sys
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DataModels.Models.trajectory import Trajectory, TrajectoryPoint, MatchingTask
from UtilityTools.file_utils import TrajectoryFileProcessor
from UtilityTools.geo_utils import GeoUtils
from CoreConfig.database import get_db
from CoreConfig.logging import get_logger

logger = get_logger(__name__)


class TrajectoryService:
    """轨迹服务类"""
    
    def __init__(self):
        """初始化轨迹服务"""
        pass
    
    def create_trajectory(self, user_id: str, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        创建轨迹
        
        Args:
            user_id: 用户ID
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            轨迹信息字典
        """
        try:
            # 解析轨迹文件
            processor = TrajectoryFileProcessor()
            trajectory_data = processor.parse_file(file_path, file_type)
            
            # 创建轨迹对象
            trajectory = Trajectory(
                trajectory_id=str(uuid.uuid4()),
                user_id=user_id,
                name=os.path.basename(file_path),
                filename=os.path.basename(file_path),
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type=file_type,
                data_source="auto",
                data_category="continuous_trajectory"
            )
            
            # 计算轨迹统计信息
            stats = GeoUtils.calculate_trajectory_statistics(trajectory_data["points"])
            trajectory.point_count = stats["total_points"]
            trajectory.total_distance = stats["total_distance"]
            trajectory.duration = stats["duration"]
            
            # 计算边界框
            bounds = stats["bounds"]
            if bounds:
                trajectory.bounds_min_lat = bounds.min_lat
                trajectory.bounds_max_lat = bounds.max_lat
                trajectory.bounds_min_lng = bounds.min_lng
                trajectory.bounds_max_lng = bounds.max_lng
            
            # 保存轨迹到数据库
            db = next(get_db())
            db.add(trajectory)
            
            # 创建轨迹点
            points = []
            for i, point_data in enumerate(trajectory_data["points"]):
                point = TrajectoryPoint(
                    point_id=str(uuid.uuid4()),
                    trajectory_id=trajectory.id,
                    sequence_number=i+1,
                    latitude=point_data.latitude,
                    longitude=point_data.longitude,
                    elevation=point_data.elevation,
                    timestamp=point_data.timestamp,
                    speed=point_data.speed,
                    direction=point_data.direction,
                    accuracy=point_data.accuracy
                )
                points.append(point)
            
            db.add_all(points)
            db.commit()
            db.refresh(trajectory)
            
            return {
                "success": True,
                "trajectory_id": trajectory.trajectory_id,
                "message": "轨迹创建成功"
            }
            
        except Exception as e:
            logger.error(f"创建轨迹失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        """
        获取轨迹
        
        Args:
            trajectory_id: 轨迹ID
            
        Returns:
            轨迹对象，如果未找到则返回None
        """
        try:
            db = next(get_db())
            trajectory = db.query(Trajectory).filter(
                Trajectory.trajectory_id == trajectory_id
            ).first()
            return trajectory
        except Exception as e:
            logger.error(f"获取轨迹失败: {str(e)}")
            return None
    
    def list_trajectories(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Trajectory]:
        """
        列出用户轨迹
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            轨迹列表
        """
        try:
            db = next(get_db())
            trajectories = db.query(Trajectory).filter(
                Trajectory.user_id == user_id
            ).offset(offset).limit(limit).all()
            return trajectories
        except Exception as e:
            logger.error(f"列出轨迹失败: {str(e)}")
            return []
    
    def delete_trajectory(self, trajectory_id: str) -> Dict[str, Any]:
        """
        删除轨迹
        
        Args:
            trajectory_id: 轨迹ID
            
        Returns:
            删除结果
        """
        try:
            db = next(get_db())
            trajectory = db.query(Trajectory).filter(
                Trajectory.trajectory_id == trajectory_id
            ).first()
            
            if not trajectory:
                return {
                    "success": False,
                    "error": "轨迹不存在"
                }
            
            db.delete(trajectory)
            db.commit()
            
            return {
                "success": True,
                "message": "轨迹删除成功"
            }
        except Exception as e:
            logger.error(f"删除轨迹失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }