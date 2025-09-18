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
        # 从天地图WFS服务加载真实道路数据
        try:
            self.roads = self._load_osm_roads()
            logger.info(f"成功加载 {len(self.roads)} 条天地图道路")
        except Exception as e:
            logger.error(f"加载天地图WFS道路失败: {e}")
            # 如果天地图WFS失败，尝试OpenStreetMap作为备选
            try:
                self.roads = self._load_osm_fallback("113.812401,22.503099,114.269966,22.748068")
                logger.info(f"使用OpenStreetMap备选方案，加载了 {len(self.roads)} 条道路")
            except Exception as fallback_error:
                logger.error(f"OpenStreetMap备选方案也失败: {fallback_error}")
                # 如果都失败，使用空的道路网络
                self.roads = []
                logger.warning("无法加载任何道路数据，使用空道路网络")
    
    
    def _load_osm_roads(self) -> List[Dict[str, Any]]:
        """从天地图WFS服务加载深圳地区的道路数据"""
        # 深圳边界框 (基于GPS数据范围)
        bbox = "113.812401,22.503099,114.269966,22.748068"
        
        # 天地图WFS服务URL
        wfs_url = "http://gisserver.tianditu.gov.cn/TDTService/wfs"
        
        # WFS GetFeature请求参数 - 尝试多个可能的道路图层
        road_layers = ['TDTService:LRDL', 'TDTService:LRRL', 'TDTService:AANP']
        
        for layer_name in road_layers:
            try:
                params = {
                    'service': 'WFS',
                    'version': '1.1.0',
                    'request': 'GetFeature',
                    'typeName': layer_name,
                    'outputFormat': 'application/json',
                    'srsName': 'EPSG:4326',
                    'bbox': f'{bbox},EPSG:4326'
                }
                
                logger.info(f"尝试获取图层: {layer_name}")
                response = requests.get(wfs_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                roads = []
                
                # 解析WFS返回的GeoJSON数据
                for feature in data.get('features', []):
                    geometry = feature.get('geometry', {})
                    properties = feature.get('properties', {})
                    
                    if geometry.get('type') in ['LineString', 'MultiLineString']:
                        coordinates = geometry.get('coordinates', [])
                        
                        # 处理MultiLineString
                        if geometry.get('type') == 'MultiLineString':
                            for line_coords in coordinates:
                                if len(line_coords) >= 2:
                                    points = [(coord[0], coord[1]) for coord in line_coords]
                                    road_name = properties.get('NAME', f'未命名道路_{feature.get("id", "unknown")}')
                                    road_type = properties.get('TYPE', layer_name.split(':')[1])
                                    
                                    roads.append({
                                        'id': f'tdt_{layer_name}_{feature.get("id", "unknown")}_{len(roads)}',
                                        'name': road_name,
                                        'type': road_type,
                                        'points': points
                                    })
                        else:
                            # 处理LineString
                            if len(coordinates) >= 2:
                                points = [(coord[0], coord[1]) for coord in coordinates]
                                road_name = properties.get('NAME', f'未命名道路_{feature.get("id", "unknown")}')
                                road_type = properties.get('TYPE', layer_name.split(':')[1])
                                
                                roads.append({
                                    'id': f'tdt_{layer_name}_{feature.get("id", "unknown")}',
                                    'name': road_name,
                                    'type': road_type,
                                    'points': points
                                })
                
                if roads:
                    logger.info(f"从天地图WFS图层 {layer_name} 加载了 {len(roads)} 条道路")
                    return roads
                else:
                    logger.warning(f"图层 {layer_name} 没有返回道路数据")
                    
            except Exception as e:
                logger.warning(f"获取图层 {layer_name} 失败: {e}")
                continue
        
        # 如果所有图层都失败，抛出异常
        raise Exception("所有天地图WFS图层都无法获取道路数据")
    
    def _load_osm_fallback(self, bbox: str) -> List[Dict[str, Any]]:
        """备选方案：从OpenStreetMap加载道路数据"""
        overpass_query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified)$"]({bbox});
        );
        out geom;
        """
        
        try:
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
                    tags = element.get('tags', {})
                    highway_type = tags.get('highway', 'unknown')
                    name = tags.get('name', f'未命名道路_{element["id"]}')
                    
                    points = []
                    for node in element['geometry']:
                        points.append((node['lon'], node['lat']))
                    
                    if len(points) >= 2:
                        roads.append({
                            'id': f'osm_way_{element["id"]}',
                            'name': name,
                            'type': highway_type,
                            'points': points
                        })
            
            logger.info(f"从OSM备选方案加载了 {len(roads)} 条道路")
            return roads
            
        except Exception as e:
            logger.error(f"OSM备选方案也失败: {e}")
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
        
        # 如果没找到，使用第一个道路的第一个点作为默认点
        if self.roads and len(self.roads) > 0:
            default_road = self.roads[0]
            default_point = self.roads[0]['points'][0] if self.roads[0]['points'] else (114.0, 22.5)
        else:
            # 如果没有任何道路数据，使用深圳中心点
            default_road = {'id': 'default', 'name': '默认点', 'type': 'unknown', 'points': []}
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
