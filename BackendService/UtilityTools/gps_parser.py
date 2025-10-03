"""
GPS数据解析工具（优化版）
- 支持多文件并行解析
- 边解析边批量写入 MongoDB
- 低内存占用，适合海量数据
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, BulkWriteError
import glob  # 用于文件匹配

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 线程锁（用于日志和共享状态）
thread_lock = threading.Lock()


class GPSDataParser:
    """GPS数据解析器（优化版）"""

    def __init__(self, max_workers: int = 4):
        # 项目根目录：从当前文件向上三级（假设在 backend/service/gps_parser.py）
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.max_workers = max_workers
        self.batch_size = 1000  # MongoDB 批量插入大小
        self.total_processed = 0
        self.total_inserted = 0
        self.stats_lock = threading.Lock()  # 用于统计计数器

    def _parse_line(self, line: str, line_num: int, source_file: str) -> Optional[Dict[str, Any]]:
        """解析单行GPS数据"""
        if not line.strip():
            return None

        try:
            parts = line.strip().split(',')
            if len(parts) != 10:
                logger.debug(f"[{source_file}:{line_num}] 字段数不为10，跳过")
                return None

            date_str = parts[0].strip()
            time_str = parts[1].strip()
            record_type = parts[2].strip()
            plate_number = parts[3].strip()
            longitude = float(parts[4].strip())
            latitude = float(parts[5].strip())
            speed = float(parts[6].strip())
            heading = float(parts[7].strip())
            reserved_field = parts[8].strip()
            location_flag = int(parts[9].strip())


            # 构建时间
            try:
                if len(time_str) == 6:
                    dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                else:
                    dt = datetime.strptime(f"{date_str}00000{time_str}", "%Y%m%d%H%M%S")
            except ValueError:
                logger.debug(f"[{source_file}:{line_num}] 时间格式错误，跳过")
                return None

            return {
                "plate_number": plate_number,
                "datetime": dt,
                "date": date_str,
                "time": time_str,
                "record_type": record_type,
                "location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "speed": speed,
                "heading": heading,
                "reserved_field": reserved_field,
                "location_flag": location_flag,
                "is_valid": location_flag == 1,
                "source_file": os.path.basename(source_file)  # 记录来源文件
            }

        except (ValueError, IndexError) as e:
            logger.debug(f"[{source_file}:{line_num}] 解析失败: {e}")
            return None

    def _parse_file_to_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """解析单个文件，返回文档列表（用于批量插入）"""
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    point = self._parse_line(line, line_num, file_path)
                    if point:
                        documents.append(point)

            logger.info(f"✅ 文件 '{os.path.basename(file_path)}' 解析完成: {len(documents)} 条有效记录")
            return documents

        except Exception as e:
            logger.error(f"❌ 读取文件失败 '{file_path}': {e}")
            return []

    def _insert_batch(self, documents: List[Dict[str, Any]], db_name: str, collection_name: str):
        """批量插入到 MongoDB"""
        if not documents:
            return

        try:
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client[db_name]
            collection = db[collection_name]

            # 确保索引存在
            collection.create_index("plate_number")
            collection.create_index("datetime")
            collection.create_index([("location", "2dsphere")])

            try:
                result = collection.insert_many(documents)
                inserted_count = len(result.inserted_ids)

                with self.stats_lock:
                    self.total_inserted += inserted_count

                logger.debug(f"📥 批量插入 {inserted_count} 条记录")

            except BulkWriteError as bwe:
                logger.warning(f"部分写入失败: {bwe.details}")
            finally:
                client.close()

        except ServerSelectionTimeoutError:
            logger.error("❌ 无法连接到 MongoDB，请检查服务是否启动")
        except Exception as e:
            logger.error(f"❌ 写入MongoDB时出错: {e}")

    def parse_and_save_multiple(
            self,
            file_pattern: str = "data/*/*.txt",
            db_name: str = "MapTools",
            collection_name: str = "gps_points"
    ):
        """
        并行解析多个文件，并流式保存到 MongoDB
        """
        # 获取所有文件
        search_path = os.path.join(self.data_dir, file_pattern)
        file_paths = glob.glob(search_path)

        if not file_paths:
            logger.warning(f"⚠️ 未找到匹配的文件: {search_path}")
            return

        logger.info(f"🔍 发现 {len(file_paths)} 个文件待处理，使用 {self.max_workers} 个线程并行解析...")

        # 重置统计
        self.total_inserted = 0
        self.total_processed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_path = {
                executor.submit(self._parse_file_to_documents, fp): fp
                for fp in file_paths
            }

            batch_buffer = []

            # 收集结果并立即写入
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    docs = future.result()
                    batch_buffer.extend(docs)
                    with self.stats_lock:
                        self.total_processed += len(docs)

                    # 批量写入
                    while len(batch_buffer) >= self.batch_size:
                        self._insert_batch(batch_buffer[:self.batch_size], db_name, collection_name)
                        del batch_buffer[:self.batch_size]

                except Exception as e:
                    logger.error(f"处理文件时异常 '{file_path}': {e}")

            # 写入剩余数据
            if batch_buffer:
                self._insert_batch(batch_buffer, db_name, collection_name)

        logger.info(f"🎉 全部处理完成！")
        logger.info(f"📊 总共解析 {self.total_processed} 条记录，成功插入 {self.total_inserted} 条")

    def parse_single_file(
            self,
            filename: str = "sample-utf.txt",
            db_name: str = "MapTools",
            collection_name: str = "gps_points"
    ):
        """
        解析单个文件并保存到 MongoDB
        """
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return

        logger.info(f"📄 开始解析单个文件: {filename}")
        documents = self._parse_file_to_documents(file_path)
        with self.stats_lock:
            self.total_processed += len(documents)
        self._insert_batch(documents, db_name, collection_name)
        logger.info(f"✅ 单文件 '{filename}' 已保存至 {db_name}.{collection_name}")

    def parse_sample_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        解析示例数据（用于API测试）
        
        Args:
            limit: 返回的数据点数量限制
            
        Returns:
            List[Dict]: GPS点数据列表
        """
        try:
            # 从MongoDB获取数据
            client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)
            db = client["MapTools"]
            
            # 查找修正轨迹集合
            gps_points = []
            for i in range(1, 31):
                collection_name = f"corrected_trajectories_{i:02d}"
                if collection_name in db.list_collection_names():
                    collection = db[collection_name]
                    # 获取第一个有轨迹点的文档
                    doc = collection.find_one({"trajectory_points": {"$exists": True, "$ne": []}})
                    if doc and doc.get("trajectory_points"):
                        trajectory_points = doc.get("trajectory_points", [])
                        # 限制数量
                        if limit and limit > 0:
                            trajectory_points = trajectory_points[:limit]
                        
                        for j, point in enumerate(trajectory_points):
                            gps_point = {
                                'id': j + 1,
                                'plate_number': doc.get('plate_number', ''),
                                'datetime': point.get('datetime', ''),
                                'longitude': float(point.get('longitude', 0)),
                                'latitude': float(point.get('latitude', 0)),
                                'speed': float(point.get('speed', 0)),
                                'heading': float(point.get('heading', 0)),
                                'is_valid': point.get('is_valid', True)
                            }
                            gps_points.append(gps_point)
                        
                        if gps_points:  # 找到数据就退出
                            break
            
            client.close()
            logger.info(f"从MongoDB获取了 {len(gps_points)} 个GPS点")
            return gps_points
            
        except Exception as e:
            logger.error(f"解析示例数据失败: {e}")
            return []

    def filter_valid_points(self, gps_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤有效的GPS点
        
        Args:
            gps_points: GPS点列表
            
        Returns:
            List[Dict]: 过滤后的有效GPS点列表
        """
        return [point for point in gps_points if point.get('is_valid', False)]


# ======================
# 测试函数
# ======================
def test_parser():
    """测试解析器功能"""
    parser = GPSDataParser(max_workers=4)

    # ✅ 测试：解析并保存单个文件
    parser.parse_single_file(
        filename="sample-utf.txt",
        db_name="MapTools",
        collection_name="gps_points"
    )

    # ✅ 测试：解析多个文件（取消注释使用）
    # parser.parse_and_save_multiple(
    #     file_pattern="data/**/*.txt",  # 支持递归匹配
    #     db_name="MapTools",
    #     collection_name="gps_points"
    # )


if __name__ == "__main__":
    test_parser()