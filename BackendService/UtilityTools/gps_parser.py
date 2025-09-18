"""
GPS数据解析工具
解析sample-utf.txt中的出租车GPS数据
"""

import csv
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GPSDataParser:
    """GPS数据解析器"""
    
    def __init__(self):
        # 从BackendService目录向上两级到项目根目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    def parse_sample_data(self, filename: str = "sample-utf.txt") -> List[Dict[str, Any]]:
        """
        解析sample-utf.txt文件
        
        字段格式：日期(YYYYMMDD), 时间(HHMMSS), 记录类型, 车牌号, 经度(lon), 纬度(lat), 速度(km/h), 航向(度), 保留字段1, 定位标志
        
        Returns:
            List[Dict]: 解析后的GPS点列表
        """
        file_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []
        
        gps_points = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:  # 跳过空行
                        continue
                    
                    try:
                        # 按逗号分割
                        parts = line.split(',')
                        if len(parts) != 10:
                            logger.warning(f"第{line_num}行数据格式不正确，跳过: {line}")
                            continue
                        
                        # 解析各字段
                        date_str = parts[0].strip()
                        time_str = parts[1].strip()
                        record_type = parts[2].strip()
                        plate_number = parts[3].strip()
                        longitude = float(parts[4].strip())
                        latitude = float(parts[5].strip())
                        speed = float(parts[6].strip())
                        heading = float(parts[7].strip())
                        reserved_field = parts[8].strip()
                        location_flag = int(parts[9].strip())
                        
                        # 构建时间戳
                        try:
                            # 处理时间格式，如 235926 或 1
                            if len(time_str) == 6:
                                time_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                            else:
                                # 处理单数字时间，如 "1" 表示 00:00:01
                                time_obj = datetime.strptime(f"{date_str}00000{time_str}", "%Y%m%d%H%M%S")
                        except ValueError:
                            logger.warning(f"第{line_num}行时间格式错误，跳过: {line}")
                            continue
                        
                        gps_point = {
                            'id': line_num,
                            'date': date_str,
                            'time': time_str,
                            'datetime': time_obj.isoformat(),
                            'record_type': record_type,
                            'plate_number': plate_number,
                            'longitude': longitude,
                            'latitude': latitude,
                            'speed': speed,
                            'heading': heading,
                            'reserved_field': reserved_field,
                            'location_flag': location_flag,
                            'is_valid': location_flag == 1  # 定位标志为1表示有效定位
                        }
                        
                        gps_points.append(gps_point)
                        
                    except (ValueError, IndexError) as e:
                        logger.warning(f"第{line_num}行数据解析错误: {e}, 跳过: {line}")
                        continue
            
            logger.info(f"成功解析 {len(gps_points)} 个GPS点")
            return gps_points
            
        except Exception as e:
            logger.error(f"解析文件时出错: {e}")
            return []
    
    def filter_valid_points(self, gps_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤有效的GPS点"""
        valid_points = [point for point in gps_points if point.get('is_valid', False)]
        logger.info(f"过滤后有效GPS点数量: {len(valid_points)}")
        return valid_points
    
    def group_by_vehicle(self, gps_points: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按车牌号分组GPS点"""
        vehicles = {}
        for point in gps_points:
            plate_number = point['plate_number']
            if plate_number not in vehicles:
                vehicles[plate_number] = []
            vehicles[plate_number].append(point)
        
        # 按时间排序每个车辆的轨迹点
        for plate_number in vehicles:
            vehicles[plate_number].sort(key=lambda x: x['datetime'])
        
        logger.info(f"按车辆分组，共 {len(vehicles)} 辆车")
        return vehicles

# 测试函数
def test_parser():
    """测试解析器"""
    parser = GPSDataParser()
    gps_points = parser.parse_sample_data()
    
    if gps_points:
        print(f"解析到 {len(gps_points)} 个GPS点")
        print("前3个点示例:")
        for i, point in enumerate(gps_points[:3]):
            print(f"  {i+1}. {point['plate_number']} - ({point['longitude']}, {point['latitude']}) - {point['datetime']}")
        
        # 按车辆分组
        vehicles = parser.group_by_vehicle(gps_points)
        print(f"\n按车辆分组，共 {len(vehicles)} 辆车")
        for plate_number, points in list(vehicles.items())[:3]:
            print(f"  {plate_number}: {len(points)} 个点")

if __name__ == "__main__":
    test_parser()
