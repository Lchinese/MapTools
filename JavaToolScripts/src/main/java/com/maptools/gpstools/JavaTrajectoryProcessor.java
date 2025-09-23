package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Indexes;
import org.bson.Document;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.LineString;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Java轨迹处理器 - 完全重写，参照Python数据结构
 * 支持多线程处理，避免重复存储，修复类型转换问题
 */
public class JavaTrajectoryProcessor {
    
    private static final String MONGO_CONNECTION_STRING = "mongodb://localhost:27017";
    private static final String DATABASE_NAME = "MapTools";
    private static final int THREAD_POOL_SIZE = 20;
    private static final int BATCH_SIZE = 1000;
    
    private MongoClient mongoClient;
    private MongoDatabase database;
    private ExecutorService executor;
    private JavaRoadMatcher roadMatcher;
    private GeometryFactory geometryFactory;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSaved = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    
    public JavaTrajectoryProcessor() {
        this.mongoClient = new MongoClient(new MongoClientURI(MONGO_CONNECTION_STRING));
        this.database = mongoClient.getDatabase(DATABASE_NAME);
        this.executor = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        this.geometryFactory = new GeometryFactory();
        
        // 初始化道路匹配器
        try {
            this.roadMatcher = new JavaRoadMatcher();
            System.out.println("道路匹配器初始化成功");
        } catch (Exception e) {
            System.err.println("道路匹配器初始化失败: " + e.getMessage());
            this.roadMatcher = null;
        }
    }
    
    /**
     * 处理所有GPS点集合，转换为轨迹数据
     */
    public void processAllCollections(boolean matchToRoads) {
        System.out.println("🚀 开始处理所有GPS点集合...");
        
        try {
            // 处理01到30的所有集合
            for (int i = 1; i <= 30; i++) {
                String collectionSuffix = String.format("%02d", i);
                String sourceCollectionName = "gps_points_" + collectionSuffix;
                String targetCollectionName = "original_trajectories_" + collectionSuffix;
                
                System.out.println("处理集合: " + sourceCollectionName + " -> " + targetCollectionName);
                
                // 检查源集合是否存在
                if (!database.listCollectionNames().into(new ArrayList<>()).contains(sourceCollectionName)) {
                    System.out.println("源集合 " + sourceCollectionName + " 不存在，跳过");
                    continue;
                }
                
                processCollection(sourceCollectionName, targetCollectionName, matchToRoads);
            }
            
            // 等待所有任务完成
            System.out.println("等待所有集合处理完成...");
            executor.shutdown();
            try {
                if (!executor.awaitTermination(60, TimeUnit.MINUTES)) {
                    System.out.println("强制关闭线程池...");
                    executor.shutdownNow();
                }
            } catch (InterruptedException e) {
                System.out.println("线程池等待被中断");
                executor.shutdownNow();
                Thread.currentThread().interrupt();
            }
            
            // 打印最终统计
            printFinalStats();
            
        } catch (Exception e) {
            System.err.println("处理过程中出错: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (roadMatcher != null) {
                roadMatcher.close();
            }
            if (mongoClient != null) {
                mongoClient.close();
            }
        }
    }
    
    /**
     * 处理单个集合
     */
    private void processCollection(String sourceCollectionName, String targetCollectionName, boolean matchToRoads) {
        MongoCollection<Document> sourceCollection = database.getCollection(sourceCollectionName);
        MongoCollection<Document> targetCollection = database.getCollection(targetCollectionName);
        
        // 检查源集合中的文档数量
        long sourceCount = sourceCollection.countDocuments();
        System.out.println("源集合 " + sourceCollectionName + " 共有 " + sourceCount + " 个GPS点");
        
        // 获取所有车牌号
        List<String> allPlates = sourceCollection.distinct("plate_number", String.class).into(new ArrayList<>());
        System.out.println("找到 " + allPlates.size() + " 个车牌号，开始处理...");
        
        // 检查已存在的车牌号，避免重复存储
        String trajectoryType = matchToRoads ? "matched_trajectory" : "original_trajectory";
        Set<String> existingPlates = new HashSet<>();
        targetCollection.find(Filters.eq("type", trajectoryType))
                .projection(new Document("plate_number", 1))
                .into(new ArrayList<>())
                .forEach(doc -> existingPlates.add(doc.getString("plate_number")));
        
        System.out.println("已存在 " + existingPlates.size() + " 个车牌号的轨迹数据");
        
        // 过滤掉已存在的车牌号
        List<String> platesToProcess = new ArrayList<>();
        for (String plateNumber : allPlates) {
            if (!existingPlates.contains(plateNumber)) {
                platesToProcess.add(plateNumber);
            }
        }
        
        System.out.println("需要处理 " + platesToProcess.size() + " 个车牌号（跳过 " + (allPlates.size() - platesToProcess.size()) + " 个已存在的）");
        
        // 如果所有车牌都已存在，直接返回
        if (platesToProcess.isEmpty()) {
            System.out.println("所有车牌号都已存在，跳过处理");
            return;
        }
        
        // 使用多线程处理车牌号
        processPlatesMultithreaded(platesToProcess, sourceCollection, targetCollection, 
                                 matchToRoads, sourceCollectionName, trajectoryType);
        
        System.out.println("集合 " + sourceCollectionName + " 处理完成");
    }
    
