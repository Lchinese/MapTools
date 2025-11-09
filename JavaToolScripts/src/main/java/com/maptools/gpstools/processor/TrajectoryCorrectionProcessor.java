package com.maptools.gpstools.processor;

import org.bson.Document;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.FindIterable;
import com.mongodb.client.model.Filters;
import com.mongodb.MongoWriteException;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;

import com.maptools.gpstools.algorithm.HmmModel;
import com.maptools.gpstools.algorithm.RoadTransitionModel;
import com.maptools.gpstools.algorithm.AdjacencyConsistencyModel;
import com.maptools.gpstools.util.TrajectoryCorrectionUtils;

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
    private HmmModel hmmModel;
    private RoadTransitionModel roadTransitionModel;
    private AdjacencyConsistencyModel adjacencyConsistencyModel;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSaved = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalErrors = new AtomicLong(0);
    private AtomicLong totalDuplicatesRemoved = new AtomicLong(0);
    private AtomicLong totalAnomalousPointsRemoved = new AtomicLong(0);
    
    // 限制缓存大小以避免内存溢出
    private static final int MAX_CACHE_SIZE = 10000;
    
    // 缓存优化：避免重复计算
    private Map<String, Double> distanceCache = new ConcurrentHashMap<>();
    private Map<String, Long> timeDiffCache = new ConcurrentHashMap<>();
    
    // 内存管理
    private MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
    
    public TrajectoryCorrectionProcessor() {
        this.mongoClient = MongoClients.create("mongodb://localhost:27017");
        this.database = mongoClient.getDatabase("MapTools");
        this.executorService = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        this.hmmModel = new HmmModel();
        this.roadTransitionModel = new RoadTransitionModel();
        this.adjacencyConsistencyModel = new AdjacencyConsistencyModel();
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
                if (processed % 500 == 0) { // 每500个车牌输出一次进度
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
        
        // 仅使用道路匹配后的轨迹（不回退到原始轨迹）
        Document originalDoc = sourceCollection
            .find(Filters.and(
                Filters.eq("plate_number", plateNumber),
                Filters.eq("type", "matched_trajectory")
            ))
            .first();
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
        List<Map<String, Object>> correctedPoints = correctTrajectory(trajectoryPoints);
        
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
     * 修正单个轨迹 - 使用HMM模型进行异常点检测
     */
    public List<Map<String, Object>> correctTrajectory(List<Map<String, Object>> originalPoints) {
        if (originalPoints == null || originalPoints.size() < 2) {
            return originalPoints;
        }
        
        int originalCount = originalPoints.size();
        
        // 第一步：移除重复的相邻点
        List<Map<String, Object>> deduplicatedPoints = removeDuplicatePoints(originalPoints);
        int afterDeduplication = deduplicatedPoints.size();
        
        // 如果去重后点数少于2，直接返回
        if (deduplicatedPoints.size() < 2) {
            return deduplicatedPoints;
        }
        
        // 第二步：使用HMM进行异常点检测和过滤（返回统计信息）
        TrajectoryStats stats = new TrajectoryStats();
        List<Map<String, Object>> filteredPoints = hmmBasedAnomalyDetection(deduplicatedPoints, stats);
        int afterHmmFilter = filteredPoints.size();
        
        totalProcessed.incrementAndGet();
        
        // 调试输出：显示点数量变化
        if (originalCount != filteredPoints.size()) {
            int deduplicationRemoved = originalCount - afterDeduplication;
            int hmmRemoved = afterDeduplication - afterHmmFilter;
            
            System.out.println(String.format(
                "Trajectory: %d -> %d | Removed: Dup=%d, HMM=%d", 
                originalCount, filteredPoints.size(), 
                deduplicationRemoved,
                hmmRemoved
            ));
        }
        
        return filteredPoints;
    }
    
    /**
     * 轨迹统计信息（用于单次处理的统计）
     */
    private static class TrajectoryStats {
    }
    
    /**
     * 预计算的轨迹指标（避免重复计算）
     * 设为静态内部类，允许 HmmModel 访问
     */
    public static class TrajectoryMetrics {
        public double[] speeds;           // 速度 (km/h)
        public double[] distances;        // 距离 (m)
        public long[] timeDiffs;          // 时间差 (ms)
        public double[] headings;         // 方向角 (度)
        public double[] headingDiffs;     // 方向变化 (度)
        
        public TrajectoryMetrics(int size) {
            this.speeds = new double[size];
            this.distances = new double[size];
            this.timeDiffs = new long[size];
            this.headings = new double[size];
            this.headingDiffs = new double[size];
        }
    }
    
    /**
     * 一次性预计算所有轨迹指标（避免重复计算）
     */
    private TrajectoryMetrics precomputeTrajectoryMetrics(List<Map<String, Object>> points) {
        int n = points.size();
        TrajectoryMetrics metrics = new TrajectoryMetrics(n);
        
        // 第一个点的默认值
        metrics.speeds[0] = 0.0;
        metrics.distances[0] = 0.0;
        metrics.timeDiffs[0] = 0L;
        metrics.headings[0] = safeHeading(points.get(0).get("heading"));
        metrics.headingDiffs[0] = 0.0;
        
        // 计算后续点的指标
        for (int i = 1; i < n; i++) {
            Map<String, Object> prev = points.get(i - 1);
            Map<String, Object> curr = points.get(i);
            
            // 提取坐标
            double prevLon = safeDouble(prev.get("longitude"));
            double prevLat = safeDouble(prev.get("latitude"));
            double curLon = safeDouble(curr.get("longitude"));
            double curLat = safeDouble(curr.get("latitude"));
            
            // 计算距离（使用缓存）
            metrics.distances[i] = getCachedDistance(prevLon, prevLat, curLon, curLat);
            
            // 计算时间差（使用缓存）
            metrics.timeDiffs[i] = getCachedTimeDifference(prev, curr);
            
            // 计算速度
            if (metrics.timeDiffs[i] > 0 && metrics.timeDiffs[i] != Long.MAX_VALUE) {
                metrics.speeds[i] = (metrics.distances[i] / 1000.0) / (metrics.timeDiffs[i] / 3600000.0);
            } else {
                metrics.speeds[i] = 0.0;
            }
            
            // 提取方向角
            double prevHeading = safeHeading(prev.get("heading"));
            double curHeading = safeHeading(curr.get("heading"));
            
            // 如果当前点速度为0，则不参考方向信息
            Object speedObj = curr.get("speed");
            if (speedObj instanceof Number && ((Number) speedObj).doubleValue() == 0) {
                curHeading = Double.NaN; // 速度为0时不参考方向
            }
            
            metrics.headings[i] = curHeading;
            
            // 计算方向变化
            if (Double.isNaN(prevHeading) || Double.isNaN(curHeading)) {
                // 如果任一方向无效，则方向变化也为无效
                metrics.headingDiffs[i] = Double.NaN;
            } else {
                double headingDiff = Math.abs(curHeading - prevHeading);
                if (headingDiff > 180) {
                    headingDiff = 360 - headingDiff;
                }
                metrics.headingDiffs[i] = headingDiff;
            }
        }
        
        return metrics;
    }
    
    /**
     * 基于HMM的异常点检测（三维互补检测系统）
     * 
     * 检测维度（职责分离，避免重复评估）：
     * 1. HMM概率：速度统计特征（基于高斯分布）- 权重 40%
     * 2. 道路切换概率：物理可行性（距离约束）- 权重 20%
     * 3. 相邻一致性：几何连续性（方向、曲率）- 权重 40%
     * 
     * 综合评分 = 速度统计×0.4 + 物理约束×0.2 + 几何一致性×0.4
     */
    private List<Map<String, Object>> hmmBasedAnomalyDetection(List<Map<String, Object>> points, TrajectoryStats stats) {
        if (points.size() < 2) {
            return points;
        }
        
        try {
            // 预计算所有指标（避免重复计算）
            TrajectoryMetrics metrics = precomputeTrajectoryMetrics(points);
            
            // 维度1：HMM速度统计检测
            double[] probabilities = hmmModel.calculatePointProbabilitiesFromMetrics(metrics);
        
            // 维度2：道路切换物理可行性检测
            double[] roadTransitionProbabilities = calculateRoadTransitionProbabilities(points, metrics);
            
            // 维度3：几何一致性检测（方向、曲率）
            // 使用基于置信度的相邻一致性评分
            double[] adjacencyConsistency = calculateAdjacencyConsistencyWithSelfConfidence(points, metrics);
            
            // 综合判定：三维评分加权和（更合理的评分方式）
            List<Map<String, Object>> filteredPoints = new ArrayList<>();
            for (int i = 0; i < points.size(); i++) {
                // 综合评分 = 速度统计×0.4 + 物理约束×0.2 + 几何一致性×0.4
                double combinedScore = probabilities[i] * 0.4 
                                     + roadTransitionProbabilities[i] * 0.2 
                                     + adjacencyConsistency[i] * 0.4;
                if (Double.isNaN(combinedScore) || Double.isInfinite(combinedScore)) {
                    combinedScore = 0.0;
                }
                // 夹紧到[0,1]
                if (combinedScore < 0.0) combinedScore = 0.0;
                if (combinedScore > 1.0) combinedScore = 1.0;
                
                // 两档决策：接收/丢弃（基于阈值）
                if (combinedScore > 0.6) { // 接收
                    filteredPoints.add(points.get(i));
                } else { // 丢弃
                    totalAnomalousPointsRemoved.incrementAndGet();
                }
            }
        
            return filteredPoints;
        } catch (Exception e) {
            // 如果HMM处理失败，返回原始点（保守策略）
            System.err.println("HMM anomaly detection failed, returning original trajectory: " + e.getMessage());
            e.printStackTrace(); // 添加堆栈跟踪以便调试
            return points;
        }
    }
    
    /**
     * 计算道路切换概率（使用预计算指标）
     * 职责：只检查距离和时间合理性，速度检查已由HMM负责
     */
    private double[] calculateRoadTransitionProbabilities(List<Map<String, Object>> points, TrajectoryMetrics metrics) {
        double[] probabilities = new double[points.size()];
        
        // 第一个点默认为正常
        probabilities[0] = 1.0;
        
        for (int i = 1; i < points.size(); i++) {
            // 直接使用预计算的距离、时间
            double distance = metrics.distances[i];
            long timeDiff = metrics.timeDiffs[i];
            
            // 获取当前点的道路类型
            String roadType = safeString(points.get(i).get("road_type"));
            
            // 检查道路一致性 - 综合考虑前后高置信度点的道路信息
            String roadId = safeString(points.get(i).get("road_id"));
            String prevRoadId = (i > 0) ? safeString(points.get(i-1).get("road_id")) : null;
            double roadConsistencyFactor = roadTransitionModel.evaluateRoadConsistency(roadId, prevRoadId);
            
            if (timeDiff > 0 && timeDiff != Long.MAX_VALUE) {
                // 道路切换概率计算（只考虑距离和时间，速度检查已在HMM中完成）
                double roadTransitionProb = roadTransitionModel.calculateRoadTransitionProbability(distance, timeDiff, roadType);
                // 应用道路一致性因素
                probabilities[i] = Math.min(1.0, roadTransitionProb * roadConsistencyFactor);
            } else {
                // 时间解析失败，使用保守概率
                probabilities[i] = 0.5 * roadConsistencyFactor;
            }
        }
        
        return probabilities;
    }
    
    /**
     * 计算相邻一致性（使用自身历史评分作为置信度基准的版本）
     * 
     * 该方法首先计算初始的一致性评分，然后使用这些评分作为置信度基准来重新计算
     */
    private double[] calculateAdjacencyConsistencyWithSelfConfidence(List<Map<String, Object>> points, 
                                                         TrajectoryMetrics metrics) {
        // 首先计算初始的一致性评分（使用空数组作为初始一致性）
        double[] initialConsistency = new double[points.size()];
        for (int i = 0; i < initialConsistency.length; i++) {
            initialConsistency[i] = 1.0;
        }
        
        // 然后使用这些评分作为置信度基准来重新计算
        return adjacencyConsistencyModel.calculateAdjacencyConsistencyWithConfidence(points, metrics, initialConsistency);
    }
    
    /**
     * 移除重复的相邻点
     */
    private List<Map<String, Object>> removeDuplicatePoints(List<Map<String, Object>> points) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (points == null || points.isEmpty()) {
            return result;
        }
        
        result.add(points.get(0));
        for (int i = 1; i < points.size(); i++) {
            Map<String, Object> prev = points.get(i - 1);
            Map<String, Object> curr = points.get(i);
            
            double prevLon = safeDouble(prev.get("longitude"));
            double prevLat = safeDouble(prev.get("latitude"));
            double curLon = safeDouble(curr.get("longitude"));
            double curLat = safeDouble(curr.get("latitude"));
            
            if (prevLon != curLon || prevLat != curLat) {
                result.add(curr);
            } else {
                totalDuplicatesRemoved.incrementAndGet();
            }
        }
        
        return result;
    }
    
    /**
     * 安全提取double值
     */
    private double safeDouble(Object obj) {
        if (obj instanceof Number) {
            return ((Number) obj).doubleValue();
        }
        return 0.0;
    }
    
    /**
     * 安全提取String值
     */
    private String safeString(Object obj) {
        if (obj instanceof String) {
            return (String) obj;
        }
        return "";
    }
    
    /**
     * 安全提取Double值
     */
    private Double safeHeading(Object obj) {
        if (obj instanceof Number) {
            return ((Number) obj).doubleValue();
        }
        return null;
    }
    
    /**
     * 获取缓存的距离
     */
    private double getCachedDistance(double lon1, double lat1, double lon2, double lat2) {
        String key = lon1 + "," + lat1 + "," + lon2 + "," + lat2;
        
        // 控制缓存大小
        if (distanceCache.size() > MAX_CACHE_SIZE) {
            distanceCache.clear();
        }
        
        Double cached = distanceCache.get(key);
        if (cached != null) {
            return cached;
        }
        
        double distance = calculateDistance(lon1, lat1, lon2, lat2);
        distanceCache.put(key, distance);
        return distance;
    }
    
    /**
     * 带缓存的时间差计算
     */
    private long getCachedTimeDifference(Map<String, Object> point1, Map<String, Object> point2) {
        // 创建缓存键（基于时间字符串）
        String time1 = point1.get("datetime") != null ? point1.get("datetime").toString() : "";
        String time2 = point2.get("datetime") != null ? point2.get("datetime").toString() : "";
        String cacheKey = time1 + "|" + time2;
        
        // 控制缓存大小
        if (timeDiffCache.size() > MAX_CACHE_SIZE) {
            timeDiffCache.clear();
        }
        
        Long cached = timeDiffCache.get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        long timeDiff = calculateTimeDifference(point1, point2);
        timeDiffCache.put(cacheKey, timeDiff);
        return timeDiff;
    }
    
    /**
     * 计算两个点之间的时间差（毫秒）
     */
    private long calculateTimeDifference(Map<String, Object> point1, Map<String, Object> point2) {
        try {
            Object datetimeObj1 = point1.get("datetime");
            Object datetimeObj2 = point2.get("datetime");
            
            if (datetimeObj1 == null || datetimeObj2 == null) {
                return Long.MAX_VALUE; // 无法计算时间差时返回最大值
            }
            
            // 移除调试信息，让脚本正常运行
            
            Date date1 = null;
            Date date2 = null;
            
            // 如果已经是Date对象，直接使用
            if (datetimeObj1 instanceof Date && datetimeObj2 instanceof Date) {
                date1 = (Date) datetimeObj1;
                date2 = (Date) datetimeObj2;
            } else {
                // 如果是字符串，尝试解析
                String datetime1 = datetimeObj1.toString();
                String datetime2 = datetimeObj2.toString();
                
                // 尝试多种时间格式，包括Date.toString()格式
                String[] formats = {
                    "EEE MMM dd HH:mm:ss zzz yyyy",  // Date.toString()格式: Thu Sep 01 08:07:20 CST 2016
                    "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
                    "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",
                    "yyyy-MM-dd'T'HH:mm:ss.SSS",
                    "yyyy-MM-dd'T'HH:mm:ss'Z'",
                    "yyyy-MM-dd'T'HH:mm:ssXXX",
                    "yyyy-MM-dd'T'HH:mm:ss",
                    "yyyy-MM-dd HH:mm:ss.SSS",
                    "yyyy-MM-dd HH:mm:ss"
                };
                
                for (String format : formats) {
                    try {
                        java.text.SimpleDateFormat sdf;
                        if (format.equals("EEE MMM dd HH:mm:ss zzz yyyy")) {
                            // Date.toString()格式需要ENGLISH locale
                            sdf = new java.text.SimpleDateFormat(format, java.util.Locale.ENGLISH);
                        } else {
                            sdf = new java.text.SimpleDateFormat(format);
                        }
                        sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                        date1 = sdf.parse(datetime1);
                        date2 = sdf.parse(datetime2);
                        break;
                    } catch (Exception e) {
                        // 继续尝试下一个格式
                    }
                }
            }
            
            if (date1 == null || date2 == null) {
                return Long.MAX_VALUE;
            }
            
            long timeDiff = Math.abs(date2.getTime() - date1.getTime());
            return timeDiff;
        } catch (Exception e) {
            return Long.MAX_VALUE; // 解析失败时返回最大值
        }
    }
    
    /**
     * 计算两点间距离（米）
     */
    private double calculateDistance(double lon1, double lat1, double lon2, double lat2) {
        double EARTH_RADIUS = 6371000.0; // 地球半径（米）
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS * c;
    }
    
    /**
     * 按原始顺序获取集合中的所有车牌号
     */
    private List<String> getPlateNumbersInOrder(MongoCollection<Document> collection) {
        Set<String> plateNumberSet = new LinkedHashSet<>(); // 使用LinkedHashSet保持顺序并去重
        
        // 按_id排序获取车牌号，保持原始插入顺序
        FindIterable<Document> docs = collection.find()
            .projection(new Document("plate_number", 1))
            .sort(new Document("_id", 1));
            
        for (Document doc : docs) {
            String plateNumber = doc.getString("plate_number");
            if (plateNumber != null && !plateNumber.trim().isEmpty()) {
                plateNumberSet.add(plateNumber);
            }
        }
        
        return new ArrayList<>(plateNumberSet);
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
        
        System.out.println("\n轨迹修正统计:");
        System.out.println("移除重复点数: " + totalDuplicatesRemoved.get());
        System.out.println("移除异常点数: " + totalAnomalousPointsRemoved.get());
        
        System.out.println("\n✅ 所有轨迹修正处理完成！");
    }
    
    /**
     * 获取统计信息
     */
    public Map<String, Long> getStatistics() {
        Map<String, Long> stats = new HashMap<>();
        stats.put("totalProcessed", totalProcessed.get());
        stats.put("totalSkipped", totalSkipped.get());
        stats.put("totalDuplicatesRemoved", totalDuplicatesRemoved.get());
        stats.put("totalAnomalousPointsRemoved", totalAnomalousPointsRemoved.get());
        return stats;
    }
    
    /**
     * 重置统计信息
     */
    public void resetStatistics() {
        totalProcessed.set(0);
        totalSkipped.set(0);
        totalDuplicatesRemoved.set(0);
        totalAnomalousPointsRemoved.set(0);
        
        // 清理缓存
        distanceCache.clear();
        timeDiffCache.clear();
    }
    
    /**
     * 关闭连接
     */
    public void close() {
        if (mongoClient != null) {
            mongoClient.close();
        }
        
        // 清理缓存
        distanceCache.clear();
        timeDiffCache.clear();
        
        System.gc();
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