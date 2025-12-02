import pymongo
import pandas as pd
import os
import time

def connect_to_mongodb():
    """连接到MongoDB数据库"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["MapTools"]
        return client, db
    except Exception as e:
        print(f"连接MongoDB失败: {e}")
        return None, None

def export_sample_trajectories_to_csv():
    """导出前100条原始轨迹和对应的修正轨迹数据到CSV文件"""
    # 连接MongoDB
    client, db = connect_to_mongodb()
    if not client or db is None:
        return
    
    try:
        # CSV文件路径
        original_csv_file = "sample_original_trajectories.csv"
        corrected_csv_file = "sample_corrected_trajectories.csv"
        
        # 如果CSV文件已存在，先删除它们
        if os.path.exists(original_csv_file):
            os.remove(original_csv_file)
            print(f"已删除已存在的 {original_csv_file} 文件")
            
        if os.path.exists(corrected_csv_file):
            os.remove(corrected_csv_file)
            print(f"已删除已存在的 {corrected_csv_file} 文件")
        
        # 记录开始时间
        start_time = time.time()
        
        # 用于收集数据的列表
        original_data = []
        corrected_data = []
        plate_list = []  # 存储已处理的车牌号，保证顺序一致
        
        # 遍历原始轨迹集合获取前100辆车的车牌号
        plate_count = 0
        for i in range(1, 31):
            if plate_count >= 100:
                break
                
            collection_name = f"original_trajectories_{i:02d}"
            collection = db[collection_name]
            
            print(f"正在处理集合: {collection_name}")
            
            # 检查集合是否存在且有数据
            doc_count = collection.count_documents({})
            if doc_count == 0:
                print(f"集合 {collection_name} 为空或不存在，跳过")
                continue
            
            print(f"集合 {collection_name} 包含 {doc_count} 个文档")
            
            # 查询前若干个文档，直到达到100辆车
            cursor = collection.find({}).limit(100 - plate_count)
            
            for trajectory_doc in cursor:
                plate_number = trajectory_doc.get("plate_number")
                if plate_number in plate_list:
                    continue  # 避免重复
                    
                if "trajectory_points" not in trajectory_doc or not trajectory_doc["trajectory_points"]:
                    continue
                
                # 提取轨迹点数据
                trajectory_points = trajectory_doc["trajectory_points"]
                
                # 转换为列表
                for point in trajectory_points:
                    row = {
                        "plate_number": plate_number,
                        "datetime": point.get("datetime"),
                        "longitude": point.get("longitude"),
                        "latitude": point.get("latitude"),
                        "speed": point.get("speed"),
                        "heading": point.get("heading"),
                        "is_valid": point.get("is_valid"),
                        "source_file": point.get("source_file")
                    }
                    original_data.append(row)
                
                plate_list.append(plate_number)
                plate_count += 1
                print(f"  已添加车辆 {plate_number} 的原始轨迹数据，共 {len(trajectory_points)} 个轨迹点")
                
                # 如果已经达到100辆车，停止处理
                if plate_count >= 100:
                    break
        
        print(f"\n总共获取了 {len(plate_list)} 个车牌号:")
        for i, plate in enumerate(plate_list):
            print(f"  {i+1}. {plate}")
        
        # 根据车牌号列表获取对应的修正轨迹数据
        corrected_plate_count = 0
        for plate_number in plate_list:
            # 在所有修正轨迹集合中查找该车牌号
            for i in range(1, 31):
                collection_name = f"corrected_trajectories_{i:02d}"
                collection = db[collection_name]
                
                trajectory_doc = collection.find_one({"plate_number": plate_number})
                if trajectory_doc:
                    if "trajectory_points" not in trajectory_doc or not trajectory_doc["trajectory_points"]:
                        continue
                    
                    # 提取轨迹点数据
                    trajectory_points = trajectory_doc["trajectory_points"]
                    
                    # 转换为列表
                    for point in trajectory_points:
                        row = {
                            "plate_number": plate_number,
                            "datetime": point.get("datetime"),
                            "longitude": point.get("longitude"),
                            "latitude": point.get("latitude"),
                            "speed": point.get("speed"),
                            "heading": point.get("heading"),
                            "is_valid": point.get("is_valid"),
                            "source_file": point.get("source_file"),
                            "road_id": point.get("road_id"),
                            "road_name": point.get("road_name"),
                            "distance_to_road": point.get("distance_to_road"),
                            "matched": point.get("matched")
                        }
                        corrected_data.append(row)
                    
                    corrected_plate_count += 1
                    print(f"  已添加车辆 {plate_number} 的修正轨迹数据，共 {len(trajectory_points)} 个轨迹点")
                    break  # 找到后跳出循环
        
        # 写入CSV文件
        if original_data:
            df = pd.DataFrame(original_data)
            df.to_csv(original_csv_file, index=False, encoding='utf-8')
            print(f"\n原始轨迹数据已成功导出到 {original_csv_file}")
            print(f"总共导出了 {len(plate_list)} 辆车的原始轨迹数据")
            print(f"总共导出了 {len(original_data)} 个原始轨迹点")
        else:
            print("没有找到任何原始轨迹数据")
            
        if corrected_data:
            df = pd.DataFrame(corrected_data)
            df.to_csv(corrected_csv_file, index=False, encoding='utf-8')
            print(f"\n修正轨迹数据已成功导出到 {corrected_csv_file}")
            print(f"总共导出了 {corrected_plate_count} 辆车的修正轨迹数据")
            print(f"总共导出了 {len(corrected_data)} 个修正轨迹点")
        else:
            print("没有找到任何修正轨迹数据")
        
        elapsed_time = time.time() - start_time
        print(f"\n耗时: {elapsed_time:.2f} 秒")
        
    except Exception as e:
        print(f"导出数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if client:
            client.close()

if __name__ == "__main__":
    print("导出前100条轨迹样本数据到CSV文件")
    print("将同时导出原始轨迹和对应的修正轨迹，保证顺序一致\n")
    
    export_sample_trajectories_to_csv()