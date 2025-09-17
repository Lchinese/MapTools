"""
地理计算工具模块
提供地理坐标计算、距离测量、投影转换等地理计算功能
"""

import math
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Point:
    """地理点数据结构"""
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    
    def __post_init__(self):
        """验证坐标范围"""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"纬度必须在-90到90之间，当前值: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"经度必须在-180到180之间，当前值: {self.longitude}")


@dataclass
class BoundingBox:
    """边界框数据结构"""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float
    
    def __post_init__(self):
        """验证边界框有效性"""
        if self.min_lat >= self.max_lat:
            raise ValueError("最小纬度必须小于最大纬度")
        if self.min_lng >= self.max_lng:
            raise ValueError("最小经度必须小于最大经度")
        if not -90 <= self.min_lat <= 90 or not -90 <= self.max_lat <= 90:
            raise ValueError("纬度必须在-90到90之间")
        if not -180 <= self.min_lng <= 180 or not -180 <= self.max_lng <= 180:
            raise ValueError("经度必须在-180到180之间")
    
    def contains(self, point: Point) -> bool:
        """检查点是否在边界框内"""
        return (self.min_lat <= point.latitude <= self.max_lat and
                self.min_lng <= point.longitude <= self.max_lng)
    
    def center(self) -> Point:
        """获取边界框中心点"""
        return Point(
            latitude=(self.min_lat + self.max_lat) / 2,
            longitude=(self.min_lng + self.max_lng) / 2
        )


