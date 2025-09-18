"""
道路匹配工具
将GPS点匹配到最近的道路上
"""

import math
import requests
import json
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class RoadMatcher:
    """道路匹配器"""
    
    def __init__(self):
        # 尝试从OpenStreetMap加载真实道路数据，如果失败则使用模拟数据
        try:
            self.roads = self._load_osm_roads()
            logger.info(f"成功加载 {len(self.roads)} 条OSM道路")
        except Exception as e:
            logger.warning(f"加载OSM道路失败: {e}，使用模拟道路网络")
            self.roads = self._create_simple_road_network()
    
    def _create_simple_road_network(self) -> List[Dict[str, Any]]:
        """创建基于GPS数据分布的动态道路网络"""
        # 基于GPS数据实际范围创建道路网络
        # GPS范围: 纬度 22.503099-22.748068, 经度 113.812401-114.269966
        
        roads = []
        
        # 创建网格状道路网络，覆盖GPS数据分布区域
        lat_min, lat_max = 22.50, 22.75
        lon_min, lon_max = 113.80, 114.27
        
        # 东西向道路（纬度固定，经度变化）
        for i, lat in enumerate([22.52, 22.55, 22.58, 22.61, 22.64, 22.67, 22.70, 22.73]):
            road_id = f'road_ew_{i+1:02d}'
            road_name = f'东西向道路{i+1}'
            
            # 创建经度点，覆盖GPS数据范围
            points = []
            for lon in [113.85, 113.90, 113.95, 114.00, 114.05, 114.10, 114.15, 114.20, 114.25]:
                points.append((lon, lat))
            
            roads.append({
                'id': road_id,
                'name': road_name,
                'type': 'highway' if i in [2, 4] else 'arterial',
                'points': points
            })
        
        # 南北向道路（经度固定，纬度变化）
        for i, lon in enumerate([113.85, 113.90, 113.95, 114.00, 114.05, 114.10, 114.15, 114.20, 114.25]):
            road_id = f'road_ns_{i+1:02d}'
            road_name = f'南北向道路{i+1}'
            
            # 创建纬度点，覆盖GPS数据范围
            points = []
            for lat in [22.52, 22.55, 22.58, 22.61, 22.64, 22.67, 22.70, 22.73]:
                points.append((lon, lat))
            
            roads.append({
                'id': road_id,
                'name': road_name,
                'type': 'highway' if i in [3, 5] else 'arterial',
                'points': points
            })
        
        # 添加一些对角线道路
        roads.append({
            'id': 'road_diag_01',
            'name': '对角线道路1',
            'type': 'arterial',
            'points': [
                (113.85, 22.52), (113.90, 22.55), (113.95, 22.58), (114.00, 22.61), (114.05, 22.64), (114.10, 22.67)
            ]
        })
        
        roads.append({
            'id': 'road_diag_02',
            'name': '对角线道路2',
            'type': 'arterial',
            'points': [
                (114.00, 22.52), (114.05, 22.55), (114.10, 22.58), (114.15, 22.61), (114.20, 22.64), (114.25, 22.67)
            ]
        })
        
        return roads
    
    def _load_osm_roads(self) -> List[Dict[str, Any]]:
        """从OpenStreetMap加载深圳地区的道路数据"""
        # 深圳边界框 (基于GPS数据范围)
        bbox = "113.812401,22.503099,114.269966,22.748068"
        
        # Overpass API查询语句 - 获取主要道路
        overpass_query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]({bbox});
        );
        out geom;
        """
        
        try:
            # 调用Overpass API
            response = requests.post(
                "https://overpass-api.de/api/interpreter",
                data=overpass_query,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            roads = []
            
            for element in data.get('elements', []):
                if element['type'] == 'way' and 'geometry' in element:
                    # 提取道路信息
                    tags = element.get('tags', {})
                    highway_type = tags.get('highway', 'unknown')
                    name = tags.get('name', f'未命名道路_{element["id"]}')
                    
                    # 转换坐标格式 (lon, lat)
                    points = []
                    for node in element['geometry']:
                        points.append((node['lon'], node['lat']))
                    
                    if len(points) >= 2:  # 至少需要两个点才能形成道路
                        roads.append({
                            'id': f'osm_way_{element["id"]}',
                            'name': name,
                            'type': highway_type,
                            'points': points
                        })
            
            logger.info(f"从OSM加载了 {len(roads)} 条道路")
            return roads
            
        except Exception as e:
            logger.error(f"从OSM加载道路数据失败: {e}")
            raise e
    
    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """计算两点间距离（米）"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # 使用Haversine公式计算球面距离
        R = 6371000  # 地球半径（米）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def point_to_line_distance(self, point: Tuple[float, float], line_start: Tuple[float, float], line_end: Tuple[float, float]) -> Tuple[float, Tuple[float, float]]:
        """计算点到线段的距离和最近点"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # 计算线段长度的平方
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_length_sq == 0:
            # 线段退化为点
            distance = self.calculate_distance(point, line_start)
            return distance, line_start
        
        # 计算投影参数t
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
        
        # 计算最近点
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        closest_point = (closest_x, closest_y)
        
        # 计算距离
        distance = self.calculate_distance(point, closest_point)
        
        return distance, closest_point
    
    def find_closest_road_point(self, gps_point: Tuple[float, float]) -> Dict[str, Any]:
        """找到GPS点最近的道路点（简化算法）"""
        gps_lat, gps_lon = gps_point
        min_distance = float('inf')
        closest_road = None
        closest_point = None
        
        # 遍历所有道路，找到最近的道路点
        for road in self.roads:
            road_points = road['points']
            
            # 检查每个道路点
            for point in road_points:
                point_lat, point_lon = point
                distance = self.calculate_distance(gps_point, point)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_road = road
                    closest_point = point
        
        # 如果找到了合适的匹配点，返回结果
        if closest_road and closest_point:
            return {
                'road': closest_road,
                'matched_point': closest_point,
                'distance': min_distance,
                'segment': None
            }
        
        # 如果没找到，使用默认点（深南大道中心）
        default_road = self.roads[0]
        default_point = (114.0, 22.5)
        return {
            'road': default_road,
            'matched_point': default_point,
            'distance': self.calculate_distance(gps_point, default_point),
            'segment': None
        }
    
    def match_gps_to_roads(self, gps_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将GPS点匹配到道路"""
        matched_points = []
        
        for gps_point in gps_points:
            gps_coord = (gps_point['longitude'], gps_point['latitude'])
            match_result = self.find_closest_road_point(gps_coord)
            
            matched_point = {
                'original_gps': gps_point,
                'matched_longitude': match_result['matched_point'][0],
                'matched_latitude': match_result['matched_point'][1],
                'road_id': match_result['road']['id'],
                'road_name': match_result['road']['name'],
                'road_type': match_result['road']['type'],
                'distance_to_road': match_result['distance'],
                'segment': match_result['segment']
            }
            
            matched_points.append(matched_point)
        
        logger.info(f"完成 {len(matched_points)} 个GPS点的道路匹配")
        return matched_points

# 测试函数
def test_road_matcher():
    """测试道路匹配器"""
    from gps_parser import GPSDataParser
    
    # 解析GPS数据
    parser = GPSDataParser()
    gps_points = parser.parse_sample_data()
    
    if not gps_points:
        print("没有GPS数据可测试")
        return
    
    # 取前10个点进行测试
    test_points = gps_points[:10]
    
    # 进行道路匹配
    matcher = RoadMatcher()
    matched_points = matcher.match_gps_to_roads(test_points)
    
    print(f"测试 {len(test_points)} 个GPS点的道路匹配:")
    for i, point in enumerate(matched_points):
        original = point['original_gps']
        print(f"  {i+1}. {original['plate_number']} - 原始: ({original['longitude']:.6f}, {original['latitude']:.6f})")
        print(f"      匹配到: {point['road_name']} - ({point['matched_longitude']:.6f}, {point['matched_latitude']:.6f})")
        print(f"      距离: {point['distance_to_road']:.2f}米")

if __name__ == "__main__":
    test_road_matcher()
