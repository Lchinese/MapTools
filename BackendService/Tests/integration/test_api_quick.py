"""
MapTools API 快速测试
快速验证核心API功能
"""

import unittest
import requests
import json
import time

# API基础配置
BASE_URL = "http://localhost:8000"

class TestQuickAPI(unittest.TestCase):
    """快速API测试"""
    
    def setUp(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_basic_health(self):
        """测试基础健康检查"""
        print("1. 测试基础健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            print(f"   状态码: {response.status_code}")
            self.assertEqual(response.status_code, 200, "健康检查应该返回200状态码")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("status", data, "响应应该包含status字段")
        except Exception as e:
            self.fail(f"健康检查异常: {e}")
    
    def test_trajectory_apis(self):
        """测试轨迹数据API"""
        print("\n2. 测试轨迹数据API...")
        
        # 测试获取日期范围
        try:
            response = self.session.get(f"{self.base_url}/trajectory/date-range", timeout=10)
            print(f"   日期范围API - 状态码: {response.status_code}")
            self.assertEqual(response.status_code, 200, "日期范围API应该返回200状态码")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            self.fail(f"日期范围API异常: {e}")
        
        # 测试获取车牌号列表
        try:
            response = self.session.get(f"{self.base_url}/trajectory/plates", 
                                      params={"page_size": 5}, timeout=10)
            print(f"   车牌号列表API - 状态码: {response.status_code}")
            self.assertEqual(response.status_code, 200, "车牌号列表API应该返回200状态码")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            self.fail(f"车牌号列表API异常: {e}")
    
    def test_tianditu_wfs(self):
        """测试天地图WFS API"""
        print("\n3. 测试天地图WFS API...")
        
        # 测试连接
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/test-connection", timeout=30)
            print(f"   WFS连接测试 - 状态码: {response.status_code}")
            # WFS连接可能失败，所以不强制要求200状态码
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            print(f"   WFS连接测试异常: {e}")
        
        # 测试获取道路图层
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/road-layers", timeout=10)
            print(f"   道路图层API - 状态码: {response.status_code}")
            self.assertEqual(response.status_code, 200, "道路图层API应该返回200状态码")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            self.fail(f"道路图层API异常: {e}")
    
    def test_road_matching(self):
        """测试路网匹配API"""
        print("\n4. 测试路网匹配API...")
        
        # 测试道路匹配
        try:
            response = self.session.post(f"{self.base_url}/road-matching/match-trajectory",
                                       params={"plate_number": "粤B12345"}, timeout=30)
            print(f"   道路匹配API - 状态码: {response.status_code}")
            # 道路匹配可能失败（没有数据），所以不强制要求200状态码
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            print(f"   道路匹配API异常: {e}")
    
    def test_auth(self):
        """测试认证API"""
        print("\n5. 测试认证API...")
        
        # 测试用户注册
        try:
            register_data = {
                "username": f"test_user_{int(time.time())}",
                "email": f"test{int(time.time())}@example.com",
                "password": "test_password_123"
            }
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=register_data, timeout=10)
            print(f"   用户注册API - 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   响应: {data}")
                self.assertIn("success", data, "响应应该包含success字段")
        except Exception as e:
            print(f"   用户注册API异常: {e}")

def run_quick_tests():
    """运行快速测试"""
    print("=== MapTools API 快速测试 ===")
    print(f"测试目标: {BASE_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQuickAPI)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n=== 测试总结 ===")
    print("快速测试完成！请查看上述输出了解各API状态。")
    print("\n如果看到错误，请确保：")
    print("1. 后端服务正在运行 (python main.py)")
    print("2. MongoDB服务正在运行")
    print("3. MySQL服务正在运行")
    print("4. 网络连接正常")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_quick_tests()
    exit(0 if success else 1)
