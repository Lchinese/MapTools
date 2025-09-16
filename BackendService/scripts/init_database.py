#!/usr/bin/env python3
"""
数据库初始化脚本
使用SQLAlchemy ORM创建数据库和表结构
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CoreConfig.settings import get_settings
from DataModels.base import Base
from CoreConfig.database import engine

# 导入所有模型以确保它们被注册到Base.metadata
from DataModels.Models.trajectory import (
    Trajectory, TrajectoryPoint, MatchingTask, MatchedPoint,
    User, RoadNetwork, RoadSegment, File, SystemLog
)

def create_database():
    """创建数据库（如果不存在）"""
    settings = get_settings()
    
    # 解析数据库URL
    db_url = settings.DATABASE_URL
    if db_url.startswith('mysql+pymysql://'):
        db_url = db_url.replace('mysql+pymysql://', 'mysql+pymysql://')
    
    # 提取数据库名称
    db_name = db_url.split('/')[-1]
    base_url = '/'.join(db_url.split('/')[:-1])
    
    print(f"正在创建数据库: {db_name}")
    
    try:
        # 连接到MySQL服务器（不指定数据库）
        engine = create_engine(f"{base_url}/mysql")
        
        with engine.connect() as conn:
            # 删除数据库（如果存在）
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            print(f"已删除现有数据库: {db_name}")
            
            # 创建数据库
            conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"数据库 {db_name} 创建成功")
            
            # 提交事务
            conn.commit()
            
    except SQLAlchemyError as e:
        print(f"创建数据库时出错: {e}")
        return False
    
    return True

def create_tables():
    """创建所有表"""
    print("正在创建表结构...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("所有表创建成功")
        
        # 显示创建的表
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"已创建的表: {[table[0] for table in tables]}")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"创建表时出错: {e}")
        return False

def verify_tables():
    """验证表结构"""
    print("正在验证表结构...")
    
    try:
        with engine.connect() as conn:
            # 检查每个表是否存在
            expected_tables = [
                'users', 'trajectories', 'trajectory_points', 
                'matching_tasks', 'matched_points',
                'road_networks', 'road_segments', 'files', 'system_logs'
            ]
            
            result = conn.execute(text("SHOW TABLES"))
            existing_tables = [table[0] for table in result.fetchall()]
            
            print("表结构验证结果:")
            for table in expected_tables:
                if table in existing_tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} (缺失)")
            
            return len(existing_tables) == len(expected_tables)
            
    except SQLAlchemyError as e:
        print(f"验证表结构时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("MapTools 数据库初始化")
    print("=" * 50)
    
    # 步骤1: 创建数据库
    if not create_database():
        print("数据库创建失败，退出")
        return False
    
    # 步骤2: 创建表
    if not create_tables():
        print("表创建失败，退出")
        return False
    
    # 步骤3: 验证表结构
    if not verify_tables():
        print("表结构验证失败")
        return False
    
    print("=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
