package com.maptools.gpstools;

import org.bson.Document;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.FindIterable;
import com.mongodb.MongoWriteException;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;

/**
 * 轨迹修正主处理器
 * 多线程处理轨迹修正任务
 */
public class TrajectoryCorrectionProcessor {
    
    private static final int THREAD_POOL_SIZE = 8;
    private static final int BATCH_SIZE = 100;
    private static final String SOURCE_COLLECTION_PREFIX = "original_trajectories_";
    private static final String TARGET_COLLECTION_PREFIX = "corrected_trajectories_";
    
    private MongoClient mongoClient;
    private MongoDatabase database;
    private ExecutorService executorService;
    private TrajectoryCorrector trajectoryCorrector;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSaved = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalErrors = new AtomicLong(0);
    
    // 内存管理
    private MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
    
    public TrajectoryCorrectionProcessor() {
        this.mongoClient = MongoClients.create("mongodb://localhost:27017");
        this.database = mongoClient.getDatabase("MapTools");
        this.executorService = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        this.trajectoryCorrector = new TrajectoryCorrector();
    }
    
    /**
     * 主处理方法
     */
    public void processTrajectoryCorrection(boolean skipExisting) {
        System.out.println("==================================================");
        System.out.println("轨迹修正处理开始");
        System.out.println("==================================================");
        
        long startTime = System.currentTimeMillis();
        
        try {
            // Process each original trajectory collection
            for (int i = 1; i <= 30; i++) {
                String sourceCollectionName = SOURCE_COLLECTION_PREFIX + String.format("%02d", i);
                String targetCollectionName = TARGET_COLLECTION_PREFIX + String.format("%02d", i);
                
                if (database.getCollection(sourceCollectionName).countDocuments() > 0) {
                    System.out.println("\n处理集合: " + sourceCollectionName + " -> " + targetCollectionName);
                    processCollection(sourceCollectionName, targetCollectionName, skipExisting);
                }
            }
            
        } catch (Exception e) {
            System.err.println("处理失败: " + e.getMessage());
            e.printStackTrace();
        } finally {
            executorService.shutdown();
            trajectoryCorrector.close();
            mongoClient.close();
        }
        
        long endTime = System.currentTimeMillis();
        long duration = endTime - startTime;
        
        printFinalStats(duration);
    }
    
