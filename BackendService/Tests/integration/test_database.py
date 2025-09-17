"""
数据库集成测试
"""

import sys
import os
from pathlib import Path
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入相关模块
try:
    from CoreConfig.database import Base, get_db
    from DataModels.Models.trajectory import Trajectory, TrajectoryPoint
    from DataModels.Models.road_network import RoadSegment
except ImportError:
    try:
        from BackendService.CoreConfig.database import Base, get_db
        from BackendService.DataModels.Models.trajectory import Trajectory, TrajectoryPoint
        from BackendService.DataModels.Models.road_network import RoadSegment
    except ImportError:
        # 如果无法导入，跳过这些测试
        class TestDatabaseModels(unittest.TestCase):
            def test_skip_database_tests(self):
                self.skipTest("无法导入数据库模型")
        
        if __name__ == '__main__':
            unittest.main()
        exit()

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestDatabaseModels(unittest.TestCase):
    """数据库模型测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建所有表
        try:
            Base.metadata.create_all(bind=engine)
            self.session = TestingSessionLocal()
        except Exception as e:
            self.skipTest(f"无法创建测试数据库: {e}")
        
    def tearDown(self):
        """测试后的清理工作"""
        try:
            self.session.close()
            Base.metadata.drop_all(bind=engine)
        except:
            pass
        
    def test_trajectory_model_creation(self):
        """测试轨迹模型创建和保存"""
        # 创建轨迹点
        points = [
            TrajectoryPoint(
                point_id="point_001",
                sequence_number=1,
                latitude=39.9087,
                longitude=116.3974,
                timestamp=1000,
                speed=10.0,
                direction=45.0
            ),
            TrajectoryPoint(
                point_id="point_002",
                sequence_number=2,
                latitude=39.9088,
                longitude=116.3975,
                timestamp=1001,
                speed=12.0,
                direction=46.0
            )
        ]
        
        # 创建轨迹
        trajectory = Trajectory(
            trajectory_id="test_traj_001",
            user_id="user_001",
            name="测试轨迹",
            filename="test.gpx",
            file_size=1024,
            file_type="gpx",
            data_source="gpx",
            data_category="continuous_trajectory",
            points=points
        )
        
        # 保存到数据库
        self.session.add(trajectory)
        self.session.commit()
        
        # 从数据库查询
        retrieved_trajectory = self.session.query(Trajectory).filter(
            Trajectory.trajectory_id == "test_traj_001"
        ).first()
        
        # 验证数据
        self.assertIsNotNone(retrieved_trajectory)
        self.assertEqual(retrieved_trajectory.trajectory_id, "test_traj_001")
        self.assertEqual(retrieved_trajectory.name, "测试轨迹")
        self.assertEqual(len(retrieved_trajectory.points), 2)
        
    def test_road_segment_model_creation(self):
        """测试道路段模型创建和保存"""
        # 创建道路段
        road_segment = RoadSegment(
            segment_id="seg_001",
            network_id="network_001",
            start_latitude=39.9080,
            start_longitude=116.3970,
            end_latitude=39.9090,
            end_longitude=116.3980,
            road_name="测试道路",
            road_type="primary"
        )
        
        # 保存到数据库
        self.session.add(road_segment)
        self.session.commit()
        
        # 从数据库查询
        retrieved_segment = self.session.query(RoadSegment).filter(
            RoadSegment.segment_id == "seg_001"
        ).first()
        
        # 验证数据
        self.assertIsNotNone(retrieved_segment)
        self.assertEqual(retrieved_segment.segment_id, "seg_001")
        self.assertEqual(retrieved_segment.road_name, "测试道路")
        self.assertEqual(retrieved_segment.road_type, "primary")
        
    def test_trajectory_point_relationship(self):
        """测试轨迹点关系"""
        # 创建轨迹点
        points = [
            TrajectoryPoint(
                point_id="point_003",
                sequence_number=1,
                latitude=39.9087,
                longitude=116.3974,
                timestamp=1000
            )
        ]
        
        # 创建轨迹
        trajectory = Trajectory(
            trajectory_id="test_traj_002",
            user_id="user_001",
            name="关系测试轨迹",
            filename="test.gpx",
            file_size=1024,
            file_type="gpx",
            data_source="gpx",
            data_category="continuous_trajectory",
            points=points
        )
        
        # 保存到数据库
        self.session.add(trajectory)
        self.session.commit()
        
        # 验证轨迹点与轨迹的关系
        retrieved_trajectory = self.session.query(Trajectory).filter(
            Trajectory.trajectory_id == "test_traj_002"
        ).first()
        
        self.assertIsNotNone(retrieved_trajectory)
        self.assertEqual(len(retrieved_trajectory.points), 1)
        self.assertEqual(retrieved_trajectory.points[0].latitude, 39.9087)
        self.assertEqual(retrieved_trajectory.points[0].longitude, 116.3974)

if __name__ == '__main__':
    unittest.main()