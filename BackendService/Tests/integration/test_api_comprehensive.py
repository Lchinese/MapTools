"""
MapTools API 综合测试
测试所有API端点的功能和性能
"""

import unittest
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

# API基础配置
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.test_results = []
    
    def test_endpoint(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, expected_status: int = 200) -> Dict[str, Any]:
        """测试单个API端点"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, params=params, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                "method": method,
                "endpoint": endpoint,
                "url": url,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code == expected_status,
                "response_size": len(response.content),
                "timestamp": datetime.now().isoformat()
            }
            
            # 尝试解析JSON响应
            try:
                result["response_data"] = response.json()
            except:
                result["response_text"] = response.text[:500]  # 限制文本长度
            
            # 记录错误信息
            if not result["success"]:
                result["error"] = f"期望状态码 {expected_status}, 实际状态码 {response.status_code}"
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "method": method,
                "endpoint": endpoint,
                "url": url,
                "status_code": 0,
                "response_time": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            return error_result

class TestHealthAPIs(unittest.TestCase):
    """健康检查API测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_basic_health(self):
        """测试基础健康检查"""
        result = self.tester.test_endpoint("GET", "/health")
        self.assertTrue(result["success"], f"健康检查失败: {result.get('error')}")
    
    def test_detailed_health(self):
        """测试详细健康检查"""
        result = self.tester.test_endpoint("GET", "/health/detailed")
        self.assertTrue(result["success"], f"详细健康检查失败: {result.get('error')}")
    
    def test_root_endpoint(self):
        """测试根路径"""
        result = self.tester.test_endpoint("GET", "/")
        self.assertTrue(result["success"], f"根路径测试失败: {result.get('error')}")

class TestTrajectoryAPIs(unittest.TestCase):
    """轨迹数据API测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_date_range(self):
        """测试获取日期范围"""
        result = self.tester.test_endpoint("GET", "/trajectory/date-range")
        self.assertTrue(result["success"], f"获取日期范围失败: {result.get('error')}")
    
    def test_plate_numbers(self):
        """测试获取车牌号列表"""
        result = self.tester.test_endpoint("GET", "/trajectory/plates", {
            "page_size": 10
        })
        self.assertTrue(result["success"], f"获取车牌号列表失败: {result.get('error')}")
    
    def test_time_slots(self):
        """测试获取时间段信息"""
        result = self.tester.test_endpoint("GET", "/trajectory/time-slots", {
            "date": "2023-10-01"
        })
        self.assertTrue(result["success"], f"获取时间段信息失败: {result.get('error')}")
    
    def test_trajectory_summary(self):
        """测试获取轨迹摘要"""
        result = self.tester.test_endpoint("GET", "/trajectory/summary", {
            "plate_number": "粤B12345"
        })
        # 即使没有数据也应该返回成功状态
        self.assertTrue(result["success"], f"获取轨迹摘要失败: {result.get('error')}")
    
    def test_trajectory_by_plate(self):
        """测试根据车牌号获取轨迹"""
        result = self.tester.test_endpoint("GET", "/trajectory/by-plate", {
            "plate_number": "粤B12345",
            "page": 1,
            "page_size": 100
        })
        self.assertTrue(result["success"], f"根据车牌号获取轨迹失败: {result.get('error')}")
    
    def test_batch_trajectory(self):
        """测试批量获取轨迹数据"""
        result = self.tester.test_endpoint("GET", "/trajectory/batch", {
            "limit": 10,
            "match_to_roads": False
        })
        self.assertTrue(result["success"], f"批量获取轨迹数据失败: {result.get('error')}")

class TestTiandituWFSAPIs(unittest.TestCase):
    """天地图WFS API测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_capabilities(self):
        """测试获取WFS服务能力"""
        result = self.tester.test_endpoint("GET", "/tianditu-wfs/capabilities")
        self.assertTrue(result["success"], f"获取WFS服务能力失败: {result.get('error')}")
    
    def test_connection(self):
        """测试WFS服务连接"""
        result = self.tester.test_endpoint("GET", "/tianditu-wfs/test-connection")
        self.assertTrue(result["success"], f"WFS服务连接测试失败: {result.get('error')}")
    
    def test_road_layers(self):
        """测试获取道路图层"""
        result = self.tester.test_endpoint("GET", "/tianditu-wfs/road-layers")
        self.assertTrue(result["success"], f"获取道路图层失败: {result.get('error')}")
    
    def test_load_roads(self):
        """测试加载道路数据"""
        bbox = "113.812401,22.503099,114.269966,22.748068"
        result = self.tester.test_endpoint("GET", "/tianditu-wfs/load-roads", {
            "bbox": bbox,
            "max_features": 100
        })
        self.assertTrue(result["success"], f"加载道路数据失败: {result.get('error')}")
    
    def test_road_statistics(self):
        """测试获取道路统计信息"""
        bbox = "113.812401,22.503099,114.269966,22.748068"
        result = self.tester.test_endpoint("GET", "/tianditu-wfs/road-statistics", {
            "bbox": bbox,
            "max_features": 100
        })
        self.assertTrue(result["success"], f"获取道路统计信息失败: {result.get('error')}")

