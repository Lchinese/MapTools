"""
地理计算工具函数
提供各种地理空间计算功能
"""

import math
from typing import List, Tuple, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class Point:
    """地理点数据结构"""
    latitude: float
    longitude: float
    
    def __str__(self):
        return f"Point({self.latitude:.6f}, {self.longitude:.6f})"


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
            距离（米）
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
            (最短距离, 投影点纬度, 投影点经度)
        """
        # 将线段端点坐标
        A_lat, A_lon = line_start_lat, line_start_lon
        B_lat, B_lon = line_end_lat, line_end_lon
        P_lat, P_lon = point_lat, point_lon
        
        # 计算向量
        AB_lat = B_lat - A_lat
        AB_lon = B_lon - A_lon
        AP_lat = P_lat - A_lat
        AP_lon = P_lon - A_lon
        
        # 计算投影参数t
        AB_dot_AB = AB_lat * AB_lat + AB_lon * AB_lon
        if AB_dot_AB == 0:
            # 线段退化为点
            distance = GeoUtils.haversine_distance(P_lat, P_lon, A_lat, A_lon)
            return distance, A_lat, A_lon
        
        AB_dot_AP = AB_lat * AP_lat + AB_lon * AP_lon
        t = max(0, min(1, AB_dot_AP / AB_dot_AB))
        
        # 计算投影点坐标
        proj_lat = A_lat + t * AB_lat
        proj_lon = A_lon + t * AB_lon
        
        # 计算距离
        distance = GeoUtils.haversine_distance(P_lat, P_lon, proj_lat, proj_lon)
        
        return distance, proj_lat, proj_lon
    
    @staticmethod
    def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点间的方位角
        
        Args:
            lat1, lon1: 起点坐标
            lat2, lon2: 终点坐标
            
        Returns:
            方位角（度，0-360）
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
        计算两点的中点
        
        Args:
            lat1, lon1: 第一个点坐标
            lat2, lon2: 第二个点坐标
            
        Returns:
            (中点纬度, 中点经度)
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        Bx = math.cos(lat2) * math.cos(dlon)
        By = math.cos(lat2) * math.sin(dlon)
        
        lat3 = math.atan2(math.sin(lat1) + math.sin(lat2),
                         math.sqrt((math.cos(lat1) + Bx)**2 + By**2))
        lon3 = lon1 + math.atan2(By, math.cos(lat1) + Bx)
        
        return math.degrees(lat3), math.degrees(lon3)
    
    @staticmethod
    def is_point_in_bounds(point_lat: float, point_lon: float,
                          bounds: Dict[str, float]) -> bool:
        """
        检查点是否在边界框内
        
        Args:
            point_lat, point_lon: 点坐标
            bounds: 边界框 {"min_lat": float, "max_lat": float, "min_lon": float, "max_lon": float}
            
        Returns:
            是否在边界框内
        """
        return (bounds["min_lat"] <= point_lat <= bounds["max_lat"] and
                bounds["min_lon"] <= point_lon <= bounds["max_lon"])
    
    @staticmethod
    def calculate_bounds(points: List[Point], buffer: float = 0.001) -> Dict[str, float]:
        """
        计算点集的边界框
        
        Args:
            points: 点列表
            buffer: 缓冲区大小（度）
            
        Returns:
            边界框字典
        """
        if not points:
            return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}
        
        lats = [p.latitude for p in points]
        lons = [p.longitude for p in points]
        
        return {
            "min_lat": min(lats) - buffer,
            "max_lat": max(lats) + buffer,
            "min_lon": min(lons) - buffer,
            "max_lon": max(lons) + buffer
        }
    
    @staticmethod
    def filter_points_by_bounds(points: List[Point], bounds: Dict[str, float]) -> List[Point]:
        """
        根据边界框过滤点
        
        Args:
            points: 点列表
            bounds: 边界框
            
        Returns:
            过滤后的点列表
        """
        return [p for p in points if GeoUtils.is_point_in_bounds(p.latitude, p.longitude, bounds)]
    
    @staticmethod
    def calculate_speed(lat1: float, lon1: float, time1: float,
                       lat2: float, lon2: float, time2: float) -> float:
        """
        根据两个GPS点计算速度
        
        Args:
            lat1, lon1, time1: 第一个点的坐标和时间
            lat2, lon2, time2: 第二个点的坐标和时间
            
        Returns:
            速度（km/h）
        """
        if time2 <= time1:
            return 0
        
        distance = GeoUtils.haversine_distance(lat1, lon1, lat2, lon2)  # 米
        time_diff = time2 - time1  # 秒
        
        speed_ms = distance / time_diff  # 米/秒
        speed_kmh = speed_ms * 3.6  # 公里/小时
        
        return speed_kmh
    
    @staticmethod
    def smooth_trajectory(points: List[Point], window_size: int = 3) -> List[Point]:
        """
        对轨迹进行平滑处理（简单移动平均）
        
        Args:
            points: 原始点列表
            window_size: 窗口大小
            
        Returns:
            平滑后的点列表
        """
        if len(points) < window_size:
            return points
        
        smoothed = []
        for i in range(len(points)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(points), i + window_size // 2 + 1)
            
            window_points = points[start_idx:end_idx]
            avg_lat = sum(p.latitude for p in window_points) / len(window_points)
            avg_lon = sum(p.longitude for p in window_points) / len(window_points)
            
            smoothed.append(Point(avg_lat, avg_lon))
        
        return smoothed
    
    @staticmethod
    def remove_outliers(points: List[Point], max_speed: float = 200) -> List[Point]:
        """
        移除异常点（基于速度）
        
        Args:
            points: 点列表
            max_speed: 最大合理速度（km/h）
            
        Returns:
            移除异常点后的点列表
        """
        if len(points) < 2:
            return points
        
        filtered = [points[0]]  # 保留第一个点
        
        for i in range(1, len(points)):
            prev_point = filtered[-1]
            curr_point = points[i]
            
            # 计算速度（假设时间间隔为1秒，实际应用中需要真实时间戳）
            speed = GeoUtils.calculate_speed(
                prev_point.latitude, prev_point.longitude, i-1,
                curr_point.latitude, curr_point.longitude, i
            )
            
            if speed <= max_speed:
                filtered.append(curr_point)
            else:
                print(f"移除异常点: 速度 {speed:.2f} km/h")
        
        return filtered