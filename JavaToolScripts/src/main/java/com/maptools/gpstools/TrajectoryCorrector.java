package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.ConcurrentHashMap;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * HMM GPS数据点类
 */
class HmmGPSDataPoint {
    private double longitude;
    private double latitude;
    private Date timestamp;
    private Double heading; // 方向角，可为null
    
    public HmmGPSDataPoint(double longitude, double latitude, Date timestamp) {
        this.longitude = longitude;
        this.latitude = latitude;
        this.timestamp = timestamp;
        this.heading = null;
    }
    
    public HmmGPSDataPoint(double longitude, double latitude, Date timestamp, Double heading) {
        this.longitude = longitude;
        this.latitude = latitude;
        this.timestamp = timestamp;
        this.heading = heading;
    }
    
    public double getLongitude() { return longitude; }
    public double getLatitude() { return latitude; }
    public Date getTimestamp() { return timestamp; }
    public Double getHeading() { return heading; }
}

/**
 * HMM输入类
 */
class HmmInput {
    private List<HmmGPSDataPoint> observations;
    
    public HmmInput(List<HmmGPSDataPoint> observations) {
        this.observations = observations;
    }
    
    public List<HmmGPSDataPoint> getObservations() { return observations; }
}

/**
 * HMM模型类 - 专注于速度统计特征检测
 * 参数基于GraphHopper和Valhalla Meili等开源地图匹配库的标准值
 * 
 * 职责分离：
 * - HMM：速度统计异常检测（基于高斯分布）
 * - adjacencyConsistency：几何连续性检测（方向、曲率）
 * - roadTransition：物理可行性检测（距离、时间）
 */
class HmmModel {
    // GPS观测参数（基于GraphHopper标准 - 保留作为参考）
    // GPS_SIGMA = 4.07m - GPS测量误差标准差（业界标准值）
    // TRANSITION_BETA = 3.0 - 路由转换参数
    // 这些参数在标准HMM地图匹配中使用，此处保留供未来扩展参考
    
    // 速度模型参数（城市道路）
    private static final double NORMAL_SPEED_MEAN = 40.0; // 城市道路正常速度均值 (km/h)
    private static final double NORMAL_SPEED_VARIANCE = 400.0; // 正常速度方差 (std = 20 km/h)
    
    private static final double ANOMALY_SPEED_MEAN = 120.0; // 异常速度均值 (km/h) - 高速异常
    private static final double ANOMALY_SPEED_VARIANCE = 900.0; // 异常速度方差 (std = 30 km/h)
    
    /**
     * 计算轨迹点的概率（用于异常检测）- 旧版本，保留兼容性
     */
    public double[] calculatePointProbabilities(HmmInput input) {
        List<HmmGPSDataPoint> observations = input.getObservations();
        int n = observations.size();
        
        if (n < 2) {
            return new double[n];
        }
        
        // 计算每个点的速度和方向特征
        double[] speeds = calculateSpeeds(observations);
        double[] directionChanges = calculateDirectionChanges(observations);
        
        // 使用简化的HMM前向-后向算法，结合速度和方向
        return forwardBackwardAlgorithm(speeds, directionChanges);
    }
    
    /**
     * 从预计算的指标计算轨迹点概率（优化版本，避免重复计算）
     * 注意：方向检测已移至adjacencyConsistency，此处只关注速度统计特征
     */
    public double[] calculatePointProbabilitiesFromMetrics(TrajectoryCorrector.TrajectoryMetrics metrics) {
        int n = metrics.speeds.length;
        
        if (n < 2) {
            return new double[n];
        }
        
        // HMM只关注速度统计特征，方向检测交给adjacencyConsistency处理（避免重复）
        return forwardBackwardAlgorithmSpeedOnly(metrics.speeds);
    }
    
    /**
     * 简化的HMM算法（仅基于速度）
     */
    private double[] forwardBackwardAlgorithmSpeedOnly(double[] speeds) {
        int n = speeds.length;
        double[] probabilities = new double[n];
        
        for (int i = 0; i < n; i++) {
            double speed = speeds[i];
            
            // 计算正常状态的概率（基于速度）
            double normalSpeedProb = gaussianProbability(speed, NORMAL_SPEED_MEAN, NORMAL_SPEED_VARIANCE);
            
            // 计算异常状态的概率（基于速度）
            double anomalySpeedProb = gaussianProbability(speed, ANOMALY_SPEED_MEAN, ANOMALY_SPEED_VARIANCE);
            
            // 归一化概率
            double totalProb = normalSpeedProb + anomalySpeedProb;
            if (totalProb > 0) {
                probabilities[i] = normalSpeedProb / totalProb;
            } else {
                probabilities[i] = 0.5; // 默认概率
            }
        }
        
        return probabilities;
    }
    
    /**
     * 计算轨迹点之间的速度和方向特征
     */
    private double[] calculateSpeeds(List<HmmGPSDataPoint> observations) {
        int n = observations.size();
        double[] speeds = new double[n];
        speeds[0] = 0.0; // 第一个点速度为0
        
        for (int i = 1; i < n; i++) {
            HmmGPSDataPoint prev = observations.get(i - 1);
            HmmGPSDataPoint curr = observations.get(i);
            
            double distance = calculateDistance(
                prev.getLongitude(), prev.getLatitude(),
                curr.getLongitude(), curr.getLatitude()
            );
            
            long timeDiff = curr.getTimestamp().getTime() - prev.getTimestamp().getTime();
            
            if (timeDiff > 0) {
                speeds[i] = (distance / 1000.0) / (timeDiff / 3600000.0); // km/h
            } else {
                speeds[i] = 0.0;
            }
        }
        
        return speeds;
    }
    