class TestRoadMatchingAPIs(unittest.TestCase):
    """路网匹配API测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_match_trajectory(self):
        """测试匹配轨迹到道路"""
        result = self.tester.test_endpoint("POST", "/road-matching/match-trajectory", {
            "plate_number": "粤B12345",
            "algorithm": "distance_matching"
        })
        self.assertTrue(result["success"], f"匹配轨迹到道路失败: {result.get('error')}")
    
    def test_batch_match(self):
        """测试批量匹配轨迹"""
        result = self.tester.test_endpoint("POST", "/road-matching/batch-match", {
            "plate_numbers": ["粤B12345", "粤B67890"],
            "algorithm": "distance_matching"
        })
        self.assertTrue(result["success"], f"批量匹配轨迹失败: {result.get('error')}")
    
    def test_generate_road_trajectory(self):
        """测试生成沿道路轨迹"""
        result = self.tester.test_endpoint("POST", "/road-matching/generate-road-trajectory", {
            "plate_number": "粤B12345",
            "smooth_factor": 0.5
        })
        self.assertTrue(result["success"], f"生成沿道路轨迹失败: {result.get('error')}")

class TestAuthAPIs(unittest.TestCase):
    """认证API测试"""
    
    def setUp(self):
        self.tester = APITester()
        self.test_username = f"test_user_{int(time.time())}"
        self.test_email = f"test{int(time.time())}@example.com"
        self.test_password = "test_password_123"
    
    def test_register(self):
        """测试用户注册"""
        result = self.tester.test_endpoint("POST", "/auth/register", data={
            "username": self.test_username,
            "email": self.test_email,
            "password": self.test_password
        })
        self.assertTrue(result["success"], f"用户注册失败: {result.get('error')}")
    
    def test_login(self):
        """测试用户登录"""
        # 先注册用户
        self.tester.test_endpoint("POST", "/auth/register", data={
            "username": self.test_username,
            "email": self.test_email,
            "password": self.test_password
        })
        
        # 然后测试登录
        result = self.tester.test_endpoint("POST", "/auth/login", data={
            "username": self.test_username,
            "password": self.test_password
        })
        self.assertTrue(result["success"], f"用户登录失败: {result.get('error')}")

class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_nonexistent_endpoint(self):
        """测试不存在的端点"""
        result = self.tester.test_endpoint("GET", "/nonexistent-endpoint", expected_status=404)
        self.assertTrue(result["success"], f"不存在的端点应该返回404: {result.get('error')}")
    
    def test_invalid_parameters(self):
        """测试无效参数"""
        result = self.tester.test_endpoint("GET", "/trajectory/by-plate", {
            "plate_number": "",  # 空车牌号
        })
        # 空车牌号应该返回错误状态
        self.assertFalse(result["success"], "空车牌号应该返回错误")
    
    def test_invalid_date_format(self):
        """测试无效日期格式"""
        result = self.tester.test_endpoint("GET", "/trajectory/time-slots", {
            "date": "invalid-date"
        })
        # 无效日期格式应该返回错误
        self.assertFalse(result["success"], "无效日期格式应该返回错误")

class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        self.tester = APITester()
    
    def test_trajectory_query_performance(self):
        """测试轨迹数据查询性能"""
        start_time = time.time()
        
        for i in range(5):
            result = self.tester.test_endpoint("GET", "/trajectory/plates", {
                "page_size": 50
            })
            self.assertTrue(result["success"], f"轨迹数据查询失败: {result.get('error')}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 5次请求应该在10秒内完成
        self.assertLess(total_time, 10, f"轨迹数据查询性能测试失败，耗时 {total_time:.2f}秒")
    
    def test_response_time(self):
        """测试响应时间"""
        result = self.tester.test_endpoint("GET", "/health")
        self.assertTrue(result["success"], f"健康检查失败: {result.get('error')}")
        
        # 响应时间应该在5秒内
        self.assertLess(result["response_time"], 5, 
                       f"响应时间过长: {result['response_time']:.3f}秒")

def create_test_suite():
    """创建测试套件"""
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestHealthAPIs,
        TestTrajectoryAPIs,
        TestTiandituWFSAPIs,
        TestRoadMatchingAPIs,
        TestAuthAPIs,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def run_tests():
    """运行测试"""
    print("=== MapTools API 综合测试 ===")
    print(f"测试目标: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试套件
    suite = create_test_suite()
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print(f"\n测试结果:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  成功率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.2f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
