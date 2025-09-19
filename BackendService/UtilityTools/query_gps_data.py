"""
按车牌号查询MongoDB中的GPS数据
"""

import pymongo
from datetime import datetime
import argparse
import sys

def connect_to_mongodb(db_name="MapTools", collection_name="gps_points"):
    """
    连接到MongoDB数据库
    
    Args:
        db_name (str): 数据库名称
        collection_name (str): 集合名称
        
    Returns:
        collection: MongoDB集合对象
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

def query_by_plate_number(collection, plate_number):
    """
    根据车牌号查询GPS数据
    
    Args:
        collection: MongoDB集合对象
        plate_number (str): 车牌号
        
    Returns:
        list: 查询结果列表
    """
    try:
        # 查询指定车牌号的所有记录
        results = list(collection.find({"plate_number": plate_number}))
        return results
    except Exception as e:
        print(f"查询数据时出错: {e}")
        return []

def query_by_plate_and_date_range(collection, plate_number, start_date=None, end_date=None):
    """
    根据车牌号和日期范围查询GPS数据
    
    Args:
        collection: MongoDB集合对象
        plate_number (str): 车牌号
        start_date (str): 开始日期 (格式: YYYY-MM-DD)
        end_date (str): 结束日期 (格式: YYYY-MM-DD)
        
    Returns:
        list: 查询结果列表
    """
    try:
        # 构建查询条件
        query = {"plate_number": plate_number}
        
        # 添加日期范围条件
        if start_date or end_date:
            date_query = {}
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                date_query["$gte"] = start_dt
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                # 将结束日期设置为当天的最后一秒
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                date_query["$lte"] = end_dt
            query["datetime"] = date_query
        
        # 执行查询
        results = list(collection.find(query).sort("datetime", 1))  # 按时间升序排列
        return results
    except Exception as e:
        print(f"查询数据时出错: {e}")
        return []

def display_results(results, plate_number):
    """
    显示查询结果
    
    Args:
        results (list): 查询结果列表
        plate_number (str): 车牌号
    """
    if not results:
        print(f"未找到车牌号为 {plate_number} 的数据")
        return
    
    print(f"\n找到 {len(results)} 条车牌号为 {plate_number} 的记录:")
    print("-" * 80)
    
    for i, record in enumerate(results, 1):
        print(f"{i}. 时间: {record['datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   位置: ({record['location']['coordinates'][1]}, {record['location']['coordinates'][0]})")
        print(f"   速度: {record['speed']} km/h")
        print(f"   方向: {record['heading']} 度")
        print(f"   有效定位: {'是' if record['is_valid'] else '否'}")
        print(f"   来源文件: {record['source_file']}")
        print()

def get_all_plate_numbers(collection):
    """
    获取数据库中所有不同的车牌号
    
    Args:
        collection: MongoDB集合对象
        
    Returns:
        list: 车牌号列表
    """
    try:
        plate_numbers = collection.distinct("plate_number")
        return plate_numbers
    except Exception as e:
        print(f"获取车牌号列表时出错: {e}")
        return []

def display_plate_numbers(plate_numbers):
    """
    显示所有车牌号
    
    Args:
        plate_numbers (list): 车牌号列表
    """
    if not plate_numbers:
        print("数据库中没有车牌号数据")
        return
    
    print(f"\n数据库中共有 {len(plate_numbers)} 个不同的车牌号:")
    print("-" * 40)
    
    # 按字母顺序排序
    plate_numbers.sort()
    
    # 分列显示
    for i in range(0, len(plate_numbers), 3):
        row = plate_numbers[i:i+3]
        print("  ".join(f"{plate:<12}" for plate in row))

def main():
    """
    主函数
    """
    # 连接到MongoDB
    collection, client = connect_to_mongodb()
    if collection is None:
        sys.exit(1)
    
    try:
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description="按车牌号查询GPS数据")
        parser.add_argument("-p", "--plate", help="车牌号")
        parser.add_argument("-s", "--start", help="开始日期 (格式: YYYY-MM-DD)")
        parser.add_argument("-e", "--end", help="结束日期 (格式: YYYY-MM-DD)")
        parser.add_argument("-l", "--list", action="store_true", help="列出所有车牌号")
        
        args = parser.parse_args()
        
        # 如果指定了-l参数，列出所有车牌号
        if args.list:
            plate_numbers = get_all_plate_numbers(collection)
            display_plate_numbers(plate_numbers)
            return
        
        # 如果指定了车牌号，进行查询
        if args.plate:
            if args.start or args.end:
                # 带日期范围的查询
                results = query_by_plate_and_date_range(collection, args.plate, args.start, args.end)
            else:
                # 简单的车牌号查询
                results = query_by_plate_number(collection, args.plate)
            
            display_results(results, args.plate)
        else:
            # 如果没有指定参数，显示帮助信息
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()