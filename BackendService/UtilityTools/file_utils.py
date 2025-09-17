"""
文件处理工具模块
提供文件上传、解析、格式转换等功能
"""

import os
import sys
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import logging
import gpxpy
import gpxpy.gpx
import csv
import json
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径，解决相对导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CoreConfig.settings import get_settings
from DataSchemas.trajectory import DataSource, DataCategory, TrajectoryPointCreate
from UtilityTools.geo_utils import GeoUtils, Point

logger = logging.getLogger(__name__)
settings = get_settings()


class FileProcessor:
    """文件处理器基类"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    def generate_file_id(self) -> str:
        """生成唯一文件ID"""
        return str(uuid.uuid4())
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息"""
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "filename": file_path.name,
            "file_size": stat.st_size,
            "mime_type": mime_type,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "hash": self.calculate_file_hash(file_path)
        }
    
    def validate_file(self, file_path: Path, max_size: int = None) -> bool:
        """验证文件"""
        if not file_path.exists():
            return False
        
        if max_size and file_path.stat().st_size > max_size:
            logger.warning(f"文件过大: {file_path.name}, 大小: {file_path.stat().st_size}")
            return False
        
        return True


class TrajectoryFileProcessor(FileProcessor):
    """轨迹文件处理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = settings.ALLOWED_EXTENSIONS
    
    def detect_data_format(self, file_path: Path) -> DataSource:
        """自动检测数据格式"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
            
            # 出租车GPS数据：10个逗号分隔字段
            if ',' in first_line and len(first_line.split(',')) == 10:
                return DataSource.TAXI_GPS
            
            # 公交刷卡数据：空格分隔，包含ISO时间格式
            elif ' ' in first_line and 'T' in first_line:
                return DataSource.BUS_CARD
            
            # 地铁刷卡数据：逗号分隔，包含21或22交易类型
            elif ',' in first_line and ('21' in first_line or '22' in first_line):
                return DataSource.METRO_CARD
            
            # 公交GPS运行数据：多个逗号分隔字段，包含线路信息
            elif ',' in first_line and len(first_line.split(',')) > 15:
                return DataSource.BUS_GPS
            
            # 出租车交易数据：多个逗号分隔字段，包含时间范围
            elif ',' in first_line and len(first_line.split(',')) == 11:
                return DataSource.TAXI_TRANSACTION
            
            # GPX格式
            elif first_line.startswith('<?xml'):
                return DataSource.GPX
            
            # 其他CSV格式
            else:
                return DataSource.CSV
                
        except Exception as e:
            logger.error(f"检测数据格式失败: {e}")
            return DataSource.AUTO
    
    def get_data_category(self, data_source: DataSource) -> DataCategory:
        """根据数据源获取数据类别"""
        category_mapping = {
            DataSource.TAXI_GPS: DataCategory.CONTINUOUS_TRAJECTORY,
            DataSource.BUS_GPS: DataCategory.CONTINUOUS_TRAJECTORY,
            DataSource.GPX: DataCategory.CONTINUOUS_TRAJECTORY,
            DataSource.CSV: DataCategory.CONTINUOUS_TRAJECTORY,
            DataSource.BUS_CARD: DataCategory.ORIGIN_DESTINATION,
            DataSource.METRO_CARD: DataCategory.ORIGIN_DESTINATION,
            DataSource.TAXI_TRANSACTION: DataCategory.TIME_RANGE,
        }
        return category_mapping.get(data_source, DataCategory.CONTINUOUS_TRAJECTORY)
    
    def parse_gpx_file(self, file_path: Path) -> List[TrajectoryPointCreate]:
        """解析GPX文件"""
        points = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                gpx = gpxpy.parse(f)
            
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.latitude and point.longitude:
                            points.append(TrajectoryPointCreate(
                                latitude=point.latitude,
                                longitude=point.longitude,
                                timestamp=point.time or datetime.now(),
                                elevation=point.elevation,
                                speed=getattr(point, 'speed', None),
                                direction=getattr(point, 'course', None),
                                accuracy=getattr(point, 'horizontal_dilution', None)
                            ))
        except Exception as e:
            logger.error(f"解析GPX文件失败: {e}")
            raise
        
        return points
    
    def parse_taxi_gps_file(self, file_path: Path) -> List[TrajectoryPointCreate]:
        """解析出租车GPS文件"""
        points = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 10:
                        try:
                            # 解析日期时间
                            date_str = row[0]
                            time_str = row[1]
                            datetime_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                            timestamp = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                            
                            # 解析坐标
                            latitude = float(row[4])
                            longitude = float(row[5])
                            speed = float(row[6]) if row[6] else None
                            direction = float(row[7]) if row[7] else None
                            
                            points.append(TrajectoryPointCreate(
                                latitude=latitude,
                                longitude=longitude,
                                timestamp=timestamp,
                                speed=speed,
                                direction=direction,
                                accuracy=None
                            ))
                        except (ValueError, IndexError) as e:
                            logger.warning(f"跳过无效行: {row}, 错误: {e}")
                            continue
        except Exception as e:
            logger.error(f"解析出租车GPS文件失败: {e}")
            raise
        
        return points
    
    def parse_file(self, file_path: Path, data_source: DataSource = None) -> Tuple[List[TrajectoryPointCreate], DataSource, DataCategory]:
        """解析轨迹文件"""
        if not self.validate_file(file_path, settings.MAX_FILE_SIZE):
            raise ValueError("文件验证失败")
        
        # 自动检测数据格式
        if data_source is None:
            data_source = self.detect_data_format(file_path)
        
        data_category = self.get_data_category(data_source)
        
        # 根据数据源类型解析文件
        if data_source == DataSource.GPX:
            points = self.parse_gpx_file(file_path)
        elif data_source == DataSource.TAXI_GPS:
            points = self.parse_taxi_gps_file(file_path)
        else:
            # 对于其他格式，返回空列表
            points = []
        
        logger.info(f"解析文件 {file_path.name} 完成，数据源: {data_source}, 类别: {data_category}, 点数: {len(points)}")
        
        return points, data_source, data_category
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Path:
        """保存上传的文件"""
        file_id = self.generate_file_id()
        file_path = self.upload_dir / f"{file_id}_{filename}"
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"文件已保存: {file_path}")
        return file_path
    
    def cleanup_file(self, file_path: Path) -> bool:
        """清理文件"""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件已删除: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False




