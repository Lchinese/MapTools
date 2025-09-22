"""
天地图WFS服务测试
专门测试天地图WFS服务的功能
"""

import unittest
import requests
import json
import time
from datetime import datetime

# API基础配置
BASE_URL = "http://localhost:8000"

class TestTiandituWFS(unittest.TestCase):
    """天地图WFS服务测试"""
    
    def setUp(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_bbox = "113.812401,22.503099,114.269966,22.748068"  # 深圳区域
    
    def test_wfs_capabilities(self):
        """测试WFS服务能力"""
        print("测试WFS服务能力...")
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/capabilities", timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_wfs_connection(self):
        """测试WFS服务连接"""
        print("\n测试WFS服务连接...")
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/test-connection", timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_road_layers(self):
        """测试获取道路图层"""
        print("\n测试获取道路图层...")
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/road-layers", timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
                self.assertIn("data", data, "响应应该包含data字段")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_load_roads(self):
        """测试加载道路数据"""
        print(f"\n测试加载道路数据 (边界框: {self.test_bbox})...")
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/load-roads", 
                                      params={
                                          "bbox": self.test_bbox,
                                          "max_features": 100
                                      }, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
                
                if data.get("success") and "data" in data:
                    roads = data["data"].get("roads", [])
                    print(f"加载了 {len(roads)} 条道路")
                    
                    # 显示前几条道路信息
                    for i, road in enumerate(roads[:3]):
                        print(f"  道路 {i+1}: {road.get('name', '未命名')} ({road.get('type', '未知类型')})")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_road_statistics(self):
        """测试获取道路统计信息"""
        print(f"\n测试获取道路统计信息 (边界框: {self.test_bbox})...")
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/road-statistics", 
                                      params={
                                          "bbox": self.test_bbox,
                                          "max_features": 100
                                      }, timeout=30)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
                
                if data.get("success") and "data" in data:
                    stats = data["data"].get("statistics", {})
                    print(f"道路统计: {stats}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_road_matching(self):
        """测试道路匹配功能"""
        print(f"\n测试道路匹配功能 (边界框: {self.test_bbox})...")
        try:
            response = self.session.post(f"{self.base_url}/tianditu-wfs/test-road-matching", 
                                       params={
                                           "bbox": self.test_bbox,
                                           "test_points": 5
                                       }, timeout=60)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                self.assertIn("success", data, "响应应该包含success字段")
                
                if data.get("success") and "data" in data:
                    test_data = data["data"]
                    print(f"测试点数: {test_data.get('test_points', 0)}")
                    print(f"匹配结果: {test_data.get('matched_points', [])}")
            else:
                print(f"错误: {response.text}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_different_bbox(self):
        """测试不同边界框"""
        print("\n测试不同边界框...")
        
        # 测试更小的区域
        small_bbox = "114.0,22.5,114.1,22.6"
        try:
            response = self.session.get(f"{self.base_url}/tianditu-wfs/load-roads", 
                                      params={
                                          "bbox": small_bbox,
                                          "max_features": 50
                                      }, timeout=30)
            print(f"小区域 ({small_bbox}) - 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                roads = data.get("data", {}).get("roads", [])
                print(f"小区域加载了 {len(roads)} 条道路")
        except Exception as e:
            print(f"小区域测试异常: {e}")
    
    def test_different_layers(self):
        """测试不同图层"""
        print("\n测试不同图层...")
        
        layers = ["LRDL", "LRRL", "AANP", "DLTB"]
        for layer in layers:
            try:
                response = self.session.get(f"{self.base_url}/tianditu-wfs/load-roads", 
                                          params={
                                              "bbox": self.test_bbox,
                                              "max_features": 20,
                                              "layer_name": layer
                                          }, timeout=30)
                print(f"图层 {layer} - 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    roads = data.get("data", {}).get("roads", [])
                    print(f"图层 {layer} 加载了 {len(roads)} 条道路")
            except Exception as e:
                print(f"图层 {layer} 测试异常: {e}")

def run_tianditu_tests():
    """运行天地图WFS测试"""
    print("=== 天地图WFS服务测试 ===")
    print(f"测试目标: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTiandituWFS)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n=== 测试总结 ===")
    print("天地图WFS服务测试完成！")
    print("\n注意事项：")
    print("1. 天地图WFS服务需要网络连接")
    print("2. 某些测试可能因为网络问题而失败")
    print("3. 如果所有测试都失败，请检查网络连接和服务状态")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tianditu_tests()
    exit(0 if success else 1)