    /**
     * 处理单个集合
     */
    private void processCollection(String sourceCollectionName, String targetCollectionName, boolean skipExisting) {
        MongoCollection<Document> sourceCollection = database.getCollection(sourceCollectionName);
        MongoCollection<Document> targetCollection = database.getCollection(targetCollectionName);
        
        // Get all plate numbers (保持原始顺序)
        List<String> plateNumbers = getPlateNumbersInOrder(sourceCollection);
        System.out.println("找到 " + plateNumbers.size() + " 个车牌号");
        
        if (skipExisting) {
            // Skip existing trajectories
            Set<String> existingPlates = getExistingPlateNumbers(targetCollection);
            plateNumbers.removeIf(existingPlates::contains);
            System.out.println("跳过 " + existingPlates.size() + " 个已存在的轨迹，剩余 " + plateNumbers.size() + " 个");
        }
        
        // Batch processing
        List<String> plateList = plateNumbers;
        int totalPlates = plateList.size();
        
        for (int i = 0; i < totalPlates; i += BATCH_SIZE) {
            int endIndex = Math.min(i + BATCH_SIZE, totalPlates);
            List<String> batch = plateList.subList(i, endIndex);
            
                // 静默处理批次
            
            // Submit batch processing task
            final int batchIndex = i + 1;
            executorService.submit(new Runnable() {
                @Override
                public void run() {
                    processBatch(sourceCollection, targetCollection, batch, batchIndex, totalPlates);
                }
            });
        }
        
        // Wait for all tasks to complete
        try {
            executorService.awaitTermination(Long.MAX_VALUE, TimeUnit.NANOSECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("Batch processing interrupted");
        }
    }
    
    /**
     * 处理一批车牌号（按顺序处理）
     */
    private void processBatch(MongoCollection<Document> sourceCollection, 
                            MongoCollection<Document> targetCollection,
                            List<String> plateNumbers, 
                            int batchStart, 
                            int totalPlates) {
        
        // 按顺序处理批次内的车牌号
        for (String plateNumber : plateNumbers) {
            try {
                processPlateNumber(sourceCollection, targetCollection, plateNumber);
                
                long processed = totalProcessed.incrementAndGet();
                if (processed % 100 == 0) { // 每100个车牌输出一次进度
                    System.out.println("已处理: " + processed + "/" + totalPlates + 
                                     " | 保存: " + totalSaved.get() + " | 跳过: " + totalSkipped.get());
                    checkMemoryUsage();
                }
                
            } catch (Exception e) {
                System.err.println("处理车牌号 " + plateNumber + " 时出错: " + e.getMessage());
                e.printStackTrace(); // 添加详细堆栈跟踪
                totalErrors.incrementAndGet();
            }
        }
    }
    
    /**
     * 处理单个车牌号
     */
    private void processPlateNumber(MongoCollection<Document> sourceCollection,
                                  MongoCollection<Document> targetCollection,
                                  String plateNumber) {
        
        // 查找原始轨迹
        Document originalDoc = sourceCollection.find(new Document("plate_number", plateNumber)).first();
        if (originalDoc == null) {
            totalSkipped.incrementAndGet();
            return;
        }
        
        @SuppressWarnings("unchecked")
        List<Document> originalPoints = (List<Document>) originalDoc.get("trajectory_points");
        if (originalPoints == null || originalPoints.isEmpty()) {
            totalSkipped.incrementAndGet();
            return;
        }
        
        // 转换为轨迹点，过滤null值
        List<Map<String, Object>> trajectoryPoints = new ArrayList<>();
        for (Document pointDoc : originalPoints) {
            Map<String, Object> point = TrajectoryCorrectionUtils.documentToTrajectoryPoint(pointDoc);
            if (point != null) { // 过滤掉null值
                trajectoryPoints.add(point);
            }
        }
        
        // 过滤有效点
        trajectoryPoints = TrajectoryCorrectionUtils.filterValidPoints(trajectoryPoints);
        if (trajectoryPoints.isEmpty()) {
            totalSkipped.incrementAndGet();
            return;
        }
        
        // 按时间排序
        TrajectoryCorrectionUtils.sortTrajectoryPointsByTime(trajectoryPoints);
        
        // 应用轨迹修正
        List<Map<String, Object>> correctedPoints = trajectoryCorrector.correctTrajectory(trajectoryPoints);
        
        if (correctedPoints.isEmpty()) {
            totalSkipped.incrementAndGet();
            return;
        }
        
        // 创建修正轨迹文档
        Document correctedDoc = TrajectoryCorrectionUtils.createCorrectedTrajectoryDocument(
            plateNumber, correctedPoints, sourceCollection.getNamespace().getCollectionName());
        
        if (correctedDoc == null) {
            totalSkipped.incrementAndGet();
            return;
        }
        
        try {
            // 保存修正轨迹
            targetCollection.insertOne(correctedDoc);
            totalSaved.incrementAndGet();
            
        } catch (MongoWriteException e) {
            if (e.getError().getCode() == 11000) { // 重复键错误
                totalSkipped.incrementAndGet();
            } else {
                throw e;
            }
        } finally {
            // 清理内存
            trajectoryPoints.clear();
            trajectoryPoints = null;
            correctedPoints.clear();
            correctedPoints = null;
            correctedDoc = null;
            originalDoc = null;
            originalPoints = null;
        }
    }
    
    /**
     * 按原始顺序获取集合中的所有车牌号
     */
    private List<String> getPlateNumbersInOrder(MongoCollection<Document> collection) {
        List<String> plateNumbers = new ArrayList<>();
        
        // 按_id排序获取车牌号，保持原始插入顺序
        // 也可以考虑按时间排序：.sort(new Document("correction_time", 1))
        FindIterable<Document> docs = collection.find()
            .projection(new Document("plate_number", 1))
            .sort(new Document("_id", 1));
            
        for (Document doc : docs) {
            String plateNumber = doc.getString("plate_number");
            if (plateNumber != null && !plateNumber.trim().isEmpty()) {
                plateNumbers.add(plateNumber);
            }
        }
        
        return plateNumbers;
    }
    
    /**
     * 获取集合中的所有车牌号（保持顺序的版本）
     */
    private Set<String> getPlateNumbers(MongoCollection<Document> collection) {
        Set<String> plateNumbers = new HashSet<>();
        
        FindIterable<Document> docs = collection.find().projection(new Document("plate_number", 1));
        for (Document doc : docs) {
            String plateNumber = doc.getString("plate_number");
            if (plateNumber != null && !plateNumber.trim().isEmpty()) {
                plateNumbers.add(plateNumber);
            }
        }
        
        return plateNumbers;
    }
    
    /**
     * 获取已存在的车牌号
     */
    private Set<String> getExistingPlateNumbers(MongoCollection<Document> collection) {
        Set<String> existingPlates = new HashSet<>();
        
        FindIterable<Document> docs = collection.find().projection(new Document("plate_number", 1));
        for (Document doc : docs) {
            String plateNumber = doc.getString("plate_number");
            if (plateNumber != null && !plateNumber.trim().isEmpty()) {
                existingPlates.add(plateNumber);
            }
        }
        
        return existingPlates;
    }
    
    /**
     * 检查内存使用情况
     */
    private void checkMemoryUsage() {
        MemoryUsage heapUsage = memoryBean.getHeapMemoryUsage();
        long usedPercent = heapUsage.getUsed() * 100 / heapUsage.getMax();
        
        if (usedPercent > 80) {
            System.out.println("内存使用警告: " + usedPercent + "%");
            System.gc();
        }
    }
    
    /**
     * 打印最终统计信息
     */
    private void printFinalStats(long duration) {
        System.out.println("\n==================================================");
        System.out.println("轨迹修正处理完成统计");
        System.out.println("==================================================");
        System.out.println("总处理车牌数: " + totalProcessed.get());
        System.out.println("总保存轨迹数: " + totalSaved.get());
        System.out.println("总跳过车牌数: " + totalSkipped.get());
        System.out.println("总错误数: " + totalErrors.get());
        System.out.println("处理时间: " + TrajectoryCorrectionUtils.formatDuration(duration));
        
        // Print trajectory corrector statistics
        Map<String, Long> correctorStats = trajectoryCorrector.getStatistics();
        System.out.println("\n轨迹修正统计:");
        System.out.println("修正轨迹数: " + correctorStats.get("totalCorrected"));
        System.out.println("移除重复点数: " + correctorStats.get("totalDuplicatesRemoved"));
        System.out.println("移除异常点数: " + correctorStats.get("totalAnomalousPointsRemoved"));
        
        System.out.println("\n✅ 所有轨迹修正处理完成！");
    }
    
    /**
     * 主方法
     */
    public static void main(String[] args) {
        boolean skipExisting = args.length > 0 && "true".equals(args[0]);
        
        TrajectoryCorrectionProcessor processor = new TrajectoryCorrectionProcessor();
        processor.processTrajectoryCorrection(skipExisting);
    }
}