    /**
     * 多线程处理车牌号列表
     */
    private void processPlatesMultithreaded(List<String> platesToProcess, 
                                          MongoCollection<Document> sourceCollection,
                                          MongoCollection<Document> targetCollection,
                                          boolean matchToRoads, 
                                          String sourceCollectionName,
                                          String trajectoryType) {
        
        System.out.println("开始多线程处理 " + platesToProcess.size() + " 个车牌号，使用 " + THREAD_POOL_SIZE + " 个线程");
        
        AtomicInteger processedPlates = new AtomicInteger(0);
        AtomicInteger savedCount = new AtomicInteger(0);
        AtomicInteger skippedCount = new AtomicInteger(0);
        
        // 收集所有Future对象
        List<Future<?>> futures = new ArrayList<>();
        
        for (String plateNumber : platesToProcess) {
            Future<?> future = executor.submit(() -> {
                try {
                    processPlateNumber(plateNumber, sourceCollection, targetCollection, 
                                    matchToRoads, sourceCollectionName, trajectoryType);
                    savedCount.incrementAndGet();
                } catch (Exception e) {
                    System.err.println("处理车牌号 " + plateNumber + " 时出错: " + e.getMessage());
                } finally {
                    int processed = processedPlates.incrementAndGet();
                    if (processed % 100 == 0) {
                        System.out.println("进度: " + processed + "/" + platesToProcess.size() + 
                                         " | 已保存: " + savedCount.get() + " | 跳过: " + skippedCount.get());
                    }
                }
            });
            futures.add(future);
        }
        
        // 等待当前集合的所有任务完成
        System.out.println("等待集合 " + sourceCollectionName + " 的所有任务完成...");
        try {
            // 等待所有Future完成
            for (Future<?> future : futures) {
                future.get(); // 等待单个任务完成
            }
            
            System.out.println("进度: " + processedPlates.get() + "/" + platesToProcess.size() + 
                             " | 已保存: " + savedCount.get() + " | 跳过: " + skippedCount.get());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.out.println("等待被中断");
        } catch (Exception e) {
            System.err.println("等待任务完成时出错: " + e.getMessage());
        }
        
        System.out.println("集合 " + sourceCollectionName + " 多线程处理完成: 处理了 " + processedPlates.get() + " 个车牌");
    }
    
