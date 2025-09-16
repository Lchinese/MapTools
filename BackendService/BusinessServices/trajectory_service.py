"""
轨迹业务服务
提供轨迹相关的业务逻辑处理
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
import logging

from ..DataModels.Models.trajectory import Trajectory, TrajectoryPoint, MatchingTask
from ..DataSchemas.trajectory import (
    TrajectoryCreate, TrajectoryUpdate, TrajectoryResponse, 
    TrajectoryListResponse, TrajectoryQueryParams, TrajectoryStatus
)
from ..UtilityTools.file_utils import TrajectoryFileProcessor
from ..UtilityTools.geo_utils import GeoUtils
from ..CoreConfig.logging import log_performance, log_audit

logger = logging.getLogger(__name__)


class TrajectoryService:
    """轨迹业务服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_processor = TrajectoryFileProcessor()
    
    @log_performance
    @log_audit("创建轨迹")
    def create_trajectory(self, trajectory_data: TrajectoryCreate, 
                         file_path: str, points: List[Dict[str, Any]]) -> TrajectoryResponse:
        """创建轨迹"""
        try:
            # 计算轨迹统计信息
            statistics = self._calculate_trajectory_statistics(points)
            
            # 创建轨迹记录
            trajectory = Trajectory(
                name=trajectory_data.name,
                description=trajectory_data.description,
                filename=trajectory_data.filename,
                file_size=trajectory_data.file_size,
                file_type=trajectory_data.file_type,
                data_source=trajectory_data.data_source,
                data_category=trajectory_data.data_category,
                vehicle_id=trajectory_data.vehicle_id,
                passenger_id=trajectory_data.passenger_id,
                point_count=statistics['total_points'],
                total_distance=statistics['total_distance'],
                duration=statistics['duration'],
                bounds_min_lat=statistics['bounds'].min_lat if statistics['bounds'] else None,
                bounds_max_lat=statistics['bounds'].max_lat if statistics['bounds'] else None,
                bounds_min_lng=statistics['bounds'].min_lng if statistics['bounds'] else None,
                bounds_max_lng=statistics['bounds'].max_lng if statistics['bounds'] else None,
                status=TrajectoryStatus.UPLOADED
            )
            
            self.db.add(trajectory)
            self.db.flush()  # 获取ID
            
            # 创建轨迹点记录
            trajectory_points = []
            for point_data in points:
                point = TrajectoryPoint(
                    trajectory_id=trajectory.id,
                    latitude=point_data['latitude'],
                    longitude=point_data['longitude'],
                    timestamp=point_data['timestamp'],
                    elevation=point_data.get('elevation'),
                    speed=point_data.get('speed'),
                    direction=point_data.get('direction'),
                    accuracy=point_data.get('accuracy'),
                    raw_data=point_data.get('raw_data')
                )
                trajectory_points.append(point)
            
            self.db.add_all(trajectory_points)
            self.db.commit()
            
            logger.info(f"轨迹创建成功: ID={trajectory.id}, 点数={len(points)}")
            
            return TrajectoryResponse.model_validate(trajectory)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建轨迹失败: {e}")
            raise
    
    @log_performance
    def get_trajectory(self, trajectory_id: int) -> Optional[TrajectoryResponse]:
        """获取轨迹详情"""
        trajectory = self.db.query(Trajectory).filter(
            Trajectory.id == trajectory_id,
            Trajectory.is_deleted == False
        ).first()
        
        if not trajectory:
            return None
        
        return TrajectoryResponse.model_validate(trajectory)
    
    @log_performance
    def get_trajectory_list(self, query_params: TrajectoryQueryParams) -> TrajectoryListResponse:
        """获取轨迹列表"""
        query = self.db.query(Trajectory).filter(Trajectory.is_deleted == False)
        
        # 应用过滤条件
        if query_params.status:
            query = query.filter(Trajectory.status == query_params.status)
        
        if query_params.data_source:
            query = query.filter(Trajectory.data_source == query_params.data_source)
        
        if query_params.vehicle_id:
            query = query.filter(Trajectory.vehicle_id == query_params.vehicle_id)
        
        if query_params.start_date:
            query = query.filter(Trajectory.created_at >= query_params.start_date)
        
        if query_params.end_date:
            query = query.filter(Trajectory.created_at <= query_params.end_date)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        offset = (query_params.page - 1) * query_params.limit
        trajectories = query.order_by(desc(Trajectory.created_at)).offset(offset).limit(query_params.limit).all()
        
        # 计算总页数
        pages = (total + query_params.limit - 1) // query_params.limit
        
        return TrajectoryListResponse(
            trajectories=[TrajectoryResponse.model_validate(t) for t in trajectories],
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            pages=pages
        )
    
    def _calculate_trajectory_statistics(self, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算轨迹统计信息"""
        if not points:
            return {
                'total_points': 0,
                'total_distance': 0.0,
                'duration': 0,
                'bounds': None
            }
        
        # 转换为Point对象
        point_objects = []
        for point_data in points:
            point_objects.append(GeoUtils.Point(
                latitude=point_data['latitude'],
                longitude=point_data['longitude'],
                elevation=point_data.get('elevation')
            ))
        
        # 计算统计信息
        statistics = GeoUtils.calculate_trajectory_statistics(point_objects)
        
        return statistics
