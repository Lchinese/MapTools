"""
数据验证工具模块
提供数据验证、格式检查等功能
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """验证地理坐标"""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    @staticmethod
    def validate_speed(speed: float, max_speed: float = 200.0) -> bool:
        """验证速度值"""
        return 0 <= speed <= max_speed
    
    @staticmethod
    def validate_direction(direction: float) -> bool:
        """验证方向角"""
        return 0 <= direction <= 360
    
    @staticmethod
    def validate_timestamp(timestamp: Union[datetime, str]) -> bool:
        """验证时间戳"""
        try:
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """验证文件扩展名"""
        if not filename:
            return False
        
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return f".{file_ext}" in [ext.lower() for ext in allowed_extensions]