    /**
     * 处理单个车牌号的轨迹数据
     */
    private void processPlateNumber(String plateNumber, MongoCollection<Document> sourceCollection, 
                                  MongoCollection<Document> targetCollection, boolean matchToRoads, 
                                  String sourceCollectionName, String trajectoryType) {
        
        // 双重检查：再次确认该车牌号不存在，避免并发重复插入
        Document existingDoc = targetCollection.find(
            Filters.and(
                Filters.eq("plate_number", plateNumber),
                Filters.eq("type", trajectoryType)
            )
        ).first();
        
        if (existingDoc != null) {
            // 该车牌号已存在，跳过处理
            return;
        }
        
        // 查询该车牌号的所有GPS点
        List<Document> gpsPoints = sourceCollection.find(Filters.eq("plate_number", plateNumber))
                .sort(new Document("datetime", 1))
                .into(new ArrayList<>());
        
        if (gpsPoints.isEmpty()) {
            return;
        }
        
        // 转换为轨迹点格式
        List<Map<String, Object>> trajectoryPoints = new ArrayList<>();
        
        for (Document point : gpsPoints) {
            Map<String, Object> trajectoryPoint = new HashMap<>();
            trajectoryPoint.put("plate_number", point.getString("plate_number"));
            
            // 处理datetime字段，保持与Python一致
            Object datetimeObj = point.get("datetime");
            if (datetimeObj instanceof java.time.Instant) {
                trajectoryPoint.put("datetime", ((java.time.Instant) datetimeObj).toString());
            } else {
                trajectoryPoint.put("datetime", datetimeObj);
            }
            
            // 经纬度保持Double类型，与Python一致 - 使用安全的类型转换
            Document location = point.get("location", Document.class);
            @SuppressWarnings("unchecked")
            List<Number> coordinates = (List<Number>) location.get("coordinates");
            trajectoryPoint.put("longitude", coordinates.get(0).doubleValue());
            trajectoryPoint.put("latitude", coordinates.get(1).doubleValue());
            
            // speed和heading保持原始类型，与Python一致
            Object speedObj = point.get("speed");
            Object headingObj = point.get("heading");
            
            // 安全处理数值类型，保持与Python一致
            if (speedObj != null) {
                trajectoryPoint.put("speed", speedObj);
            } else {
                trajectoryPoint.put("speed", 0.0); // 使用Double类型的默认值
            }
            
            if (headingObj != null) {
                trajectoryPoint.put("heading", headingObj);
            } else {
                trajectoryPoint.put("heading", 0.0); // 使用Double类型的默认值
            }
            trajectoryPoint.put("is_valid", point.getBoolean("is_valid", false));
            
            // 安全获取source_file字段
            String sourceFile = point.getString("source_file");
            trajectoryPoint.put("source_file", sourceFile != null ? sourceFile : "");
            
            trajectoryPoints.add(trajectoryPoint);
        }
        
        // 如果需要进行道路匹配
        if (matchToRoads && roadMatcher != null) {
            try {
                trajectoryPoints = performRoadMatching(trajectoryPoints);
            } catch (Exception e) {
                System.err.println("道路匹配失败 " + plateNumber + ": " + e.getMessage());
                return;
            }
        }
        
        // 创建轨迹文档
        Document trajectoryDoc = createTrajectoryDocument(plateNumber, trajectoryPoints, matchToRoads, sourceCollectionName);
        
        if (trajectoryDoc == null) {
            return;
        }
        
        // 使用upsert操作确保不重复插入
        Document filter = new Document()
                .append("plate_number", plateNumber)
                .append("type", trajectoryType);
        
        try {
            // 先尝试插入，如果已存在则跳过
            targetCollection.insertOne(trajectoryDoc);
            totalProcessed.incrementAndGet();
            totalSaved.incrementAndGet();
        } catch (com.mongodb.MongoWriteException e) {
            // 如果是重复键错误，说明数据已存在，跳过
            if (e.getError().getCode() == 11000) {
                // 重复键错误，数据已存在，跳过
                return;
            } else {
                // 其他错误，重新抛出
                throw e;
            }
        }
    }
    
    /**
     * 执行道路匹配
     */
    private List<Map<String, Object>> performRoadMatching(List<Map<String, Object>> trajectoryPoints) {
        List<Map<String, Object>> matchedPoints = new ArrayList<>();
        
        for (Map<String, Object> point : trajectoryPoints) {
            // 安全获取经纬度，处理类型转换
            Object lonObj = point.get("longitude");
            Object latObj = point.get("latitude");
            
            double longitude, latitude;
            if (lonObj instanceof Double) {
                longitude = (Double) lonObj;
            } else if (lonObj instanceof Integer) {
                longitude = ((Integer) lonObj).doubleValue();
            } else if (lonObj instanceof Number) {
                longitude = ((Number) lonObj).doubleValue();
            } else {
                longitude = 0.0;
            }
            
            if (latObj instanceof Double) {
                latitude = (Double) latObj;
            } else if (latObj instanceof Integer) {
                latitude = ((Integer) latObj).doubleValue();
            } else if (latObj instanceof Number) {
                latitude = ((Number) latObj).doubleValue();
            } else {
                latitude = 0.0;
            }
            
            // 使用道路匹配器进行匹配
            Map<String, Object> matchResult = roadMatcher.findClosestRoad(longitude, latitude);
            
            Map<String, Object> matchedPoint = new HashMap<>(point);
            matchedPoint.put("longitude", matchResult.get("matched_longitude"));
            matchedPoint.put("latitude", matchResult.get("matched_latitude"));
            matchedPoint.put("road_id", matchResult.get("road_id"));
            matchedPoint.put("road_name", matchResult.get("road_name"));
            matchedPoint.put("road_type", matchResult.get("road_type"));
            matchedPoint.put("distance_to_road", matchResult.get("distance_to_road"));
            matchedPoint.put("matched", true);
            
            matchedPoints.add(matchedPoint);
        }
        
        return matchedPoints;
    }
    