    /**
     * 计算方向变化特征（用于HMM模型）
     */
    private double[] calculateDirectionChanges(List<HmmGPSDataPoint> observations) {
        int n = observations.size();
        double[] directionChanges = new double[n];
        directionChanges[0] = 0.0; // 第一个点方向变化为0
        
        for (int i = 1; i < n; i++) {
            HmmGPSDataPoint prev = observations.get(i - 1);
            HmmGPSDataPoint curr = observations.get(i);
            
            // 优先使用heading字段
            if (curr.getHeading() != null && prev.getHeading() != null) {
                double angleDiff = Math.abs(curr.getHeading() - prev.getHeading());
                if (angleDiff > 180) {
                    angleDiff = 360 - angleDiff;
                }
                directionChanges[i] = angleDiff;
            } else {
                // 回退到几何计算
                double angle1 = calculateBearing(
                    prev.getLongitude(), prev.getLatitude(),
                    curr.getLongitude(), curr.getLatitude()
                );
                directionChanges[i] = angle1; // 简化处理
            }
        }
        
        return directionChanges;
    }
    
    /**
     * 简化的前向-后向算法实现（结合速度和方向）
     */
    private double[] forwardBackwardAlgorithm(double[] speeds, double[] directionChanges) {
        int n = speeds.length;
        double[] probabilities = new double[n];
        
        // 简化的异常检测：基于速度和方向变化的概率分布
        for (int i = 0; i < n; i++) {
            double speed = speeds[i];
            double directionChange = directionChanges[i];
            
            // 计算正常状态的概率（基于速度）
            double normalSpeedProb = gaussianProbability(speed, NORMAL_SPEED_MEAN, NORMAL_SPEED_VARIANCE);
            
            // 计算异常状态的概率（基于速度）
            double anomalySpeedProb = gaussianProbability(speed, ANOMALY_SPEED_MEAN, ANOMALY_SPEED_VARIANCE);
            
            // 计算方向变化概率
            double directionProb = calculateDirectionProbability(directionChange);
            
            // 综合概率：速度概率 * 方向概率
            double normalProb = normalSpeedProb * directionProb;
            double anomalyProb = anomalySpeedProb * (2.0 - directionProb); // 方向变化大时，异常概率增加
            
            // 归一化概率
            double totalProb = normalProb + anomalyProb;
            if (totalProb > 0) {
                probabilities[i] = normalProb / totalProb;
            } else {
                probabilities[i] = 0.5; // 默认概率
            }
        }
        
        return probabilities;
    }
    
    /**
     * 高斯概率密度函数
     */
    private double gaussianProbability(double x, double mean, double variance) {
        double stdDev = Math.sqrt(variance);
        double coefficient = 1.0 / (stdDev * Math.sqrt(2 * Math.PI));
        double exponent = -Math.pow(x - mean, 2) / (2 * variance);
        return coefficient * Math.exp(exponent);
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
     * 计算两点间的方位角（0-360度）
     */
    private double calculateBearing(double lon1, double lat1, double lon2, double lat2) {
        double dLon = Math.toRadians(lon2 - lon1);
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);
        
        double y = Math.sin(dLon) * Math.cos(lat2Rad);
        double x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - 
                  Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
        
        double bearing = Math.toDegrees(Math.atan2(y, x));
        return (bearing + 360) % 360; // 转换为0-360度
    }
    
    /**
     * 根据角度差计算方向变化概率
     */
    private double calculateDirectionProbability(double angleDiff) {
        // 方向变化概率：角度差越大，概率越低
        if (angleDiff > 150) { // 大于150度认为是掉头/回头
            return Math.exp(-(angleDiff - 150) / 30.0); // 指数衰减，更严格
        } else if (angleDiff > 90) { // 90-150度之间，认为是急转弯
            return 0.7 + 0.3 * Math.exp(-(angleDiff - 90) / 60.0); // 中等概率
        } else if (angleDiff > 45) { // 45-90度之间，轻微降低概率
            return 0.9;
        } else {
            return 1.0; // 小角度变化，保持高概率
        }
    }
}

/**
 * 轨迹修正处理器
 * 使用HMM模型检测并移除异常点，进行轨迹清理
 * 
 * 参数标准参考：
 * - GraphHopper Map Matching (github.com/graphhopper/map-matching)
 * - Valhalla Meili (github.com/valhalla/valhalla)
 * - Microsoft Research HMM Map Matching Paper
 */
public class TrajectoryCorrector {
    
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    // 决策阈值（基于GraphHopper标准）
    private static final double ACCEPT_THRESHOLD = 0.60;  // 接收阈值
    private static final double REJECT_THRESHOLD = 0.30;  // 丢弃阈值
    // 0.30 ~ 0.60 之间的点需要重匹配
    
    private MongoClient mongoClient;
    private HmmModel hmmModel;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalDuplicatesRemoved = new AtomicLong(0);
    private AtomicLong totalAnomalousPointsRemoved = new AtomicLong(0);
    private AtomicLong totalRematchedPoints = new AtomicLong(0);
    private AtomicLong totalRematchFailures = new AtomicLong(0);
    
    // 缓存优化：避免重复计算
    private Map<String, Double> distanceCache = new ConcurrentHashMap<>();
    private Map<String, Long> timeDiffCache = new ConcurrentHashMap<>();
    
