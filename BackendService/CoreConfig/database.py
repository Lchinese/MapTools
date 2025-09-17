"""
数据库配置模块
提供数据库连接和会话管理
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .settings import get_settings

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 创建元数据
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """创建所有数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """删除所有数据库表"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_connection() -> bool:
    """
    检查数据库连接
    
    Returns:
        bool: 连接是否成功
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# 数据库健康检查
def get_database_status() -> dict:
    """
    获取数据库状态信息
    
    Returns:
        dict: 数据库状态信息
    """
    try:
        with engine.connect() as connection:
            # 检查连接
            result = connection.execute("SELECT 1 as status")
            status = result.fetchone()[0]
            
            # 获取数据库版本
            version_result = connection.execute("SELECT VERSION() as version")
            version = version_result.fetchone()[0]
            
            return {
                "status": "connected" if status == 1 else "disconnected",
                "version": version,
                "pool_size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow()
            }
    except Exception as e:
        logger.error(f"Failed to get database status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }