package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;

import java.util.ArrayList;
import java.util.List;

/**
 * MongoDB索引管理器
 * 用于检查和创建必要的索引以提升查询性能
 */
public class MongoIndexManager {
    
    private static final String MONGO_CONNECTION_STRING = "mongodb://localhost:27017";
    private static final String DATABASE_NAME = "MapTools";
    
    private MongoClient mongoClient;
    private MongoDatabase database;
    
    public MongoIndexManager() {
        this.mongoClient = new MongoClient(new MongoClientURI(MONGO_CONNECTION_STRING));
        this.database = mongoClient.getDatabase(DATABASE_NAME);
    }
    
    /**
     * 检查集合的索引情况
     */
    public void checkIndexes() {
        System.out.println("=== 检查MongoDB索引情况 ===");
        
        // 检查GPS点集合的索引
        for (int i = 1; i <= 30; i++) {
            String collectionName = "gps_points_" + String.format("%02d", i);
            checkCollectionIndexes(collectionName);
        }
        
        // 检查轨迹集合的索引
        for (int i = 1; i <= 30; i++) {
            String collectionName = "original_trajectories_" + String.format("%02d", i);
            checkCollectionIndexes(collectionName);
        }
    }
    
    /**
     * 检查单个集合的索引
     */
    private void checkCollectionIndexes(String collectionName) {
        try {
            MongoCollection<Document> collection = database.getCollection(collectionName);
            
            // 检查集合是否存在
            if (!database.listCollectionNames().into(new ArrayList<>()).contains(collectionName)) {
                System.out.println("集合 " + collectionName + " 不存在");
                return;
            }
            
            System.out.println("\n集合 " + collectionName + " 的索引:");
            List<Document> indexes = collection.listIndexes().into(new ArrayList<>());
            
            if (indexes.isEmpty()) {
                System.out.println("  无索引");
            } else {
                for (Document index : indexes) {
                    System.out.println("  - " + index.getString("name") + ": " + index.get("key"));
                }
            }
            
        } catch (Exception e) {
            System.err.println("检查集合 " + collectionName + " 索引时出错: " + e.getMessage());
        }
    }
    
    /**
     * 创建必要的索引
     */
    public void createIndexes() {
        System.out.println("\n=== 创建MongoDB索引 ===");
        
        // 为GPS点集合创建plate_number索引
        for (int i = 1; i <= 30; i++) {
            String collectionName = "gps_points_" + String.format("%02d", i);
            createPlateNumberIndex(collectionName);
        }
        
        // 为轨迹集合创建复合索引
        for (int i = 1; i <= 30; i++) {
            String collectionName = "original_trajectories_" + String.format("%02d", i);
            createTrajectoryIndexes(collectionName);
        }
    }
    
    /**
     * 为GPS点集合创建plate_number索引
     */
    private void createPlateNumberIndex(String collectionName) {
        try {
            MongoCollection<Document> collection = database.getCollection(collectionName);
            
            // 检查集合是否存在
            if (!database.listCollectionNames().into(new ArrayList<>()).contains(collectionName)) {
                return;
            }
            
            // 检查索引是否已存在
            boolean indexExists = false;
            for (Document index : collection.listIndexes()) {
                if (index.get("name").equals("plate_number_1")) {
                    indexExists = true;
                    break;
                }
            }
            
            if (!indexExists) {
                collection.createIndex(new Document("plate_number", 1));
                System.out.println("✅ 为集合 " + collectionName + " 创建了plate_number索引");
            } else {
                System.out.println("⏭️  集合 " + collectionName + " 的plate_number索引已存在");
            }
            
        } catch (Exception e) {
            System.err.println("❌ 为集合 " + collectionName + " 创建索引时出错: " + e.getMessage());
        }
    }
    
    /**
     * 为轨迹集合创建索引
     */
    private void createTrajectoryIndexes(String collectionName) {
        try {
            MongoCollection<Document> collection = database.getCollection(collectionName);
            
            // 检查集合是否存在
            if (!database.listCollectionNames().into(new ArrayList<>()).contains(collectionName)) {
                return;
            }
            
            // 创建复合索引 (plate_number + type)
            boolean compoundIndexExists = false;
            for (Document index : collection.listIndexes()) {
                if (index.get("name").equals("plate_number_1_type_1")) {
                    compoundIndexExists = true;
                    break;
                }
            }
            
            if (!compoundIndexExists) {
                collection.createIndex(new Document("plate_number", 1).append("type", 1));
                System.out.println("✅ 为集合 " + collectionName + " 创建了复合索引");
            } else {
                System.out.println("⏭️  集合 " + collectionName + " 的复合索引已存在");
            }
            
        } catch (Exception e) {
            System.err.println("❌ 为集合 " + collectionName + " 创建索引时出错: " + e.getMessage());
        }
    }
    
    /**
     * 获取集合统计信息
     */
    public void getCollectionStats() {
        System.out.println("\n=== 集合统计信息 ===");
        
        for (int i = 1; i <= 30; i++) {
            String collectionName = "gps_points_" + String.format("%02d", i);
            try {
                MongoCollection<Document> collection = database.getCollection(collectionName);
                
                if (database.listCollectionNames().into(new ArrayList<>()).contains(collectionName)) {
                    long count = collection.countDocuments();
                    System.out.println("集合 " + collectionName + ": " + count + " 个文档");
                }
            } catch (Exception e) {
                System.err.println("获取集合 " + collectionName + " 统计信息时出错: " + e.getMessage());
            }
        }
    }
    
    /**
     * 关闭连接
     */
    public void close() {
        if (mongoClient != null) {
            mongoClient.close();
        }
    }
    
    /**
     * 主方法
     */
    public static void main(String[] args) {
        MongoIndexManager manager = new MongoIndexManager();
        
        try {
            // 检查现有索引
            manager.checkIndexes();
            
            // 获取统计信息
            manager.getCollectionStats();
            
            // 创建索引
            manager.createIndexes();
            
            System.out.println("\n✅ 索引管理完成！");
            
        } catch (Exception e) {
            System.err.println("索引管理过程中出错: " + e.getMessage());
            e.printStackTrace();
        } finally {
            manager.close();
        }
    }
}
