package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
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
 * HMM模型类
 */
class HmmModel {
    private static final double NORMAL_SPEED_MEAN = 30.0; // 正常速度均值 (km/h)
    private static final double NORMAL_SPEED_VARIANCE = 100.0; // 正常速度方差
    private static final double ANOMALY_SPEED_MEAN = 80.0; // 异常速度均值 (km/h)
    private static final double ANOMALY_SPEED_VARIANCE = 400.0; // 异常速度方差
    
    /**
     * 计算轨迹点的概率（用于异常检测）
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
 */
public class TrajectoryCorrector {
    
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    private MongoClient mongoClient;
    private HmmModel hmmModel;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalDuplicatesRemoved = new AtomicLong(0);
    private AtomicLong totalAnomalousPointsRemoved = new AtomicLong(0);
    
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
        
        // 第二步：使用HMM进行异常点检测和过滤
        List<Map<String, Object>> filteredPoints = hmmBasedAnomalyDetection(deduplicatedPoints);
        int afterHmmFilter = filteredPoints.size();
        
        totalProcessed.incrementAndGet();
        
        // 调试输出：显示点数量变化
        if (originalCount != filteredPoints.size()) {
            System.out.println(String.format("Trajectory points changed: %d -> %d (Deduplication: %d, HMM anomaly detection: %d)", 
                originalCount, filteredPoints.size(), 
                originalCount - afterDeduplication, 
                afterDeduplication - afterHmmFilter));
        }
        
        return filteredPoints;
    }
    
    /**
     * 基于HMM的异常点检测（包含道路切换判定）
     */
    private List<Map<String, Object>> hmmBasedAnomalyDetection(List<Map<String, Object>> points) {
        if (points.size() < 2) {
            return points;
        }
        
        try {
            // 构建HMM输入
        HmmInput input = buildHmmInput(points);
        
            // 运行HMM算法计算每个点的概率
        double[] probabilities = hmmModel.calculatePointProbabilities(input);
        
            // 计算道路切换概率
            double[] roadTransitionProbabilities = calculateRoadTransitionProbabilities(points);
            
            // 综合判定：结合HMM概率和道路切换概率
            List<Map<String, Object>> filteredPoints = new ArrayList<>();
        for (int i = 0; i < points.size(); i++) {
                // 综合评分：HMM概率 * 道路切换概率
                double combinedScore = probabilities[i] * roadTransitionProbabilities[i];
                
                if (combinedScore > 0.5) { // 提高阈值到50%，更严格地过滤异常点
                filteredPoints.add(points.get(i));
            } else {
                totalAnomalousPointsRemoved.incrementAndGet();
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
     * 计算道路切换概率
     */
    private double[] calculateRoadTransitionProbabilities(List<Map<String, Object>> points) {
        double[] probabilities = new double[points.size()];
        
        // 第一个点默认为正常
        probabilities[0] = 1.0;
        
        for (int i = 1; i < points.size(); i++) {
            Map<String, Object> currentPoint = points.get(i);
            Map<String, Object> previousPoint = points.get(i - 1);
            
            // 计算距离和时间差
            double distance = calculateDistance(
                (Double) previousPoint.get("longitude"), (Double) previousPoint.get("latitude"),
                (Double) currentPoint.get("longitude"), (Double) currentPoint.get("latitude")
            );
            
            long timeDiff = calculateTimeDifference(previousPoint, currentPoint);
            
            if (timeDiff > 0 && timeDiff != Long.MAX_VALUE) {
                double speed = (distance / 1000.0) / (timeDiff / 3600000.0); // km/h
                
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
     * 计算道路切换概率（包含方向变化检测）
     */
    private double calculateRoadTransitionProbability(double speed, double distance, long timeDiff) {
        // 基于速度的道路切换概率
        double speedProb = 1.0;
        if (speed > 120) {
            speedProb = Math.exp(-(speed - 120) / 50.0); // 速度越高，概率越低
        } else if (speed < 5) {
            speedProb = 0.8; // 低速时保持较高概率
        }
        
        // 基于距离的合理性检查
        double distanceProb = 1.0;
        if (distance > 1000) { // 超过1公里
            distanceProb = Math.exp(-(distance - 1000) / 2000.0);
        }
        
        // 基于时间间隔的合理性
        double timeProb = 1.0;
        if (timeDiff > 300000) { // 超过5分钟
            timeProb = Math.exp(-(timeDiff - 300000) / 600000.0);
        } else if (timeDiff < 1000) { // 少于1秒
            timeProb = 0.7; // 时间间隔太短，可能有问题
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
