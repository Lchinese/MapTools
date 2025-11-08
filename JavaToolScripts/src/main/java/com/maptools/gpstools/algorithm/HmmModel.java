package com.maptools.gpstools.algorithm;

import java.util.*;

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
public class HmmModel {
    // GPS观测参数（基于GraphHopper标准 - 保留作为参考）
    // GPS_SIGMA = 4.07m - GPS测量误差标准差（业界标准值）
    // TRANSITION_BETA = 3.0 - 路由转换参数
    // 这些参数在标准HMM地图匹配中使用，此处保留供未来扩展参考
    
    // 速度模型参数（城市道路）- 调整参数使筛选更严格
    private static final double NORMAL_SPEED_MEAN = 35.0; // 降低正常速度均值 (从40.0降到35.0 km/h)
    private static final double NORMAL_SPEED_VARIANCE = 225.0; // 降低正常速度方差 (从400.0降到225.0，标准差从20降到15 km/h)
    
    private static final double ANOMALY_SPEED_MEAN = 100.0; // 降低异常速度均值 (从120.0降到100.0 km/h)
    private static final double ANOMALY_SPEED_VARIANCE = 400.0; // 降低异常速度方差 (从900.0降到400.0，标准差从30降到20 km/h)
    
    // 决策阈值（标准筛选）
    private static final double ACCEPT_THRESHOLD = 0.7;  // 接收阈值
    private static final double REJECT_THRESHOLD = 0.3;  // 丢弃阈值
    // 0.3 ~ 0.7 之间的点需要重匹配
    
    /**
     * 计算轨迹点的概率（用于异常检测）- 旧版本，保留兼容性
     */
    public double[] calculatePointProbabilities(HmmInput input) {
        List<HmmGPSDataPoint> observations = input.getObservations();
        int n = observations.size();
        
        if (n < 2) {
            double[] result = new double[n];
            // 确保第一个点的置信度为1.0
            if (n > 0) {
                result[0] = 1.0;
            }
            return result;
        }
        
        // 计算每个点的速度和方向特征
        double[] speeds = calculateSpeeds(observations);
        double[] directionChanges = calculateDirectionChanges(observations);
        
        // 使用简化的HMM前向-后向算法，结合速度和方向
        double[] probabilities = forwardBackwardAlgorithm(speeds, directionChanges);
        
        // 确保第一个点的置信度为1.0
        if (probabilities.length > 0) {
            probabilities[0] = 1.0;
        }
        
        return probabilities;
    }
    
    /**
     * 计算速度特征（用于HMM模型）
     */
    private double[] calculateSpeeds(List<HmmGPSDataPoint> observations) {
        int n = observations.size();
        double[] speeds = new double[n];
        speeds[0] = 0.0; // 第一个点速度为0
        
        for (int i = 1; i < n; i++) {
            HmmGPSDataPoint prev = observations.get(i - 1);
            HmmGPSDataPoint curr = observations.get(i);
            
            // 计算距离（米）
            double distance = calculateDistance(prev.getLongitude(), prev.getLatitude(), 
                                              curr.getLongitude(), curr.getLatitude());
            
            // 计算时间差（毫秒）
            long timeDiffMs = curr.getTimestamp().getTime() - prev.getTimestamp().getTime();
            
            // 如果时间差为0或负数，速度设为0
            if (timeDiffMs <= 0) {
                speeds[i] = 0.0;
            } else {
                // 计算速度（km/h）
                double timeDiffHours = timeDiffMs / (1000.0 * 3600.0);
                speeds[i] = (distance / 1000.0) / timeDiffHours; // 转换为 km/h
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
        
        // 确保第一个点的置信度为1.0
        if (probabilities.length > 0) {
            probabilities[0] = 1.0;
        }
        
        return probabilities;
    }
    
    /**
     * 从预计算的指标计算轨迹点概率（优化版本，避免重复计算）
     * 注意：方向检测已移至adjacencyConsistency，此处只关注速度统计特征
     */
    public double[] calculatePointProbabilitiesFromMetrics(com.maptools.gpstools.processor.TrajectoryCorrectionProcessor.TrajectoryMetrics metrics) {
        int n = metrics.speeds.length;
        
        if (n < 2) {
            double[] result = new double[n];
            // 确保第一个点的置信度为1.0
            if (n > 0) {
                result[0] = 1.0;
            }
            return result;
        }
        
        // HMM只关注速度统计特征，方向检测交给adjacencyConsistency处理（避免重复）
        double[] probabilities = new double[n];
        for (int i = 0; i < n; i++) {
            double speed = metrics.speeds[i];
            
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
        
        // 确保第一个点的置信度为1.0
        if (probabilities.length > 0) {
            probabilities[0] = 1.0;
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
     * 根据角度差计算方向变化概率（调整函数使筛选更严格）
     */
    private double calculateDirectionProbability(double angleDiff) {
        // 处理NaN值
        if (Double.isNaN(angleDiff)) {
            return 1.0; // 如果方向无效，返回默认概率
        }
        
        // 方向变化概率：角度差越大，概率越低（调整参数使筛选更严格）
        if (angleDiff > 120) { // 降低阈值（从150度降到120度）认为是掉头/回头
            return Math.exp(-(angleDiff - 120) / 20.0); // 更快的指数衰减（从30.0降到20.0）
        } else if (angleDiff > 60) { // 降低阈值（从90度降到60度）认为是急转弯
            return 0.6 + 0.4 * Math.exp(-(angleDiff - 60) / 40.0); // 调整参数（从0.7降到0.6，从60.0降到40.0）
        } else if (angleDiff > 30) { // 降低阈值（从45度降到30度）
            return 0.8; // 降低概率（从0.9降到0.8）
        } else {
            return 1.0; // 小角度变化，保持高概率
        }
    }
}