    public TrajectoryCorrector() {
        try {
            this.mongoClient = new MongoClient(new MongoClientURI("mongodb://localhost:27017"));
        } catch (Exception e) {
            // 如果MongoDB不可用，设置为null
            this.mongoClient = null;
            System.out.println("MongoDB unavailable, using offline mode: " + e.getMessage());
        }
        this.hmmModel = new HmmModel();
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
        
        // 第二步：使用HMM进行异常点检测和过滤（返回统计信息）
        TrajectoryStats stats = new TrajectoryStats();
        List<Map<String, Object>> filteredPoints = hmmBasedAnomalyDetection(deduplicatedPoints, stats);
        int afterHmmFilter = filteredPoints.size();
        
        totalProcessed.incrementAndGet();
        
        // 调试输出：显示点数量变化和重匹配信息
        if (originalCount != filteredPoints.size() || stats.rematchSuccess > 0 || stats.rematchFailure > 0) {
            int deduplicationRemoved = originalCount - afterDeduplication;
            int hmmRemoved = afterDeduplication - afterHmmFilter;
            int directlyRejected = hmmRemoved - stats.rematchFailure; // 直接丢弃的点 = 总移除 - 重匹配失败
            
            System.out.println(String.format(
                "Trajectory: %d -> %d | Removed: Dup=%d, Direct=%d, RematchFail=%d | RematchSuccess=%d", 
                originalCount, filteredPoints.size(), 
                deduplicationRemoved,
                directlyRejected,
                stats.rematchFailure,
                stats.rematchSuccess
            ));
        }
        
        return filteredPoints;
    }
    
/**
 * 轨迹统计信息（用于单次处理的统计）
 */
private static class TrajectoryStats {
    int rematchSuccess = 0;
    int rematchFailure = 0;
}

/**
 * 预计算的轨迹指标（避免重复计算）
 * 设为静态内部类，允许 HmmModel 访问
 */
static class TrajectoryMetrics {
    double[] speeds;           // 速度 (km/h)
    double[] distances;        // 距离 (m)
    long[] timeDiffs;          // 时间差 (ms)
    double[] headings;         // 方向角 (度)
    double[] headingDiffs;     // 方向变化 (度)
    
    TrajectoryMetrics(int size) {
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
        metrics.headings[i] = curHeading;
        
        // 计算方向变化
        double headingDiff = Math.abs(curHeading - prevHeading);
        if (headingDiff > 180) {
            headingDiff = 360 - headingDiff;
        }
        metrics.headingDiffs[i] = headingDiff;
    }
    
    return metrics;
}
    
    /**
     * 基于HMM的异常点检测（三维互补检测系统）
     * 
     * 检测维度（职责分离，避免重复评估）：
     * 1. HMM概率：速度统计特征（基于高斯分布）
     * 2. 道路切换概率：物理可行性（距离、速度、时间合理性）
     * 3. 相邻一致性：几何连续性（方向、曲率、直线跨越）
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
            double[] adjacencyConsistency = calculateAdjacencyConsistency(points, metrics);
            
            // 综合判定：三维评分相乘（职责互补，无重复）
            List<Map<String, Object>> filteredPoints = new ArrayList<>();
            int lastAcceptedIndex = -1;
        for (int i = 0; i < points.size(); i++) {
                // 综合评分 = 速度统计 × 物理可行性 × 几何一致性
                double combinedScore = probabilities[i] * roadTransitionProbabilities[i] * adjacencyConsistency[i];
                if (Double.isNaN(combinedScore) || Double.isInfinite(combinedScore)) {
                    combinedScore = 0.0;
                }
                // 夹紧到[0,1]
                if (combinedScore < 0.0) combinedScore = 0.0;
                if (combinedScore > 1.0) combinedScore = 1.0;

                // 三档决策：接收/重匹配/丢弃（基于GraphHopper标准）
                if (combinedScore > ACCEPT_THRESHOLD) { // 直接接收
                filteredPoints.add(points.get(i));
                    lastAcceptedIndex = filteredPoints.size() - 1;
                } else if (combinedScore < REJECT_THRESHOLD) { // 直接丢弃
                    totalAnomalousPointsRemoved.incrementAndGet();
                } else { // 需要重匹配（在阈值之间）
                    Map<String, Object> rematched = tryLocalRematch(points, i, filteredPoints, lastAcceptedIndex);
                    if (rematched != null) {
                        filteredPoints.add(rematched);
                        lastAcceptedIndex = filteredPoints.size() - 1;
                        totalRematchedPoints.incrementAndGet();
                        stats.rematchSuccess++; // 局部统计
            } else {
                        // 无法有效重匹配则丢弃
                        totalRematchFailures.incrementAndGet();
                totalAnomalousPointsRemoved.incrementAndGet();
                        stats.rematchFailure++; // 局部统计
                    }
            }
        }
        
        return filteredPoints;
        } catch (Exception e) {
            // 如果HMM处理失败，返回原始点（保守策略）
            System.err.println("HMM anomaly detection failed, returning original trajectory: " + e.getMessage());
            return points;
        }
    }
    
    /**
     * 计算道路切换概率（使用预计算指标）
     */
    private double[] calculateRoadTransitionProbabilities(List<Map<String, Object>> points, TrajectoryMetrics metrics) {
        double[] probabilities = new double[points.size()];
        
        // 第一个点默认为正常
        probabilities[0] = 1.0;
        
        for (int i = 1; i < points.size(); i++) {
            // 直接使用预计算的速度、距离、时间
            double speed = metrics.speeds[i];
            double distance = metrics.distances[i];
            long timeDiff = metrics.timeDiffs[i];
            
            if (timeDiff > 0 && timeDiff != Long.MAX_VALUE) {
                // 道路切换概率计算（只考虑速度、距离、时间，方向检测已整合到HMM中）
                double roadTransitionProb = calculateRoadTransitionProbability(speed, distance, timeDiff);
                probabilities[i] = roadTransitionProb;
            } else {
                // 时间解析失败，使用保守概率
                probabilities[i] = 0.5;
            }
        }
        
        return probabilities;
    }
    
