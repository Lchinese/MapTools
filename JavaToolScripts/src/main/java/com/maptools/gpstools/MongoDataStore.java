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
import java.nio.file.Files;
import java.nio.file.Paths;

public class MongoDataStore {
    private MongoClient mongoClient;
    private MongoDatabase database;
    private PrintWriter logWriter;
    private PrintWriter summaryWriter;
    private AtomicInteger totalInserted;
    private AtomicInteger totalSkipped;
    private AtomicInteger totalFiltered;
    
    // 使用配置管理器
    private ConfigManager config = ConfigManager.getInstance();
    
    public MongoDataStore() {
        this.mongoClient = new MongoClient(new MongoClientURI(config.getMongoDBConnectionString()));
        this.database = mongoClient.getDatabase(config.getMongoDBDatabaseName());
        this.totalInserted = new AtomicInteger(0);
        this.totalSkipped = new AtomicInteger(0);
        this.totalFiltered = new AtomicInteger(0);
        
        try {
            // 创建日志文件写入器
            String logDir = config.getLogDirectory();
            Files.createDirectories(Paths.get(logDir));
            
            this.logWriter = new PrintWriter(new FileWriter(logDir + "/invalid_data.log", true));
            this.summaryWriter = new PrintWriter(new FileWriter(logDir + "/processing_summary.log", true));
        } catch (IOException e) {
            System.err.println("无法创建日志文件: " + e.getMessage());
            this.logWriter = null;
            this.summaryWriter = null;
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
        int fileTotal = points.size();
        
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
        
        // 记录文件处理摘要
        synchronized (this) {
            if (summaryWriter != null) {
                summaryWriter.println("文件: " + fileName + 
                                    ", 总点数: " + fileTotal + 
                                    ", 插入: " + fileInserted + 
                                    ", 跳过: " + fileSkipped + 
                                    ", 保留: " + (fileTotal - fileSkipped));
                summaryWriter.flush();
            }
        }
    }
    
    /**
     * 验证坐标是否有效
     * 
     * @param longitude 经度
     * @param latitude 纬度
     * @return 如果坐标有效返回true，否则返回false
     */
    private boolean isValidCoordinate(double longitude, double latitude) {
        // 检查经纬度是否在合理范围内
        return (longitude >= -180 && longitude <= 180) && 
               (latitude >= -90 && latitude <= 90) &&
               (longitude != 0.0 || latitude != 0.0); // 排除0,0坐标
    }
    
    /**
     * 打印处理总结
     */
    public void printSummary() {
        int inserted = totalInserted.get();
        int skipped = totalSkipped.get();
        
        System.out.println("\n=== 处理总结 ===");
        System.out.println("成功插入点数: " + inserted);
        System.out.println("跳过无效点数: " + skipped);
        System.out.println("总计处理点数: " + (inserted + skipped));
        
        // 记录到摘要日志
        synchronized (this) {
            if (summaryWriter != null) {
                summaryWriter.println("\n=== 处理总结 ===");
                summaryWriter.println("成功插入点数: " + inserted);
                summaryWriter.println("跳过无效点数: " + skipped);
                summaryWriter.println("总计处理点数: " + (inserted + skipped));
                summaryWriter.println("================\n");
                summaryWriter.flush();
            }
        }
    }
    
    public void close() {
        if (mongoClient != null) {
            mongoClient.close();
        }
        
        // 关闭日志文件写入器
        if (logWriter != null) {
            logWriter.close();
        }
        
        if (summaryWriter != null) {
            summaryWriter.close();
        }
    }
}