    /**
     * 创建轨迹文档
     */
    private Document createTrajectoryDocument(String plateNumber, List<Map<String, Object>> trajectoryPoints, 
                                            boolean matchToRoads, String sourceCollectionName) {
        if (trajectoryPoints.isEmpty()) {
            return null;
        }
        
        // 计算边界框
        double minLon = Double.MAX_VALUE, maxLon = Double.MIN_VALUE;
        double minLat = Double.MAX_VALUE, maxLat = Double.MIN_VALUE;
        
        for (Map<String, Object> point : trajectoryPoints) {
            // 安全获取经纬度，处理类型转换
            Object lonObj = point.get("longitude");
            Object latObj = point.get("latitude");
            
            double lon, lat;
            if (lonObj instanceof Double) {
                lon = (Double) lonObj;
            } else if (lonObj instanceof Integer) {
                lon = ((Integer) lonObj).doubleValue();
            } else if (lonObj instanceof Number) {
                lon = ((Number) lonObj).doubleValue();
            } else {
                lon = 0.0;
            }
            
            if (latObj instanceof Double) {
                lat = (Double) latObj;
            } else if (latObj instanceof Integer) {
                lat = ((Integer) latObj).doubleValue();
            } else if (latObj instanceof Number) {
                lat = ((Number) latObj).doubleValue();
            } else {
                lat = 0.0;
            }
            
            minLon = Math.min(minLon, lon);
            maxLon = Math.max(maxLon, lon);
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
        }
        
        Document bbox = new Document()
                .append("min_lon", minLon)
                .append("max_lon", maxLon)
                .append("min_lat", minLat)
                .append("max_lat", maxLat);
        
        Map<String, Object> firstPoint = trajectoryPoints.get(0);
        Map<String, Object> lastPoint = trajectoryPoints.get(trajectoryPoints.size() - 1);
        
        Document timeRange = new Document()
                .append("start", firstPoint.get("datetime"))
                .append("end", lastPoint.get("datetime"));
        
        return new Document()
                .append("plate_number", plateNumber)
                .append("trajectory_points", trajectoryPoints)
                .append("point_count", trajectoryPoints.size())
                .append("first_point", firstPoint)
                .append("last_point", lastPoint)
                .append("time_range", timeRange)
                .append("bbox", bbox)
                .append("source", sourceCollectionName)
                .append("created_at", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME))
                .append("type", matchToRoads ? "matched_trajectory" : "original_trajectory");
    }
    
    /**
     * 打印最终统计信息
     */
    private void printFinalStats() {
        System.out.println("\n=== 处理完成统计 ===");
        System.out.println("总处理车牌数: " + totalProcessed.get());
        System.out.println("总保存轨迹数: " + totalSaved.get());
        System.out.println("总跳过车牌数: " + totalSkipped.get());
        System.out.println("✅ 所有轨迹数据处理完成！");
    }
    
    /**
     * 主方法
     */
    public static void main(String[] args) {
        boolean matchToRoads = true; // 默认进行道路匹配
        
        if (args.length > 0) {
            matchToRoads = Boolean.parseBoolean(args[0]);
        }
        
        System.out.println("Java轨迹处理器启动，道路匹配: " + matchToRoads);
        
        JavaTrajectoryProcessor processor = new JavaTrajectoryProcessor();
        processor.processAllCollections(matchToRoads);
    }
}
