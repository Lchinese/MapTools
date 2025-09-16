"""
API集成测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from BackendService.main import app
from BackendService.CoreConfig.database import Base, get_db
from BackendService.CoreConfig.settings import get_settings

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestHealthAPI:
    """健康检查API测试"""
    
    def test_health_check(self, setup_database):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "status" in data["data"]
    
    def test_detailed_health_check(self, setup_database):
        """测试详细健康检查"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "system" in data["data"]
        assert "services" in data["data"]

class TestTrajectoryAPI:
    """轨迹API测试"""
    
    def test_get_trajectories(self, setup_database):
        """测试获取轨迹列表"""
        response = client.get("/api/v1/trajectories")
        assert response.status_code == 200
        data = response.json()
        assert "trajectories" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
    
    def test_get_trajectory_not_found(self, setup_database):
        """测试获取不存在的轨迹"""
        response = client.get("/api/v1/trajectories/999")
        assert response.status_code == 404
    
    def test_delete_trajectory_not_found(self, setup_database):
        """测试删除不存在的轨迹"""
        response = client.delete("/api/v1/trajectories/999")
        assert response.status_code == 404

class TestMatchingAPI:
    """地图匹配API测试"""
    
    def test_get_available_algorithms(self, setup_database):
        """测试获取可用算法"""
        response = client.get("/api/v1/matching/algorithms")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "algorithms" in data["data"]
        assert "default_algorithm" in data["data"]
    
    def test_get_matching_tasks(self, setup_database):
        """测试获取匹配任务列表"""
        response = client.get("/api/v1/matching/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
    
    def test_get_matching_status_not_found(self, setup_database):
        """测试获取不存在的匹配任务状态"""
        response = client.get("/api/v1/matching/status/non-existent-task-id")
        assert response.status_code == 404
    
    def test_get_matching_result_not_found(self, setup_database):
        """测试获取不存在的匹配结果"""
        response = client.get("/api/v1/matching/result/non-existent-task-id")
        assert response.status_code == 404

class TestFileUpload:
    """文件上传测试"""
    
    def test_upload_invalid_file(self, setup_database):
        """测试上传无效文件"""
        # 创建一个临时文件
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/api/v1/trajectories/upload",
                    files={"file": ("test.txt", f, "text/plain")},
                    data={"name": "测试轨迹"}
                )
            
            # 应该成功上传（即使是空文件）
            assert response.status_code in [200, 201, 400]  # 可能因为文件内容无效而返回400
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_without_file(self, setup_database):
        """测试不上传文件"""
        response = client.post("/api/v1/trajectories/upload")
        assert response.status_code == 422  # 缺少必需参数

class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_endpoint(self, setup_database):
        """测试无效端点"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
    
    def test_invalid_query_parameters(self, setup_database):
        """测试无效查询参数"""
        response = client.get("/api/v1/trajectories?page=0")  # 无效页码
        assert response.status_code == 422
        
        response = client.get("/api/v1/trajectories?limit=1000")  # 超出限制
        assert response.status_code == 422