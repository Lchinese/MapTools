import pymongo
import pandas as pd
import json
from datetime import datetime
import time
import os

def connect_to_mongodb():
    """连接到MongoDB数据库"""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["MapTools"]
        return client, db
    except Exception as e:
        print(f"连接MongoDB失败: {e}")
        return None, None

def export_corrected_trajectories_to_csv():
    """导出修正后的轨迹数据到CSV文件"""
    # 连接MongoDB
    client, db = connect_to_mongodb()
    if not client or db is None:
        return
    
    try:
        # 使用CSV文件格式
        csv_file = "corrected_trajectories.csv"
        
        # 如果CSV文件已存在，先删除它
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"已删除已存在的 {csv_file} 文件")
        
        # 记录开始时间
        start_time = time.time()
        
        # 处理每个修正后的轨迹集合
        total_points = 0
        first_batch = True
        
        # 用于分批写入的计数器
        batch_size = 10000  # 每10000条记录写入一次
        batch_data = []
        
        for i in range(1, 31):
            collection_name = f"corrected_trajectories_{i:02d}"
            collection = db[collection_name]
            
            print(f"正在处理集合: {collection_name}")
            
            # 检查集合是否存在且有数据
            doc_count = collection.count_documents({})
            if doc_count == 0:
                print(f"集合 {collection_name} 为空或不存在，跳过")
                continue
            
            print(f"集合 {collection_name} 包含 {doc_count} 个文档")
            
            # 使用流式查询处理大量数据
            cursor = collection.find({})
            doc_counter = 0
            
            for trajectory_doc in cursor:
                doc_counter += 1
                plate_number = trajectory_doc.get("plate_number", f"unknown_{doc_counter}")
                
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
                        "road_id": point.get("road_id"),
                        "distance_to_road": point.get("distance_to_road"),
                        "accuracy": point.get("accuracy")
                    }
                    # 添加重匹配相关信息
                    if "rematch_method" in point:
                        row["rematch_method"] = point.get("rematch_method")
                        row["rematch_score"] = point.get("rematch_score")
                    
                    batch_data.append(row)
                
                total_points += len(trajectory_points)
                
                # 每处理10个文档显示一次进度
                if doc_counter % 10 == 0:
                    print(f"  集合 {collection_name} 已处理 {doc_counter} 个文档")
                
                # 达到批次大小时写入数据
                if len(batch_data) >= batch_size:
                    write_data_to_csv(csv_file, batch_data, first_write=first_batch)
                    print(f"  已写入 {len(batch_data)} 条记录到CSV文件")
                    batch_data = []  # 清空已写入的数据
                    first_batch = False
        
        # 写入剩余数据
        if batch_data:
            write_data_to_csv(csv_file, batch_data, first_write=first_batch)
            print(f"  已写入 {len(batch_data)} 条记录到CSV文件")
        
        elapsed_time = time.time() - start_time
        print(f"\n数据已成功导出到 {csv_file}")
        print(f"总共导出了 {total_points} 个轨迹点")
        print(f"耗时: {elapsed_time:.2f} 秒")
        
    except Exception as e:
        print(f"导出数据时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if client:
            client.close()

def write_data_to_csv(csv_file, data, first_write=True):
    """将数据写入CSV文件"""
    try:
        df = pd.DataFrame(data)
        
        if first_write:
            # 首次写入，创建新文件（包含列标题）
            df.to_csv(csv_file, index=False, encoding='utf-8')
        else:
            # 后续写入，追加数据（不包含列标题）
            df.to_csv(csv_file, mode='a', header=False, index=False)
    except Exception as e:
        print(f"写入CSV文件时出错: {e}")

def export_statistics_to_excel():
    """导出轨迹修正统计信息到Excel文件"""
    # 连接MongoDB
    client, db = connect_to_mongodb()
    if not client or db is None:
        return
    
    try:
        output_file = "trajectory_correction_statistics.xlsx"
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        
        # 收集统计信息
        stats_data = []
        
        # 处理每个修正后的轨迹集合
        for i in range(1, 31):
            source_collection_name = f"original_trajectories_{i:02d}"
            target_collection_name = f"corrected_trajectories_{i:02d}"
            
            source_collection = db[source_collection_name]
            target_collection = db[target_collection_name]
            
            # 检查集合是否存在
            if source_collection.count_documents({}) == 0:
                continue
            
            # 统计信息
            source_count = source_collection.count_documents({})
            target_count = target_collection.count_documents({}) if target_collection.count_documents({}) > 0 else 0
            
            stats_data.append({
                "collection": f"Group {i:02d}",
                "source_trajectories": source_count,
                "corrected_trajectories": target_count,
                "correction_rate": f"{(target_count/source_count*100):.2f}%" if source_count > 0 else "0%"
            })
        
        # 创建统计信息DataFrame并导出
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name="Statistics", index=False)
            print(f"统计信息已导出到 {output_file}")
        
        writer.close()
        
    except Exception as e:
        print(f"导出统计信息时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if client:
            client.close()

if __name__ == "__main__":
    print("MongoDB轨迹数据导出到CSV工具")
    print("1. 导出修正后的轨迹数据到CSV")
    print("2. 导出统计信息到Excel")
    
    try:
        choice = input("请选择导出类型 (1 或 2): ").strip()
    except:
        choice = "1"  # 默认选择导出轨迹数据
    
    if choice == "1":
        export_corrected_trajectories_to_csv()
    elif choice == "2":
        export_statistics_to_excel()
    else:
        print("无效选择，导出修正后的轨迹数据到CSV...")
        export_corrected_trajectories_to_csv()