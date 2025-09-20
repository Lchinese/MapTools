"""
从MongoDB读取轨迹数据并返回指定格式的脚本
支持按车牌号查询并将数据格式化为 {车牌号: [轨迹点列表]} 的形式
"""

import pymongo
from datetime import datetime
from typing import Dict, List, Any


def connect_to_mongodb(db_name: str = "MapTools", collection_name: str = "gps_points"):
    """
    连接到MongoDB数据库

    Args:
        db_name (str): 数据库名称
        collection_name (str): 集合名称

    Returns:
        tuple: (collection, client) MongoDB集合对象和客户端连接
    """
    try:
        client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        # 测试连接
        client.server_info()
        db = client[db_name]
        collection = db[collection_name]
        print(f"成功连接到MongoDB: {db_name}.{collection_name}")
        return collection, client
    except Exception as e:
        print(f"连接MongoDB失败: {e}")
        return None, None


def fetch_all_trajectory_data(db_name: str = "MapTools", collection_name: str = "gps_points") -> Dict[str, List[Dict[str, Any]]]:
    """
    从MongoDB获取所有车辆轨迹数据，按车牌号分组

    Args:
        db_name (str): 数据库名称
        collection_name (str): 集合名称

    Returns:
        Dict[str, List[Dict[str, Any]]]: 以车牌号为键，轨迹点列表为值的字典
            格式: {
                "京A12345": [
                    { 'plate_number': '京A12345', 'datetime': '2023-10-01T08:00:00', 'longitude': 116.4, 'latitude': 39.9, ... },
                    { 'plate_number': '京A12345', 'datetime': '2023-10-01T08:01:00', 'longitude': 116.41, 'latitude': 39.91, ... },
                    ...
                ],
                ...
            }
    """
    collection, client = connect_to_mongodb(db_name, collection_name)
    if collection is None:
        return {}

    try:
        # 获取所有不同的车牌号
        plate_numbers = collection.distinct("plate_number")
        result = {}

        # 逐个查询每个车牌号的数据
        for plate_number in plate_numbers:
            # 查询该车牌号的所有记录
            records = list(collection.find({"plate_number": plate_number}).sort("datetime", 1))
            
            # 转换记录格式
            formatted_records = []
            for record in records:
                formatted_record = {
                    'plate_number': record['plate_number'],
                    'datetime': record['datetime'].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(record['datetime'], datetime) else record['datetime'],
                    'longitude': record['location']['coordinates'][0],  # 经度
                    'latitude': record['location']['coordinates'][1],   # 纬度
                    'speed': record.get('speed', 0),
                    'heading': record.get('heading', 0),
                    'is_valid': record.get('is_valid', False),
                    'source_file': record.get('source_file', '')
                }
                formatted_records.append(formatted_record)
            
            # 按车牌号分组存储
            result[plate_number] = formatted_records

        return result
    except Exception as e:
        print(f"查询数据时出错: {e}")
        return {}
    finally:
        if client:
            client.close()


def fetch_trajectory_data_by_plate(plate_number: str, 
                                   db_name: str = "MapTools", 
                                   collection_name: str = "gps_points") -> Dict[str, List[Dict[str, Any]]]:
    """
    根据车牌号从MongoDB获取轨迹数据

    Args:
        plate_number (str): 车牌号
        db_name (str): 数据库名称
        collection_name (str): 集合名称

    Returns:
        Dict[str, List[Dict[str, Any]]]: 以车牌号为键，轨迹点列表为值的字典
            格式: {
                "京A12345": [
                    { 'plate_number': '京A12345', 'datetime': '2023-10-01T08:00:00', 'longitude': 116.4, 'latitude': 39.9, ... },
                    { 'plate_number': '京A12345', 'datetime': '2023-10-01T08:01:00', 'longitude': 116.41, 'latitude': 39.91, ... },
                    ...
                ]
            }
    """
    collection, client = connect_to_mongodb(db_name, collection_name)
    if collection is None:
        return {}

    try:
        # 查询指定车牌号的所有记录
        records = list(collection.find({"plate_number": plate_number}).sort("datetime", 1))
        
        # 转换记录格式
        formatted_records = []
        for record in records:
            formatted_record = {
                'plate_number': record['plate_number'],
                'datetime': record['datetime'].strftime('%Y-%m-%dT%H:%M:%S') if isinstance(record['datetime'], datetime) else record['datetime'],
                'longitude': record['location']['coordinates'][0],  # 经度
                'latitude': record['location']['coordinates'][1],   # 纬度
                'speed': record.get('speed', 0),
                'heading': record.get('heading', 0),
                'is_valid': record.get('is_valid', False),
                'source_file': record.get('source_file', '')
            }
            formatted_records.append(formatted_record)
        
        # 按车牌号分组存储
        return {plate_number: formatted_records}
        
    except Exception as e:
        print(f"查询数据时出错: {e}")
        return {}
    finally:
        if client:
            client.close()


def fetch_plate_numbers(page: int = 1, page_size: int = 10,
                        db_name: str = "MapTools", 
                        collection_name: str = "gps_points") -> tuple:
    """
    分页获取车牌号列表

    Args:
        page (int): 页码
        page_size (int): 每页数量
        db_name (str): 数据库名称
        collection_name (str): 集合名称

    Returns:
        tuple: (车牌号列表, 总数, 总页数)
    """
    collection, client = connect_to_mongodb(db_name, collection_name)
    if collection is None:
        return [], 0, 0

    try:
        # 获取所有不同的车牌号
        all_plate_numbers = collection.distinct("plate_number")
        total = len(all_plate_numbers)
        total_pages = (total + page_size - 1) // page_size  # 向上取整
        
        # 验证页码
        if page > total_pages and total_pages > 0:
            page = total_pages
            
        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_plates = all_plate_numbers[start_idx:end_idx]
        
        return paginated_plates, total, total_pages
        
    except Exception as e:
        print(f"查询车牌号时出错: {e}")
        return [], 0, 0
    finally:
        if client:
            client.close()


def example_usage():
    """
    使用示例
    """
    # 获取所有车辆数据
    print("获取所有车辆轨迹数据...")
    all_data = fetch_all_trajectory_data()
    for plate, points in list(all_data.items())[:2]:  # 只显示前两个车牌号的数据
        print(f"{plate}: {len(points)} 个轨迹点")
        if points:
            print(f"  示例点: {points[0]}")
    print()

    # 获取特定车辆数据
    print("获取特定车辆轨迹数据...")
    plate_number = "京A12345"  # 示例车牌号
    plate_data = fetch_trajectory_data_by_plate(plate_number)
    if plate_data:
        points = plate_data[plate_number]
        print(f"{plate_number}: {len(points)} 个轨迹点")
        if points:
            print(f"  示例点: {points[0]}")
    else:
        print(f"未找到车牌号 {plate_number} 的数据")


if __name__ == "__main__":
    example_usage()