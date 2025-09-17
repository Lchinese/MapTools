"""
配置管理模块
提供系统配置的统一管理
"""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """系统配置类"""
    
    # 应用基础配置
    APP_NAME: str = "MapTools Backend Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/maptools"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # 天地图API配置
    TIANDITU_API_KEY: Optional[str] = None
    TIANDITU_WGS84_URL: str = "http://t0.tianditu.gov.cn/vec_c/wmts"
    TIANDITU_WEB_MERCATOR_URL: str = "http://t0.tianditu.gov.cn/vec_w/wmts"
    
    # 文件上传配置
    UPLOAD_DIR: str = "UserUploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: list = [".gpx", ".kml", ".csv", ".txt"]
    
    # 匹配算法配置
    DEFAULT_ALGORITHM: str = "distance_matching"
    MATCHING_MAX_DISTANCE: float = 1000.0  # 米
    MATCHING_USE_SPEED_FILTER: bool = True
    MATCHING_MAX_SPEED: float = 200.0  # km/h
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "Logs"
    LOG_MAX_SIZE: int = 100 * 1024 * 1024  # 100MB
    LOG_BACKUP_COUNT: int = 10
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    
    # API配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith('mysql://') and not v.startswith('mysql+pymysql://'):
            raise ValueError('Database URL must be MySQL')
        return v
    
    @field_validator('TIANDITU_API_KEY')
    @classmethod
    def validate_tianditu_key(cls, v):
        # TIANDITU_API_KEY是可选的，不需要验证
        return v
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()


def get_database_url() -> str:
    """获取数据库连接URL"""
    return settings.DATABASE_URL


def get_redis_url() -> str:
    """获取Redis连接URL"""
    return settings.REDIS_URL


def get_tianditu_config() -> Dict[str, Any]:
    """获取天地图配置"""
    return {
        "api_key": settings.TIANDITU_API_KEY,
        "wgs84_url": f"{settings.TIANDITU_WGS84_URL}?tk={settings.TIANDITU_API_KEY}",
        "web_mercator_url": f"{settings.TIANDITU_WEB_MERCATOR_URL}?tk={settings.TIANDITU_API_KEY}"
    }


def get_matching_config() -> Dict[str, Any]:
    """获取匹配算法配置"""
    return {
        "default_algorithm": settings.DEFAULT_ALGORITHM,
        "max_distance": settings.MATCHING_MAX_DISTANCE,
        "use_speed_filter": settings.MATCHING_USE_SPEED_FILTER,
        "max_speed": settings.MATCHING_MAX_SPEED
    }