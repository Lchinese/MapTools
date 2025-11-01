#!/usr/bin/env python3
import pymongo

def check_road_data():
    try:
        client = pymongo.MongoClient('localhost', 27017)
        db = client['MapTools']
        collection = db['道路数据']
        
        # 检查集合是否存在
        if collection.count_documents({}) == 0:
            print("道路数据集合为空")
            return
        
        # 获取一个样本文档
        doc = collection.find_one({'type': 'Feature'})
        if not doc:
            print("没有找到Feature类型的文档")
            return
            
        print("样本道路数据:")
        print(f"ID: {doc.get('id', '无')}")
        print(f"分类: {doc.get('分类名称', '无')}")
        print(f"几何类型: {doc.get('geometry', {}).get('type', '无')}")
        
        geometry = doc.get('geometry', {})
        coordinates = geometry.get('coordinates', [])
        print(f"坐标数量: {len(coordinates)}")
        
        if coordinates:
            print(f"第一个坐标: {coordinates[0]}")
            print(f"坐标格式: [经度, 纬度] = [{coordinates[0][0]}, {coordinates[0][1]}]")
        
        properties = doc.get('properties', {})
        print(f"属性: {properties}")
        
        # 检查总数
        total = collection.count_documents({'type': 'Feature'})
        print(f"总道路数量: {total}")
        
        client.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_road_data()
