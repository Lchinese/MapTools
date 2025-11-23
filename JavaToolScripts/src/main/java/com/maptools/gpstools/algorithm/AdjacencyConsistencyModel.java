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
        
        for (int i = 1; i < n; i++) {
            // 查找参考点（前一个和后一个高置信度点）
            int prevReferenceIndex = findPreviousHighConfidencePoint(i, confidences);
            int nextReferenceIndex = findNextHighConfidencePoint(i, confidences);
            
            // 如果参考点就是直接前点，使用标准计算
            if (prevReferenceIndex == i - 1) {
                // 使用预计算的方向变化
                double headingDiff = metrics.headingDiffs[i];
                // 改进的方向评分函数，提供更好的区分度和更合理的评分
                double headingScore = calculateImprovedHeadingScore(headingDiff);
                
                // 曲率（需要前后点）
                double curvatureScore = 1.0;
                if (i >= 2) {
                    // 使用预计算的方向变化
                    double diff1 = metrics.headingDiffs[i - 1];
                    double diff2 = metrics.headingDiffs[i];
                    // 处理NaN值
                    if (!Double.isNaN(diff1) && !Double.isNaN(diff2)) {
                        double curvatureChange = Math.abs(diff2 - diff1);
                        // 改进的曲率评分函数
                        curvatureScore = calculateImprovedCurvatureScore(curvatureChange);
                    }
                }
                
                // 几何一致性评分
                double geometricScore = headingScore * 0.5 + curvatureScore * 0.5;
                result[i] = Math.max(0.5, Math.min(1.0, geometricScore));
            } else {
                // 使用前向参考点进行一致性评估
                double referenceHeading = metrics.headings[prevReferenceIndex];
                double currentHeading = metrics.headings[i];
                
                // 计算基于经纬度的实际方向角
                double actualBearing = calculateBearing(
                    safeDouble(points.get(prevReferenceIndex).get("latitude")),
                    safeDouble(points.get(prevReferenceIndex).get("longitude")),
                    safeDouble(points.get(i).get("latitude")),
                    safeDouble(points.get(i).get("longitude"))
                );
                
                // 计算heading与实际方向的差值
                double headingDiff = 0.0;
                boolean validHeading = false;
                if (!Double.isNaN(referenceHeading) && !Double.isNaN(currentHeading)) {
                    // 计算当前点的heading与实际方向的差值
                    headingDiff = Math.abs(currentHeading - actualBearing);
                    if (headingDiff > 180) {
                        headingDiff = 360 - headingDiff;
                    }
                    validHeading = true;
                }
                
                // 曲率（需要前后点）
                double curvatureScore = 1.0;
                if (i >= 2) {
                    // 使用预计算的方向变化
                    double diff1 = metrics.headingDiffs[i - 1];
                    double diff2 = metrics.headingDiffs[i];
                    // 处理NaN值
                    if (!Double.isNaN(diff1) && !Double.isNaN(diff2)) {
                        double curvatureChange = Math.abs(diff2 - diff1);
                        // 改进的曲率评分函数
                        curvatureScore = calculateImprovedCurvatureScore(curvatureChange);
                    }
                }
                
                // 方向评分（参考点距离越远，衰减越大）
                double distanceDecay = calculateDistanceDecayFactor(i, prevReferenceIndex, metrics);
                double headingScore = validHeading ? (headingDiff <= 180 ? calculateImprovedHeadingScore(headingDiff) * distanceDecay : 0.5) : 1.0;
                
                // 如果存在后向高置信度点，也考虑其影响
                if (nextReferenceIndex != -1 && nextReferenceIndex < points.size()) {
                    double nextReferenceHeading = metrics.headings[nextReferenceIndex];
                    
                    // 计算到后向参考点的实际方向角
                    double actualBearingToNext = calculateBearing(
                        safeDouble(points.get(i).get("latitude")),
                        safeDouble(points.get(i).get("longitude")),
                        safeDouble(points.get(nextReferenceIndex).get("latitude")),
                        safeDouble(points.get(nextReferenceIndex).get("longitude"))
                    );
                    
                    double nextHeadingDiff = 0.0;
                    boolean validNextHeading = false;
                    
                    if (!Double.isNaN(nextReferenceHeading) && !Double.isNaN(currentHeading)) {
                        // 计算当前点的heading与到后向参考点实际方向的差值
                        nextHeadingDiff = Math.abs(currentHeading - actualBearingToNext);
                        if (nextHeadingDiff > 180) {
                            nextHeadingDiff = 360 - nextHeadingDiff;
                        }
                        validNextHeading = true;
                    }
                    
                    // 结合前后方向差进行评分
                    double nextHeadingScore = validNextHeading ? calculateImprovedHeadingScore(nextHeadingDiff) : 1.0;
                    headingScore = (headingScore + nextHeadingScore) / 2.0;
                }
                
                // 几何一致性评分
                double geometricScore = headingScore * 0.7 + curvatureScore * 0.3;
                result[i] = Math.max(0.5, Math.min(1.0, geometricScore));
            }
        }
        
        return result;
    }
    
    /**
     * 计算两点之间的方位角（基于经纬度）
     * 
     * @param lat1 起点纬度
     * @param lon1 起点经度
     * @param lat2 终点纬度
     * @param lon2 终点经度
     * @return 方位角（0-360度）
     */
    private double calculateBearing(double lat1, double lon1, double lat2, double lon2) {
        // 将角度转换为弧度
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);
        double deltaLonRad = Math.toRadians(lon2 - lon1);
        
        // 计算方位角
        double y = Math.sin(deltaLonRad) * Math.cos(lat2Rad);
        double x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - 
                  Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(deltaLonRad);
        double bearing = Math.toDegrees(Math.atan2(y, x));
        
        // 将结果转换为0-360度范围
        return (bearing + 360) % 360;
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
     * 查找后一个高置信度点
     */
    private int findNextHighConfidencePoint(int currentIndex, double[] confidences) {
        // 如果置信度数组为null或为空，返回-1表示未找到
        if (confidences == null || confidences.length == 0) {
            return -1;
        }
        
        // 向后查找最近的高置信度点
        for (int i = currentIndex + 1; i < confidences.length; i++) {
            // 检查置信度数组元素是否为NaN
            if (!Double.isNaN(confidences[i]) && confidences[i] >= 0.6) {
                return i;
            }
        }
        
        // 如果没有找到高置信度点，返回-1
        return -1;
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
    
    /**
     * 改进的方向评分函数
     * 提供更好的区分度和更合理的评分
     * 
     * @param headingDiff 方向差（0-180度）
     * @return 评分（0.5-1.0）
     */
    private double calculateImprovedHeadingScore(double headingDiff) {
        // 处理NaN值
        if (Double.isNaN(headingDiff)) {
            return 1.0;
        }
        
        // 确保方向差在有效范围内
        headingDiff = Math.max(0, Math.min(180, headingDiff));
        
        // 使用分段线性函数提供更好的区分度
        double score;
        if (headingDiff <= 30) {
            // 0-30度: 评分从1.0线性下降到0.9
            score = 1.0 - (headingDiff / 30.0) * 0.1;
        } else if (headingDiff <= 90) {
            // 30-90度: 评分从0.9线性下降到0.7
            score = 0.9 - ((headingDiff - 30) / 60.0) * 0.2;
        } else if (headingDiff <= 150) {
            // 90-150度: 评分从0.7线性下降到0.6
            score = 0.7 - ((headingDiff - 90) / 60.0) * 0.1;
        } else {
            // 150-180度: 评分从0.6线性下降到0.5
            score = 0.6 - ((headingDiff - 150) / 30.0) * 0.1;
        }
        
        // 确保评分不低于0.5
        return Math.max(0.5, score);
    }
    
    /**
     * 改进的曲率评分函数
     * 
     * @param curvatureChange 曲率变化
     * @return 评分（0.5-1.0）
     */
    private double calculateImprovedCurvatureScore(double curvatureChange) {
        // 处理NaN值
        if (Double.isNaN(curvatureChange)) {
            return 1.0;
        }
        
        // 使用指数衰减函数，但设置合理的下限
        double score = Math.exp(-curvatureChange / 90.0);
        return Math.max(0.5, score); // 调整最低评分为0.5
    }
}