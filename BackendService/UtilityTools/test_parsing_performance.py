"""
测试GPS数据解析性能的脚本
用于测试解析data/01目录中文件的性能
"""

import time
import os
import sys
from gps_parser import GPSDataParser

def test_parsing_performance():
    """
    测试解析data/01目录中文件的性能
    """
    # 创建GPS数据解析器实例
    parser = GPSDataParser(max_workers=4)
    
    # 定义要测试的文件模式
    file_pattern = "data/01/*.txt"
    
    print("开始测试GPS数据解析性能...")
    print(f"测试文件模式: {file_pattern}")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 解析并保存多个文件
        parser.parse_and_save_multiple(
            file_pattern=file_pattern,
            db_name="MapTools",
            collection_name="gps_points"
        )
        
        # 记录结束时间
        end_time = time.time()
        
        # 计算耗时
        elapsed_time = end_time - start_time
        
        print(f"\n测试完成!")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"平均处理速度: {parser.total_processed/elapsed_time:.2f} 条记录/秒")
        print(f"总共处理记录数: {parser.total_processed}")
        print(f"成功插入记录数: {parser.total_inserted}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
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
    parser = GPSDataParser(max_workers=8)
    
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