class GeoUtils:
    """地理计算工具类"""
    
    # 地球半径（米）
    EARTH_RADIUS = 6371000
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用Haversine公式计算两点间的球面距离
        
        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度
            
        Returns:
            float: 距离（米）
        """
        # 将十进制度数转化为弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return c * GeoUtils.EARTH_RADIUS
    
    @staticmethod
    def point_to_line_distance(point_lat: float, point_lon: float,
                              line_start_lat: float, line_start_lon: float,
                              line_end_lat: float, line_end_lon: float) -> Tuple[float, float, float]:
        """
        计算点到线段的最短距离
        
        Args:
            point_lat, point_lon: 点的坐标
            line_start_lat, line_start_lon: 线段起点坐标
            line_end_lat, line_end_lon: 线段终点坐标
            
        Returns:
            Tuple[float, float, float]: (最短距离, 投影点纬度, 投影点经度)
        """
        # 计算向量
        AB_lat = line_end_lat - line_start_lat
        AB_lon = line_end_lon - line_start_lon
        AP_lat = point_lat - line_start_lat
        AP_lon = point_lon - line_start_lon
        
        # 计算投影参数t
        AB_dot_AB = AB_lat * AB_lat + AB_lon * AB_lon
        if AB_dot_AB == 0:
            # 线段退化为点
            distance = GeoUtils.haversine_distance(point_lat, point_lon, line_start_lat, line_start_lon)
            return distance, line_start_lat, line_start_lon
        
        AB_dot_AP = AB_lat * AP_lat + AB_lon * AP_lon
        t = max(0, min(1, AB_dot_AP / AB_dot_AB))
        
        # 计算投影点坐标
        proj_lat = line_start_lat + t * AB_lat
        proj_lon = line_start_lon + t * AB_lon
        
        # 计算距离
        distance = GeoUtils.haversine_distance(point_lat, point_lon, proj_lat, proj_lon)
        
        return distance, proj_lat, proj_lon
    
    @staticmethod
    def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间的方位角
        
        Args:
            lat1, lon1: 起点坐标
            lat2, lon2: 终点坐标
            
        Returns:
            float: 方位角（度，0-360）
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
        """
        计算两点的中点坐标
        
        Args:
            lat1, lon1: 第一个点坐标
            lat2, lon2: 第二个点坐标
            
        Returns:
            Tuple[float, float]: 中点坐标 (纬度, 经度)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        Bx = math.cos(lat2) * math.cos(dlon)
        By = math.cos(lat2) * math.sin(dlon)
        
        mid_lat = math.atan2(math.sin(lat1) + math.sin(lat2),
                            math.sqrt((math.cos(lat1) + Bx) ** 2 + By ** 2))
        mid_lon = lon1 + math.atan2(By, math.cos(lat1) + Bx)
        
        return math.degrees(mid_lat), math.degrees(mid_lon)
    
    @staticmethod
    def calculate_bounding_box(points: List[Point], buffer: float = 0.0) -> BoundingBox:
        """
        计算点集的边界框
        
        Args:
            points: 点列表
            buffer: 缓冲区大小（度）
            
        Returns:
            BoundingBox: 边界框
        """
        if not points:
            raise ValueError("点列表不能为空")
        
        lats = [p.latitude for p in points]
        lngs = [p.longitude for p in points]
        
        return BoundingBox(
            min_lat=min(lats) - buffer,
            max_lat=max(lats) + buffer,
            min_lng=min(lngs) - buffer,
            max_lng=max(lngs) + buffer
        )
    
    @staticmethod
    def calculate_trajectory_statistics(points: List[Point]) -> Dict[str, Any]:
        """
        计算轨迹统计信息
        
        Args:
            points: 轨迹点列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if len(points) < 2:
            return {
                "total_distance": 0.0,
                "total_points": len(points),
                "duration": 0,
                "avg_speed": 0.0,
                "max_speed": 0.0,
                "bounds": None
            }
        
        # 计算总距离
        total_distance = 0.0
        for i in range(1, len(points)):
            distance = GeoUtils.haversine_distance(
                points[i-1].latitude, points[i-1].longitude,
                points[i].latitude, points[i].longitude
            )
            total_distance += distance
        
        # 计算时间跨度
        duration = 0
        if hasattr(points[0], 'timestamp') and hasattr(points[-1], 'timestamp'):
            duration = int((points[-1].timestamp - points[0].timestamp).total_seconds())
        
        # 计算速度统计
        speeds = []
        for i in range(1, len(points)):
            if (hasattr(points[i-1], 'timestamp') and hasattr(points[i], 'timestamp') and
                hasattr(points[i-1], 'speed') and points[i-1].speed is not None):
                speeds.append(points[i-1].speed)
        
        avg_speed = np.mean(speeds) if speeds else 0.0
        max_speed = np.max(speeds) if speeds else 0.0
        
        # 计算边界框
        bounds = GeoUtils.calculate_bounding_box(points)
        
        return {
            "total_distance": total_distance,
            "total_points": len(points),
            "duration": duration,
            "avg_speed": avg_speed,
            "max_speed": max_speed,
            "bounds": bounds
        }
    
    @staticmethod
    def filter_points_by_speed(points: List[Point], max_speed: float = 200.0) -> List[Point]:
        """
        根据速度过滤轨迹点
        
        Args:
            points: 轨迹点列表
            max_speed: 最大合理速度（km/h）
            
        Returns:
            List[Point]: 过滤后的轨迹点列表
        """
        filtered_points = []
        for point in points:
            if hasattr(point, 'speed') and point.speed is not None:
                if point.speed <= max_speed:
                    filtered_points.append(point)
                else:
                    logger.warning(f"过滤掉异常速度点: {point.speed} km/h")
            else:
                filtered_points.append(point)
        
        return filtered_points
    
    @staticmethod
    def smooth_trajectory(points: List[Point], window_size: int = 3) -> List[Point]:
        """
        平滑轨迹（简单移动平均）
        
        Args:
            points: 轨迹点列表
            window_size: 窗口大小
            
        Returns:
            List[Point]: 平滑后的轨迹点列表
        """
        if len(points) < window_size:
            return points
        
        smoothed_points = []
        half_window = window_size // 2
        
        for i in range(len(points)):
            if i < half_window or i >= len(points) - half_window:
                # 边界点保持不变
                smoothed_points.append(points[i])
            else:
                # 计算窗口内点的平均值
                window_points = points[i-half_window:i+half_window+1]
                avg_lat = np.mean([p.latitude for p in window_points])
                avg_lon = np.mean([p.longitude for p in window_points])
                
                # 创建新的点
                smoothed_point = Point(
                    latitude=avg_lat,
                    longitude=avg_lon,
                    elevation=points[i].elevation
                )
                smoothed_points.append(smoothed_point)
        
        return smoothed_points
    
    @staticmethod
    def wgs84_to_web_mercator(lat: float, lon: float) -> Tuple[float, float]:
        """
        WGS84坐标转换为Web墨卡托投影
        
        Args:
            lat: 纬度
            lon: 经度
            
        Returns:
            Tuple[float, float]: Web墨卡托坐标 (x, y)
        """
        x = lon * 20037508.34 / 180
        y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180
        return x, y
    
    @staticmethod
    def web_mercator_to_wgs84(x: float, y: float) -> Tuple[float, float]:
        """
        Web墨卡托投影转换为WGS84坐标
        
        Args:
            x: Web墨卡托X坐标
            y: Web墨卡托Y坐标
            
        Returns:
            Tuple[float, float]: WGS84坐标 (纬度, 经度)
        """
        lon = x / 20037508.34 * 180
        lat = math.atan(math.sinh(y / 20037508.34 * math.pi)) * 180 / math.pi
        return lat, lon
    
    @staticmethod
    def is_point_in_bbox(point: Point, bbox: BoundingBox) -> bool:
        """
        判断点是否在边界框内
        
        Args:
            point: 待检测的点
            bbox: 边界框
            
        Returns:
            bool: 点是否在边界框内
        """
        return (bbox.min_lat <= point.latitude <= bbox.max_lat and 
                bbox.min_lng <= point.longitude <= bbox.max_lng)
    
    @staticmethod
    def calculate_polygon_area(points: List[Point]) -> float:
        """
        计算多边形面积（使用球面几何）
        
        Args:
            points: 多边形顶点列表
            
        Returns:
            float: 面积（平方米）
        """
        if len(points) < 3:
            return 0.0
        
        # 使用球面几何计算面积
        area = 0.0
        n = len(points)
        
        for i in range(n):
            j = (i + 1) % n
            lat1, lon1 = math.radians(points[i].latitude), math.radians(points[i].longitude)
            lat2, lon2 = math.radians(points[j].latitude), math.radians(points[j].longitude)
            
            area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
        
        area = abs(area) * GeoUtils.EARTH_RADIUS ** 2 / 2
        return area