    /**
     * 计算相邻一致性（IVMM风格，使用预计算指标）：
     * - heading 连续性（相邻点方向差小则高分）
     * - 曲率连续性（连续三点转角平滑则高分）
     * - 直线跨越惩罚（长距离/短时间的直线段给惩罚）
     * 
     * 注意：此模块专门负责几何一致性检测（方向、曲率），
     *      与HMM的速度统计检测、roadTransition的物理可行性检测互补
     */
    private double[] calculateAdjacencyConsistency(List<Map<String, Object>> points, TrajectoryMetrics metrics) {
        int n = points.size();
        double[] result = new double[n];
        if (n == 0) return result;
        result[0] = 1.0;
        if (n == 1) return result;
        
        for (int i = 1; i < n; i++) {
            // 使用预计算的方向变化
            double headingDiff = metrics.headingDiffs[i];
            double headingScore = headingDiff <= 180 ? Math.exp(-headingDiff / 60.0) : 0.2;
            
            // 曲率（需要前后点）
            double curvatureScore = 1.0;
            if (i >= 2) {
                // 使用预计算的方向变化
                double diff1 = metrics.headingDiffs[i - 1];
                double diff2 = metrics.headingDiffs[i];
                double curvatureChange = Math.abs(diff2 - diff1);
                curvatureScore = Math.exp(-curvatureChange / 60.0);
            }
            
            // 直线跨越惩罚：使用预计算的距离和速度
            double distance = metrics.distances[i];
            double speed = metrics.speeds[i];
            long dt = metrics.timeDiffs[i];
            
            double straightPenalty = 1.0;
            if (dt > 0 && dt != Long.MAX_VALUE) {
                // 长距离且速度异常高时，认为可能是直线跨越（130 km/h阈值）
                if (distance > 300 && speed > 130) {
                    straightPenalty = Math.exp(- (distance - 300) / 500.0);
                }
            }
            
            double combined = headingScore * curvatureScore * straightPenalty;
            // 保底，避免完全归零
            result[i] = Math.max(0.2, Math.min(1.0, combined));
        }
        return result;
    }

