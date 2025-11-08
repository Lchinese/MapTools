package com.maptools.gpstools.algorithm;

import java.util.List;
import java.util.Map;

/**
 * 相邻一致性模型类
 * 负责计算轨迹点之间的几何连续性一致性
 */
public class AdjacencyConsistencyModel {
    
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    /**
     * 计算相邻一致性（使用置信度基准的版本）
     * 
     * @param points 轨迹点列表
     * @param metrics 预计算的轨迹指标
     * @param confidences 置信度数组
     * @return 一致性评分数组
     */
    public double[] calculateAdjacencyConsistencyWithConfidence(
            List<Map<String, Object>> points, 
            com.maptools.gpstools.processor.TrajectoryCorrectionProcessor.TrajectoryMetrics metrics,
            double[] confidences) {
        int n = points.size();
        double[] result = new double[n];
        if (n == 0) return result;
        result[0] = 1.0;
        if (n == 1) return result;
        
        // 定义置信度阈值
        final double CONFIDENCE_THRESHOLD = 0.6;
        
        for (int i = 1; i < n; i++) {
            // 查找参考点（前一个高置信度点）
            int referenceIndex = findPreviousHighConfidencePoint(i, confidences);
            
            // 如果参考点就是直接前点，使用标准计算
            if (referenceIndex == i - 1) {
                // 使用预计算的方向变化
                double headingDiff = metrics.headingDiffs[i];
                // 标准方向评分函数，处理NaN值
                double headingScore = (!Double.isNaN(headingDiff) && headingDiff <= 180) ? Math.exp(-headingDiff / 60.0) : 1.0;
                
                // 曲率（需要前后点）
                double curvatureScore = 1.0;
                if (i >= 2) {
                    // 使用预计算的方向变化
                    double diff1 = metrics.headingDiffs[i - 1];
                    double diff2 = metrics.headingDiffs[i];
                    // 处理NaN值
                    if (!Double.isNaN(diff1) && !Double.isNaN(diff2)) {
                        double curvatureChange = Math.abs(diff2 - diff1);
                        curvatureScore = Math.exp(-curvatureChange / 60.0);
                    }
                }
                
                // 直线跨越惩罚：使用预计算的距离和速度
                double distance = metrics.distances[i];
                double speed = metrics.speeds[i];
                long dt = metrics.timeDiffs[i];
                
                double straightPenalty = 1.0;
                if (dt > 0 && dt != Long.MAX_VALUE) {
                    // 加强直线跨越检测条件：距离超过200米且速度超过100 km/h，或距离超过500米且速度超过150 km/h
                    if ((distance > 200 && speed > 100) || (distance > 500 && speed > 150)) {
                        // 使用更严格的惩罚函数
                        straightPenalty = Math.exp(- (distance - 200) / 300.0);
                    }
                }
                
                // 几何一致性评分
                double geometricScore = headingScore * 0.4 + curvatureScore * 0.3 + straightPenalty * 0.3;
                result[i] = Math.max(0.0, Math.min(1.0, geometricScore));
            } else {
                // 使用参考点进行一致性评估
                double referenceHeading = metrics.headings[referenceIndex];
                double currentHeading = metrics.headings[i];
                
                // 计算与参考点的方向差
                double headingDiff = 0.0;
                boolean validHeading = false;
                if (!Double.isNaN(referenceHeading) && !Double.isNaN(currentHeading)) {
                    headingDiff = Math.abs(currentHeading - referenceHeading);
                    if (headingDiff > 180) {
                        headingDiff = 360 - headingDiff;
                    }
                    validHeading = true;
                }
                
                // 方向评分（参考点距离越远，衰减越大）
                double distanceDecay = calculateDistanceDecayFactor(i, referenceIndex, metrics);
                double headingScore = validHeading ? (headingDiff <= 180 ? Math.exp(-headingDiff / 60.0) * distanceDecay : 0.0) : 1.0;
                
                // 与参考点的距离和时间评估
                double totalDistance = 0.0;
                long totalTime = 0L;
                for (int j = referenceIndex + 1; j <= i; j++) {
                    totalDistance += metrics.distances[j];
                    totalTime += metrics.timeDiffs[j];
                }
                
                // 速度合理性检查
                double avgSpeed = 0.0;
                if (totalTime > 0 && totalTime != Long.MAX_VALUE) {
                    avgSpeed = (totalDistance / 1000.0) / (totalTime / 3600000.0);
                }
                
                double speedScore = 1.0;
                if (avgSpeed > 150 || avgSpeed < 5) {
                    speedScore = 0.5;
                }
                
                // 几何一致性评分
                double geometricScore = headingScore * 0.5 + speedScore * 0.3;
                result[i] = Math.max(0.0, Math.min(1.0, geometricScore));
            }
        }
        
        return result;
    }
    
    /**
     * 查找前一个高置信度点
     */
    private int findPreviousHighConfidencePoint(int currentIndex, double[] confidences) {
        // 如果置信度数组为null或为空，直接返回前一个点
        if (confidences == null || confidences.length == 0) {
            return Math.max(0, currentIndex - 1);
        }
        
        // 向前查找最近的高置信度点
        for (int i = currentIndex - 1; i >= 0; i--) {
            // 检查置信度数组元素是否为NaN
            if (!Double.isNaN(confidences[i]) && confidences[i] >= 0.6) {
                return i;
            }
        }
        
        // 如果没有找到高置信度点，则使用直接前点
        return Math.max(0, currentIndex - 1);
    }
    
    /**
     * 计算距离衰减因子（随着参考点距离增加而降低评分）
     */
    private double calculateDistanceDecayFactor(int currentIndex, int referenceIndex, com.maptools.gpstools.processor.TrajectoryCorrectionProcessor.TrajectoryMetrics metrics) {
        int distanceInPoints = currentIndex - referenceIndex;
        
        // 如果使用直接前点，不衰减
        if (distanceInPoints <= 1) {
            return 1.0;
        }
        
        // 指数衰减因子
        return Math.exp(-(distanceInPoints - 1) / 3.0);
    }
}