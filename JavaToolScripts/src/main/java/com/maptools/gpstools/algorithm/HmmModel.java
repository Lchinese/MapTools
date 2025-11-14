package com.maptools.gpstools.algorithm;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

import com.maptools.gpstools.processor.TrajectoryCorrectionProcessor.TrajectoryMetrics;

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
    
    // 速度模型参数（无名道路，如普通城市道路）
    private static final double NORMAL_SPEED_MEAN = 20.0; // 正常速度均值 (km/h)
    private static final double NORMAL_SPEED_VARIANCE = 100.0; // 正常速度方差 (标准差10 km/h)
    
    private static final double ANOMALY_SPEED_MEAN = 60.0; // 异常速度均值 (km/h)
    private static final double ANOMALY_SPEED_VARIANCE = 400.0; // 异常速度方差 (标准差20 km/h)
    
    // 有名道路速度模型参数（如高速公路）- 更宽松的标准
    private static final double HIGHWAY_NORMAL_SPEED_MEAN = 60.0; // 有名道路正常速度均值 (km/h)
    private static final double HIGHWAY_NORMAL_SPEED_VARIANCE = 900.0; // 有名道路正常速度方差 (标准差30 km/h)
    
    private static final double HIGHWAY_ANOMALY_SPEED_MEAN = 150.0; // 有名道路异常速度均值 (km/h)
    private static final double HIGHWAY_ANOMALY_SPEED_VARIANCE = 3600.0; // 有名道路异常速度方差 (标准差60 km/h)
    
    // 决策阈值（标准筛选）
    private static final double ACCEPT_THRESHOLD = 0.7;  // 接收阈值
    private static final double REJECT_THRESHOLD = 0.3;  // 丢弃阈值
    // 0.3 ~ 0.7 之间的点需要重匹配
    
    // 依赖的其他模型
    private RoadTransitionModel roadTransitionModel;
    private AdjacencyConsistencyModel adjacencyConsistencyModel;
    
    public HmmModel() {
        this.roadTransitionModel = new RoadTransitionModel();
        this.adjacencyConsistencyModel = new AdjacencyConsistencyModel();
    }
    
    /**
     * 从预计算的指标计算轨迹点概率（优化版本，避免重复计算）
     * 注意：方向检测已移至adjacencyConsistency，此处只关注速度统计特征
     */
    public double[] calculatePointProbabilitiesFromMetrics(TrajectoryMetrics metrics,
            List<Map<String, Object>> points) {
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
            
            // 判断是否为有名道路（存在道路ID）
            String roadId = safeString(points.get(i).get("road_id"));
            boolean isNamedRoad = roadId != null && !roadId.isEmpty() && !"null".equals(roadId);
            
            // 使用分段函数计算速度概率
            if (isNamedRoad) {
                // 有名道路（如高速公路）使用更高的速度标准
                probabilities[i] = segmentedSpeedProbabilityForNamedRoads(speed);
            } else {
                // 无名道路使用城市道路标准
                probabilities[i] = segmentedSpeedProbabilityForUnnamedRoads(speed);
            }
        }
        
        // 确保第一个点的置信度为1.0
        if (probabilities.length > 0) {
            probabilities[0] = 1.0;
        }
        
        return probabilities;
    }

    /**
     * 基于HMM的异常点检测（三维互补检测系统）
     * 结合HMM模型、道路切换模型和相邻一致性模型进行综合评估
     * 
     * 检测维度（职责分离，避免重复评估）：
     * 1. HMM概率：速度统计特征（基于高斯分布）- 权重 40%
     * 2. 道路切换概率：物理可行性（距离约束）- 权重 20%
     * 3. 相邻一致性：几何连续性（方向、曲率）- 权重 40%
     * 
     * 综合评分 = 速度统计×0.4 + 物理约束×0.2 + 几何一致性×0.4
     */
    public List<Map<String, Object>> hmmBasedAnomalyDetection(List<Map<String, Object>> points, 
            TrajectoryMetrics metrics, AtomicLong totalAnomalousPointsRemoved) {
        if (points.size() < 2) {
            return points;
        }
        
        try {
            // 维度1：HMM速度统计检测
            double[] probabilities = calculatePointProbabilitiesFromMetrics(metrics, points);
        
            // 维度2：道路切换物理可行性检测
            double[] roadTransitionProbabilities = calculateRoadTransitionProbabilities(points, metrics, probabilities);
            
            // 维度3：几何一致性检测（方向、曲率）
            // 使用基于置信度的相邻一致性评分
            double[] adjacencyConsistency = calculateAdjacencyConsistencyWithSelfConfidence(points, metrics, probabilities);
            
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
    private double[] calculateRoadTransitionProbabilities(List<Map<String, Object>> points, TrajectoryMetrics metrics, double[] confidences) {
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
            double roadConsistencyFactor = roadTransitionModel.evaluateRoadConsistencyWithConfidence(points, i, confidences);
            
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
                                                         TrajectoryMetrics metrics, double[] confidences) {
        // 使用传入的置信度数组作为初始一致性
        return adjacencyConsistencyModel.calculateAdjacencyConsistencyWithConfidence(points, metrics, confidences);
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
     * 高斯概率密度函数
     */
    private double gaussianProbability(double x, double mean, double variance) {
        double stdDev = Math.sqrt(variance);
        double coefficient = 1.0 / (stdDev * Math.sqrt(2 * Math.PI));
        double exponent = -Math.pow(x - mean, 2) / (2 * variance);
        return coefficient * Math.exp(exponent);
    }
    
    /**
     * 分段速度概率函数 - 用于无名道路
     * 0-60km/h为正常范围，60-80km/h为异常范围
     */
    private double segmentedSpeedProbabilityForUnnamedRoads(double speed) {
        if (speed < 0) {
            return 0.0;
        } else if (speed <= 60) {
            // 正常范围：线性从1.0递减到0.8
            return 1.0 - (speed / 60.0) * 0.2;
        } else if (speed <= 80) {
            // 异常范围：线性从0.8递减到0.2
            return 0.8 - ((speed - 60) / 20.0) * 0.6;
        } else {
            // 超异常范围：递减到0.0
            return Math.max(0.0, 0.2 - (speed - 80) / 80.0);
        }
    }
    
    /**
     * 分段速度概率函数 - 用于有名道路
     * 0-120km/h为正常范围，120-150km/h为异常范围
     */
    private double segmentedSpeedProbabilityForNamedRoads(double speed) {
        if (speed < 0) {
            return 0.0;
        } else if (speed <= 120) {
            // 正常范围：线性从1.0递减到0.7
            return 1.0 - (speed / 120.0) * 0.3;
        } else if (speed <= 150) {
            // 异常范围：线性从0.7递减到0.2
            return 0.7 - ((speed - 120) / 30.0) * 0.5;
        } else {
            // 超异常范围：递减到0.0
            return Math.max(0.0, 0.2 - (speed - 150) / 150.0);
        }
    }
}