    /**
     * 统一智能重匹配：综合考虑道路几何、轨迹连续性、方向一致性
     * 
     * 综合约束（非串行fallback）：
     * 1. 轨迹连续性：前后点的距离、时间、速度合理性
     * 2. 道路几何约束：MongoDB中的真实道路线形（如果可用）
     * 3. 方向一致性：与前一点及道路方向的连续性
     * 4. 距离最小化：修正后的点应尽量接近原始点
     * 
     * 生成多个候选点，综合评分后选择最优
     */
    private Map<String, Object> tryLocalRematch(List<Map<String, Object>> original, int index,
                                               List<Map<String, Object>> accepted, int lastAcceptedIndex) {
        try {
            Map<String, Object> current = original.get(index);
            // 若无已接收前驱，或数据不完整，放弃重匹配
            if (lastAcceptedIndex < 0 || accepted.isEmpty()) {
                return null;
            }
            Map<String, Object> prev = accepted.get(lastAcceptedIndex);

            // 提取基本信息
            double prevLon = safeDouble(prev.get("longitude"));
            double prevLat = safeDouble(prev.get("latitude"));
            double prevHeading = safeHeading(prev.get("heading"));
            double curLon = safeDouble(current.get("longitude"));
            double curLat = safeDouble(current.get("latitude"));
            double curHeading = safeHeading(current.get("heading"));
            
            String prevRoadId = safeString(prev.get("road_id"));
            String curRoadId = safeString(current.get("road_id"));
            
            // 生成多个候选修正点
            List<CandidatePoint> candidates = new ArrayList<>();
            
            // 候选1：保持原点不变
            candidates.add(new CandidatePoint(curLon, curLat, curHeading, "original"));
            
            // 候选2：MongoDB道路投影（如果可用）
            if (curRoadId != null && !curRoadId.isEmpty() && mongoClient != null) {
                CandidatePoint roadProjection = projectToRoadGeometry(
                    curLon, curLat, curRoadId, prevRoadId
                );
                if (roadProjection != null) {
                    candidates.add(roadProjection);
                }
            }
            
            // 候选3：方向连续性纠偏（基于前一点方向）
            if (prevRoadId != null && curRoadId != null && prevRoadId.equals(curRoadId)) {
                // 同一道路上，沿前一点方向投影
                CandidatePoint directionBased = projectAlongDirection(
                    prevLon, prevLat, prevHeading, curLon, curLat
                );
                if (directionBased != null) {
                    candidates.add(directionBased);
                }
            }
            
            // 候选4：几何优化（局部平滑）
            CandidatePoint geometryOptimized = optimizeByGeometry(
                prevLon, prevLat, prevHeading, curLon, curLat
            );
            if (geometryOptimized != null) {
                candidates.add(geometryOptimized);
            }
            
            // 综合评分：选择最优候选点
            CandidatePoint best = selectBestCandidate(
                candidates, prev, current, prevLon, prevLat, prevHeading, curLon, curLat
            );
            
            if (best == null || "original".equals(best.method)) {
                // 无有效纠偏或原点最优
                return null;
            }
            
            // 返回最优修正点
            Map<String, Object> rematched = new HashMap<>(current);
            rematched.put("longitude", best.longitude);
            rematched.put("latitude", best.latitude);
            rematched.put("heading", best.heading);
            rematched.put("rematch_method", best.method);
            rematched.put("rematch_score", best.score);
            return rematched;
            
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 候选修正点（用于综合评分）
     */
    private static class CandidatePoint {
        double longitude;
        double latitude;
        double heading;
        String method;      // 生成方法：original, road_projection, direction_based, geometry_optimized
        double score = 0.0; // 综合评分（越高越好）
        
        CandidatePoint(double lon, double lat, double heading, String method) {
            this.longitude = lon;
            this.latitude = lat;
            this.heading = heading;
            this.method = method;
        }
    }
    
    /**
     * 综合评分选择最优候选点
     * 
     * 评分维度：
     * 1. 轨迹连续性 (40%)：速度、加速度合理性
     * 2. 方向一致性 (30%)：与前一点及道路方向的连续性
     * 3. 距离惩罚 (20%)：与原始点的偏离程度
     * 4. 道路约束 (10%)：是否在道路上（如果有road_id）
     */
    private CandidatePoint selectBestCandidate(
            List<CandidatePoint> candidates,
            Map<String, Object> prev, Map<String, Object> current,
            double prevLon, double prevLat, double prevHeading,
            double curLon, double curLat) {
        
        if (candidates.isEmpty()) {
            return null;
        }
        
        CandidatePoint bestCandidate = null;
        double bestScore = -1.0;
        
        for (CandidatePoint candidate : candidates) {
            double score = 0.0;
            
            // 1. 轨迹连续性评分 (40%)
            double trajScore = evaluateTrajectoryConsistency(
                prevLon, prevLat, candidate.longitude, candidate.latitude, prev, current
            );
            score += trajScore * 0.4;
            
            // 2. 方向一致性评分 (30%)
            double dirScore = evaluateDirectionConsistency(
                prevHeading, candidate.heading
            );
            score += dirScore * 0.3;
            
            // 3. 距离惩罚 (20%) - 与原始点接近更好
            double distToOriginal = calculateDistance(curLon, curLat, 
                                                     candidate.longitude, candidate.latitude);
            double distScore = Math.exp(-distToOriginal / 50.0); // 50米为衰减尺度
            score += distScore * 0.2;
            
            // 4. 道路约束评分 (10%)
            double roadScore = 1.0;
            if ("road_projection".equals(candidate.method)) {
                roadScore = 1.0; // 道路投影点最高分
            } else if ("direction_based".equals(candidate.method)) {
                roadScore = 0.8; // 方向纠偏次之
            } else if ("geometry_optimized".equals(candidate.method)) {
                roadScore = 0.6; // 几何优化再次
            } else {
                roadScore = 0.3; // 原点最低
            }
            score += roadScore * 0.1;
            
            candidate.score = score;
            
            if (score > bestScore) {
                bestScore = score;
                bestCandidate = candidate;
            }
        }
        
        // 如果最优候选点评分不够高（<0.5），返回null
        if (bestCandidate != null && bestCandidate.score < 0.5) {
            return null;
        }
        
        return bestCandidate;
    }
    
    /**
     * 评估轨迹连续性：速度、加速度合理性
     */
    private double evaluateTrajectoryConsistency(
            double prevLon, double prevLat, double candLon, double candLat,
            Map<String, Object> prev, Map<String, Object> current) {
        
        double distance = calculateDistance(prevLon, prevLat, candLon, candLat);
        long timeDiff = getCachedTimeDifference(prev, current);
        
        if (timeDiff <= 0 || timeDiff == Long.MAX_VALUE) {
            return 0.5; // 无法计算，中等分数
        }
        
        double speed = (distance / 1000.0) / (timeDiff / 3600000.0); // km/h
        
        // 速度合理性：20-80 km/h 为最优，超出范围递减
        double speedScore;
        if (speed >= 20 && speed <= 80) {
            speedScore = 1.0;
        } else if (speed < 20) {
            speedScore = speed / 20.0;
        } else if (speed <= 120) {
            speedScore = 1.0 - (speed - 80) / 80.0;
        } else {
            speedScore = Math.exp(-(speed - 120) / 40.0);
        }
        
        return Math.max(0.0, Math.min(1.0, speedScore));
    }
    
    /**
     * 评估方向一致性
     */
    private double evaluateDirectionConsistency(double prevHeading, double candHeading) {
        double headingDiff = Math.abs(candHeading - prevHeading);
        if (headingDiff > 180) {
            headingDiff = 360 - headingDiff;
        }
        
        // 方向差越小，分数越高
        if (headingDiff <= 30) {
            return 1.0;
        } else if (headingDiff <= 90) {
            return 1.0 - (headingDiff - 30) / 60.0;
        } else {
            return Math.exp(-(headingDiff - 90) / 60.0);
        }
    }
    
    /**
     * 生成候选点：MongoDB道路投影
     */
    private CandidatePoint projectToRoadGeometry(double curLon, double curLat, 
                                                 String curRoadId, String prevRoadId) {
        try {
            Map<String, Object> result = rematchUsingRoadGeometry(
                null, null, curLon, curLat, curRoadId, prevRoadId
            );
            if (result != null) {
                return new CandidatePoint(
                    safeDouble(result.get("longitude")),
                    safeDouble(result.get("latitude")),
                    safeDouble(result.get("heading")),
                    "road_projection"
                );
            }
        } catch (Exception e) {
            // 忽略错误
        }
        return null;
    }
    
    /**
     * 生成候选点：沿前一点方向投影
     */
    private CandidatePoint projectAlongDirection(double prevLon, double prevLat, double prevHeading,
                                                  double curLon, double curLat) {
        try {
            double distance = calculateDistance(prevLon, prevLat, curLon, curLat);
            if (distance < 10 || distance > 500) {
                return null; // 距离太近或太远，不适合方向投影
            }
            
            // 沿前一点方向投影当前点
            double rad = Math.toRadians(prevHeading);
            double projLat = prevLat + (distance / 110540.0) * Math.sin(rad);
            double projLon = prevLon + (distance / (111320.0 * Math.cos(Math.toRadians(prevLat)))) * Math.cos(rad);
            
            return new CandidatePoint(projLon, projLat, prevHeading, "direction_based");
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 生成候选点：几何优化（局部平滑）
     */
    private CandidatePoint optimizeByGeometry(double prevLon, double prevLat, double prevHeading,
                                              double curLon, double curLat) {
        try {
            double bearing = calculateBearing(prevLon, prevLat, curLon, curLat);
            
            // 沿当前方向回退一点点（10-20米），寻求平滑
            double stepMeters = 15.0;
            double rad = Math.toRadians(bearing);
            double dx = Math.cos(rad) * stepMeters / 111320.0;
            double dy = Math.sin(rad) * stepMeters / 110540.0;
            
            double optimizedLon = curLon - dx;
            double optimizedLat = curLat - dy;
            
            // 计算优化后的方向（前点→优化点）
            double optimizedHeading = calculateBearing(prevLon, prevLat, optimizedLon, optimizedLat);
            
            return new CandidatePoint(optimizedLon, optimizedLat, optimizedHeading, "geometry_optimized");
        } catch (Exception e) {
            return null;
        }
    }
    
    /**
     * 使用MongoDB中的道路几何信息进行精确重匹配
     * 这是最准确的重匹配方法，将点投影到实际道路线上
     * 
     * MongoDB数据结构（GeoJSON Feature格式）：
     * {
     *   "id": "way/494982440",
     *   "type": "Feature",
     *   "geometry": {
     *     "type": "LineString",
     *     "coordinates": [[lng, lat], ...]
     *   },
     *   "properties": { ... }
     * }
     */
    private Map<String, Object> rematchUsingRoadGeometry(Map<String, Object> current, Map<String, Object> prev,
                                                          double curLon, double curLat, 
                                                          String curRoadId, String prevRoadId) {
        try {
            if (mongoClient == null) {
                return null;
            }
            
            // 查询MongoDB获取道路几何信息
            // 数据库: MapTools, Collection: 道路数据
            // 数据格式: GeoJSON Feature { "id": "way/xxx", "geometry": {...} }
            com.mongodb.client.MongoDatabase db = mongoClient.getDatabase("MapTools");
            com.mongodb.client.MongoCollection<org.bson.Document> collection = db.getCollection("道路数据");
            
            // 使用 "id" 字段查询（如 "way/494982440"）
            org.bson.Document query = new org.bson.Document("id", curRoadId);
            org.bson.Document roadDoc = collection.find(query).first();
            
            if (roadDoc == null) {
                // 找不到道路，可能road_id格式不匹配或道路不存在
                return null;
            }
            
            // 验证是否为GeoJSON Feature
            String type = roadDoc.getString("type");
            if (!"Feature".equals(type)) {
                return null; // 不是GeoJSON Feature格式
            }
            
            // 获取道路几何信息
            org.bson.Document geometry = roadDoc.get("geometry", org.bson.Document.class);
            if (geometry == null) {
                return null; // 没有geometry字段
            }
            
            String geometryType = geometry.getString("type");
            if (!"LineString".equals(geometryType) && !"MultiLineString".equals(geometryType)) {
                return null; // 只支持LineString和MultiLineString
            }
            
            // 获取坐标（处理LineString和MultiLineString两种情况）
            java.util.List<java.util.List<Double>> coordinates = null;
            
            if ("LineString".equals(geometryType)) {
                // LineString: coordinates 是 [[lng, lat], ...]
                @SuppressWarnings("unchecked")
                java.util.List<java.util.List<Double>> coords = 
                    (java.util.List<java.util.List<Double>>) geometry.get("coordinates");
                coordinates = coords;
            } else if ("MultiLineString".equals(geometryType)) {
                // MultiLineString: coordinates 是 [[[lng, lat], ...], [[lng, lat], ...], ...]
                // 取第一条线（或找最近的线）
                @SuppressWarnings("unchecked")
                java.util.List<java.util.List<java.util.List<Double>>> multiCoords = 
                    (java.util.List<java.util.List<java.util.List<Double>>>) geometry.get("coordinates");
                if (multiCoords != null && !multiCoords.isEmpty()) {
                    coordinates = multiCoords.get(0); // 简化处理，取第一条线
                }
            }
            
            if (coordinates == null || coordinates.size() < 2) {
                return null; // 坐标点太少
            }
            
            // 将当前点投影到道路线上（找最近的投影点）
            double[] projectedPoint = projectPointToRoad(curLon, curLat, coordinates);
            if (projectedPoint == null) {
                return null;
            }
            
            double projectedLon = projectedPoint[0];
            double projectedLat = projectedPoint[1];
            
            // 计算投影距离（偏离道路的距离）
            double projectionDistance = calculateDistance(curLon, curLat, projectedLon, projectedLat);
            
            // 如果投影距离合理（不超过100米），使用投影点
            if (projectionDistance < 100.0) {
                // 计算投影点处的道路方向
                double roadHeading = calculateRoadHeadingAtPoint(projectedLon, projectedLat, coordinates);
                
                Map<String, Object> rematched = new HashMap<>(current);
                rematched.put("longitude", projectedLon);
                rematched.put("latitude", projectedLat);
                rematched.put("heading", roadHeading);
                rematched.put("distance_to_road", projectionDistance);
                rematched.put("rematch_method", "road_geometry_projection");
                return rematched;
            }
            
            return null; // 投影距离太远，放弃
            
        } catch (Exception e) {
            // MongoDB查询失败，返回null让后续策略处理
            return null;
        }
    }
    
    /**
     * 将点投影到道路LineString上（找最近的投影点）
     * @return [longitude, latitude] 或 null
     */
    private double[] projectPointToRoad(double pointLon, double pointLat, 
                                       java.util.List<java.util.List<Double>> roadCoordinates) {
        double minDistance = Double.MAX_VALUE;
        double[] closestProjection = null;
        
        // 遍历道路的每一段，找到最近的投影点
        for (int i = 0; i < roadCoordinates.size() - 1; i++) {
            java.util.List<Double> p1 = roadCoordinates.get(i);
            java.util.List<Double> p2 = roadCoordinates.get(i + 1);
            
            double x1 = p1.get(0), y1 = p1.get(1);
            double x2 = p2.get(0), y2 = p2.get(1);
            
            // 计算点到线段的投影
            double[] projection = projectPointToSegment(pointLon, pointLat, x1, y1, x2, y2);
            double distance = calculateDistance(pointLon, pointLat, projection[0], projection[1]);
            
            if (distance < minDistance) {
                minDistance = distance;
                closestProjection = projection;
            }
        }
        
        return closestProjection;
    }
    
    /**
     * 将点投影到线段上
     * @return [longitude, latitude]
     */
    private double[] projectPointToSegment(double px, double py, double x1, double y1, double x2, double y2) {
        double dx = x2 - x1;
        double dy = y2 - y1;
        
        if (dx == 0 && dy == 0) {
            // 线段退化为点
            return new double[]{x1, y1};
        }
        
        // 计算投影参数 t
        double t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
        
        // 夹紧到 [0, 1]，确保投影点在线段上
        t = Math.max(0.0, Math.min(1.0, t));
        
        // 计算投影点
        double projX = x1 + t * dx;
        double projY = y1 + t * dy;
        
        return new double[]{projX, projY};
    }
    
    /**
     * 计算道路在指定点处的方向（heading）
     */
    private double calculateRoadHeadingAtPoint(double lon, double lat, 
                                               java.util.List<java.util.List<Double>> roadCoordinates) {
        // 找到距离该点最近的道路段
        int closestSegmentIndex = 0;
        double minDistance = Double.MAX_VALUE;
        
        for (int i = 0; i < roadCoordinates.size() - 1; i++) {
            java.util.List<Double> p1 = roadCoordinates.get(i);
            java.util.List<Double> p2 = roadCoordinates.get(i + 1);
            
            double midLon = (p1.get(0) + p2.get(0)) / 2.0;
            double midLat = (p1.get(1) + p2.get(1)) / 2.0;
            
            double distance = calculateDistance(lon, lat, midLon, midLat);
            if (distance < minDistance) {
                minDistance = distance;
                closestSegmentIndex = i;
            }
        }
        
        // 计算该段的方向
        java.util.List<Double> p1 = roadCoordinates.get(closestSegmentIndex);
        java.util.List<Double> p2 = roadCoordinates.get(closestSegmentIndex + 1);
        
        return calculateBearing(p1.get(0), p1.get(1), p2.get(0), p2.get(1));
    }

    private double safeHeading(Object headingObj) {
        try {
            if (headingObj == null) return 0.0;
            return ((Number) headingObj).doubleValue();
        } catch (Exception e) {
            return 0.0;
        }
    }

    private double safeDouble(Object obj) {
        try {
            if (obj == null) return 0.0;
            return ((Number) obj).doubleValue();
        } catch (Exception e) {
            try {
                return Double.parseDouble(obj.toString());
            } catch (Exception ignore) {
                return 0.0;
            }
        }
    }
    
    private String safeString(Object obj) {
        try {
            if (obj == null) return null;
            String str = obj.toString().trim();
            return str.isEmpty() ? null : str;
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 带缓存的距离计算
     */
    private double getCachedDistance(double lon1, double lat1, double lon2, double lat2) {
        // 创建缓存键（降低精度减少缓存键数量）
        String cacheKey = String.format("%.6f,%.6f,%.6f,%.6f", lon1, lat1, lon2, lat2);
        
        Double cached = distanceCache.get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        double distance = calculateDistance(lon1, lat1, lon2, lat2);
        distanceCache.put(cacheKey, distance);
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
        
        Long cached = timeDiffCache.get(cacheKey);
        if (cached != null) {
            return cached;
        }
        
        long timeDiff = calculateTimeDifference(point1, point2);
        timeDiffCache.put(cacheKey, timeDiff);
        return timeDiff;
    }

    /**
     * 计算道路切换概率（基于Valhalla Meili和GraphHopper标准）
     */
    private double calculateRoadTransitionProbability(double speed, double distance, long timeDiff) {
        // 基于速度的道路切换概率（参考GraphHopper标准）
        double speedProb = 1.0;
        if (speed > 130) { // 130 km/h是城市道路异常速度阈值（业界标准）
            speedProb = Math.exp(-(speed - 130) / 40.0); // 速度越高，概率越低
        } else if (speed < 5) {
            speedProb = 0.85; // 低速时保持较高概率（略微提高）
        }
        
        // 基于距离的合理性检查（参考Valhalla max_route_distance=2500m）
        double distanceProb = 1.0;
        if (distance > 2500) { // 超过2.5公里认为异常
            distanceProb = Math.exp(-(distance - 2500) / 1500.0);
        }
        
        // 基于时间间隔的合理性（提高到10分钟，更宽松）
        double timeProb = 1.0;
        if (timeDiff > 600000) { // 超过10分钟
            timeProb = Math.exp(-(timeDiff - 600000) / 600000.0);
        } else if (timeDiff < 1000) { // 少于1秒
            timeProb = 0.75; // 时间间隔太短，可能有问题（略微提高）
        }
        
        // 综合概率
        return speedProb * distanceProb * timeProb;
    }
    
    
    
    /**
     * 构建HMM输入
     */
    private HmmInput buildHmmInput(List<Map<String, Object>> points) {
        List<HmmGPSDataPoint> observations = new ArrayList<>();
        
        for (Map<String, Object> point : points) {
            try {
                // 提取坐标和时间信息
                Double longitude = (Double) point.get("longitude");
                Double latitude = (Double) point.get("latitude");
                Object datetimeObj = point.get("datetime");
                
                if (longitude == null || latitude == null || datetimeObj == null) {
                    continue; // 跳过不完整的点
                }
                
                // 解析时间
                Date timestamp = parseDateTime(datetimeObj);
                if (timestamp == null) {
                    continue; // 跳过时间解析失败的点
                }
                
                // 获取heading信息
                Double heading = null;
                Object headingObj = point.get("heading");
                if (headingObj != null) {
                    try {
                        heading = ((Number) headingObj).doubleValue();
                    } catch (Exception e) {
                        // 忽略heading解析错误
                    }
                }
                
                // 创建GPS数据点
                HmmGPSDataPoint gpsPoint = new HmmGPSDataPoint(longitude, latitude, timestamp, heading);
                observations.add(gpsPoint);
                
            } catch (Exception e) {
                // 跳过有问题的点
                continue;
            }
        }
        
        return new HmmInput(observations);
    }
    
    /**
     * 解析时间对象
     */
    private Date parseDateTime(Object datetimeObj) {
        try {
            if (datetimeObj instanceof Date) {
                return (Date) datetimeObj;
            } else {
                String datetime = datetimeObj.toString();
                
                // 尝试多种时间格式
                String[] formats = {
                    "EEE MMM dd HH:mm:ss zzz yyyy",  // Date.toString()格式
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
                        SimpleDateFormat sdf;
                        if (format.equals("EEE MMM dd HH:mm:ss zzz yyyy")) {
                            sdf = new SimpleDateFormat(format, java.util.Locale.ENGLISH);
                        } else {
                            sdf = new SimpleDateFormat(format);
                        }
                        sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                        return sdf.parse(datetime);
                    } catch (Exception e) {
                        // 继续尝试下一个格式
                    }
                }
            }
        } catch (Exception e) {
            // 解析失败
        }
        
        return null;
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
                        SimpleDateFormat sdf;
                        if (format.equals("EEE MMM dd HH:mm:ss zzz yyyy")) {
                            // Date.toString()格式需要ENGLISH locale
                            sdf = new SimpleDateFormat(format, java.util.Locale.ENGLISH);
                        } else {
                            sdf = new SimpleDateFormat(format);
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
    private List<Map<String, Object>> removeDuplicatePoints(List<Map<String, Object>> points) {
        List<Map<String, Object>> deduplicated = new ArrayList<>();
        
        for (int i = 0; i < points.size(); i++) {
            Map<String, Object> currentPoint = points.get(i);
            
            // 更保守的去重策略：只检查是否与上一个点完全相同
            boolean isDuplicate = false;
            if (i > 0) {
                Map<String, Object> prevPoint = points.get(i - 1);
                
                if (isSameLocation(currentPoint, prevPoint)) {
                    isDuplicate = true;
                    totalDuplicatesRemoved.incrementAndGet();
                }
            }
            
            if (!isDuplicate) {
                deduplicated.add(currentPoint);
            }
        }
        
        return deduplicated;
    }
    
    /**
     * 检查两个点是否在同一位置
     */
    private boolean isSameLocation(Map<String, Object> point1, Map<String, Object> point2) {
        double lon1 = (Double) point1.get("longitude");
        double lat1 = (Double) point1.get("latitude");
        double lon2 = (Double) point2.get("longitude");
        double lat2 = (Double) point2.get("latitude");
        
        // 经纬度完全相同（放宽精度到约1米）
        return Math.abs(lon1 - lon2) < 1e-5 && Math.abs(lat1 - lat2) < 1e-5;
    }
    
    
    /**
     * 计算两点间距离（米）
     */
    private double calculateDistance(double lon1, double lat1, double lon2, double lat2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS * c;
    }

    /**
     * 计算两点间的方位角（0-360度）
     */
    private double calculateBearing(double lon1, double lat1, double lon2, double lat2) {
        double dLon = Math.toRadians(lon2 - lon1);
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);

        double y = Math.sin(dLon) * Math.cos(lat2Rad);
        double x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
                   Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);

        double bearing = Math.toDegrees(Math.atan2(y, x));
        return (bearing + 360) % 360;
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
        stats.put("totalRematchedPoints", totalRematchedPoints.get());
        stats.put("totalRematchFailures", totalRematchFailures.get());
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
        totalRematchedPoints.set(0);
        totalRematchFailures.set(0);
        
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
        System.gc();
    }
    
}
