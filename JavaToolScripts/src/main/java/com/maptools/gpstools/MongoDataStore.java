package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.time.ZoneOffset;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

public class MongoDataStore {
    private MongoClient mongoClient;
    private MongoDatabase database;
    private PrintWriter logWriter;
    private AtomicInteger totalInserted;
    private AtomicInteger totalSkipped;
    
    public MongoDataStore(String connectionString, String dbName) {
        this.mongoClient = new MongoClient(new MongoClientURI(connectionString));
        this.database = mongoClient.getDatabase(dbName);
        this.totalInserted = new AtomicInteger(0);
        this.totalSkipped = new AtomicInteger(0);
        
        try {
            // 创建日志文件写入器
            this.logWriter = new PrintWriter(new FileWriter("logs/invalid_data.log", true));
        } catch (IOException e) {
            System.err.println("无法创建日志文件: " + e.getMessage());
            this.logWriter = null;
        }
    }
    
    public void saveGPSPoints(List<GPSDataPoint> points, String collectionName, String fileName) {
        MongoCollection<Document> collection = database.getCollection(collectionName);
        
        // 只在第一次保存时创建索引
        if (totalInserted.get() == 0) {
            synchronized (this) {
                // 再次检查确保只创建一次
                if (totalInserted.get() == 0) {
                    // 创建索引
                    collection.createIndex(new Document("plate_number", 1));
                    collection.createIndex(new Document("datetime", 1));
                    // 为地理空间查询创建索引
                    collection.createIndex(new Document("location", "2dsphere"));
                }
            }
        }
        
        int batchSize = 1000;
        int fileInserted = 0;
        int fileSkipped = 0;
        
        // 分批插入
        for (int i = 0; i < points.size(); i += batchSize) {
            int end = Math.min(i + batchSize, points.size());
            List<GPSDataPoint> batch = points.subList(i, end);
            
            List<Document> documents = new java.util.ArrayList<>();
            for (GPSDataPoint point : batch) {
                // 验证经纬度数据是否有效
                if (!isValidCoordinate(point.getLongitude(), point.getLatitude())) {
                    // 将无效数据信息写入日志文件而不是终端
                    synchronized (this) {
                        if (logWriter != null) {
                            logWriter.println("警告: 跳过无效坐标数据 - 经度: " + point.getLongitude() + 
                                             ", 纬度: " + point.getLatitude() + 
                                             ", 车牌号: " + point.getPlateNumber() +
                                             ", 时间: " + point.getDate() + " " + point.getTime() +
                                             ", 文件: " + fileName);
                            logWriter.flush();
                        }
                    }
                    fileSkipped++;
                    totalSkipped.incrementAndGet();
                    continue;
                }
                
                Document doc = new Document()
                    .append("plate_number", point.getPlateNumber())
                    .append("datetime", point.getDatetime().atOffset(ZoneOffset.UTC).toInstant().toEpochMilli())
                    .append("date", point.getDate())
                    .append("time", point.getTime())
                    .append("record_type", point.getRecordType())
                    .append("location", new Document()
                        .append("type", "Point")
                        .append("coordinates", java.util.Arrays.asList(point.getLongitude(), point.getLatitude())))
                    .append("speed", point.getSpeed())
                    .append("heading", point.getHeading())
                    .append("reserved_field", point.getReservedField())
                    .append("location_flag", point.getLocationFlag())
                    .append("is_valid", point.isValid())
                    .append("source_file", fileName);
                    
                documents.add(doc);
            }
            
            if (!documents.isEmpty()) {
                collection.insertMany(documents);
                fileInserted += documents.size();
                totalInserted.addAndGet(documents.size());
            }
        }
        
        System.out.println("文件 " + fileName + " 成功保存 " + fileInserted + " 条记录，跳过 " + fileSkipped + " 条无效记录");
    }
    
    /**
     * 验证经纬度坐标是否有效
     * @param longitude 经度
     * @param latitude 纬度
     * @return 坐标是否有效
     */
    private boolean isValidCoordinate(double longitude, double latitude) {
        // 检查经度是否在有效范围内 (-180 到 180)
        if (longitude < -180 || longitude > 180) {
            return false;
        }
        
        // 检查纬度是否在有效范围内 (-90 到 90)
        if (latitude < -90 || latitude > 90) {
            return false;
        }
        
        return true;
    }
    
    public void printSummary() {
        System.out.println("总共保存 " + totalInserted.get() + " 条记录");
        System.out.println("总共跳过 " + totalSkipped.get() + " 条无效记录");
    }
    
    public void close() {
        if (mongoClient != null) {
            mongoClient.close();
        }
        
        // 关闭日志文件写入器
        if (logWriter != null) {
            logWriter.close();
        }
    }
}