#!/usr/bin/env python3
"""
测试GPS数据解析性能的脚本
用于测试解析data/01目录中文件的性能
"""

import time
import os
import sys
import pymongo

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以从UtilityTools导入gps_parser
from UtilityTools.gps_parser import GPSDataParser

def get_parsed_files():
    """获取已经解析过的文件列表"""
    try:
        client = pymongo.MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
        db = client['MapTools']
        collection = db['gps_points']
        
        # 获取所有已解析的文件名
        parsed_files = set(collection.distinct("source_file"))
        client.close()
        return parsed_files
    except Exception as e:
        print(f"获取已解析文件列表失败: {e}")
        return set()

def test_parsing_performance():
    """
    测试解析data/01目录中文件的性能（跳过已解析的文件）
    """
    # 获取已解析的文件列表
    print("检查已解析的文件...")
    parsed_files = get_parsed_files()
    print(f"已解析文件数量: {len(parsed_files)}")
    
    # 创建GPS数据解析器实例
    parser = GPSDataParser(max_workers=12)
    
    # 定义要测试的文件模式
    file_pattern = "data/01/*.txt"
    
    # 获取所有文件
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "01")
    all_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    
    # 过滤出未解析的文件
    unparsed_files = [f for f in all_files if f not in parsed_files]
    
    print(f"总文件数: {len(all_files)}")
    print(f"未解析文件数: {len(unparsed_files)}")
    
    if not unparsed_files:
        print("所有文件都已解析完成！")
        return
    
    print("开始解析未处理的文件...")
    print(f"未解析文件: {unparsed_files[:10]}{'...' if len(unparsed_files) > 10 else ''}")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 只处理未解析的文件
        for filename in unparsed_files:
            print(f"正在处理: {filename}")
            parser.parse_single_file(
                filename=f"data/01/{filename}",
                db_name="MapTools",
                collection_name="gps_points"
            )
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算耗时
        elapsed_time = end_time - start_time
        
        print(f"\n解析完成!")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"平均处理速度: {parser.total_processed/elapsed_time:.2f} 条记录/秒")
        print(f"本次处理记录数: {parser.total_processed}")
        print(f"本次成功插入记录数: {parser.total_inserted}")
        print(f"处理文件数: {len(unparsed_files)}")
        
    except Exception as e:
        print(f"解析过程中出现错误: {e}")
        sys.exit(1)

def test_single_file_parsing():
    """
    测试单个文件解析性能
    """
    # 获取data/01目录中的第一个文件
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "01")
    
    if not os.path.exists(data_dir):
        print(f"目录不存在: {data_dir}")
        return
    
    txt_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"在 {data_dir} 目录中未找到txt文件")
        return
    
    # 选择第一个文件进行测试
    test_file = txt_files[0]
    file_path = os.path.join(data_dir, test_file)
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
    
    print(f"开始测试单个文件解析性能...")
    print(f"测试文件: {test_file}")
    print(f"文件大小: {file_size:.2f} MB")
    
    # 创建GPS数据解析器实例
    parser = GPSDataParser(max_workers=12)
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 解析单个文件
        parser.parse_single_file(
            filename=f"data/01/{test_file}",
            db_name="MapTools",
            collection_name="gps_points"
        )
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算耗时
        elapsed_time = end_time - start_time
        
        print(f"\n单文件测试完成!")
        print(f"文件: {test_file}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        print(f"处理速度: {parser.total_processed/elapsed_time:.2f} 条记录/秒")
        print(f"处理记录数: {parser.total_processed}")
        print(f"数据吞吐量: {file_size/elapsed_time:.2f} MB/秒")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        sys.exit(1)

def main():
    """
    主函数
    """
    print("GPS数据解析性能测试")
    print("=" * 50)
    
    # 测试单个文件解析性能
    print("\n1. 单文件解析性能测试")
    print("-" * 30)
    test_single_file_parsing()
    
    # 测试多个文件解析性能
    print("\n2. 多文件解析性能测试")
    print("-" * 30)
    test_parsing_performance()

if __name__ == "__main__":
    main()