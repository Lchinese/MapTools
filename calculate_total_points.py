import pymongo

# 连接到MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['MapTools']

# 计算所有修正轨迹集合中的轨迹点总数
total_points = 0

# 遍历所有可能的修正轨迹集合
for i in range(1, 31):
    collection_name = f'corrected_trajectories_{i:02d}'
    collection = db[collection_name]
    
    # 计算该集合中所有文档的轨迹点数量总和
    # 使用point_count字段，因为它应该包含每个文档中的轨迹点数量
    collection_points = collection.aggregate([
        {'$group': {'_id': None, 'total': {'$sum': '$point_count'}}}
    ])
    
    # 获取聚合结果
    result = list(collection_points)
    if result:
        collection_total = result[0]['total']
        if collection_total > 0:
            print(f'{collection_name}: {collection_total} 个轨迹点')
            total_points += collection_total

print(f'MongoDB中所有修正轨迹集合的轨迹点总数: {total_points}')

client.close()