package com.maptools.gpstools.algorithm;

import java.util.Set;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

/**
 * 道路切换模型类
 * 负责计算轨迹点之间的道路切换概率
 */
public class RoadTransitionModel {
    
    // 定义高速公路类型标识符集合
    private static final Set<String> HIGHWAY_TYPES = new HashSet<>();
    
    static {
        // 添加常见的高速公路类型标识符
        HIGHWAY_TYPES.add("motorway");
        HIGHWAY_TYPES.add("trunk");
        HIGHWAY_TYPES.add("高速公路");
        HIGHWAY_TYPES.add("高速");
        HIGHWAY_TYPES.add("gao su");
        HIGHWAY_TYPES.add("expressway");
    }
    
    /**
     * 检查道路是否为高速公路
     * 
     * @param roadType 道路类型字符串
     * @return 是否为高速公路
     */
    private boolean isHighway(String roadType) {
        if (roadType == null || roadType.isEmpty()) {
            return false;
        }
        
        // 转换为小写进行比较
        String lowerRoadType = roadType.toLowerCase();
        
        // 直接匹配
        if (HIGHWAY_TYPES.contains(lowerRoadType)) {
            return true;
        }
        
        // 模糊匹配（包含关键字）
        for (String highwayType : HIGHWAY_TYPES) {
            if (lowerRoadType.contains(highwayType)) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * 计算道路切换概率（基于距离和时间）
     * 
     * @param distance 两点间距离（米）
     * @param timeDiff 两点间时间差（毫秒）
     * @param roadType 道路类型（用于区分高速公路和普通道路）
     * @return 道路切换概率（0.0-1.0）
     */
    public double calculateRoadTransitionProbability(double distance, long timeDiff, String roadType) {
        // 判断是否为高速公路
        boolean isHighway = isHighway(roadType);
        
        // 将时间差从毫秒转换为秒
        double timeDiffSeconds = timeDiff / 1000.0;
        
        // 根据道路类型和时间差计算合理的最大距离
        // 针对高速公路适当放宽限制，因为高速行驶时GPS误差会被放大
        double maxReasonableDistance;
        if (isHighway) {
            // 高速公路速度范围：80-120 km/h (22.2-33.3 m/s)
            // 使用平均速度100 km/h (27.8 m/s) 作为基准，但考虑GPS误差适当放宽
            double avgSpeed = 27.8; // 100 km/h
            double maxSpeed = 41.7; // 150 km/h (考虑到超速情况)
            
            // 基于平均速度计算基础距离，并增加容差
            maxReasonableDistance = timeDiffSeconds * avgSpeed;
            
            // 考虑最大速度情况下的距离
            double maxDistance = timeDiffSeconds * maxSpeed;
            
            // 综合考虑两种速度情况，设置更合理的距离范围
            // 至少5000米，最多根据时间计算（适度放宽高速公路距离限制）
            maxReasonableDistance = Math.max(5000, Math.min(maxReasonableDistance * 1.3, maxDistance));
        } else {
            // 普通道路速度范围：30-60 km/h (8.3-16.7 m/s)
            // 使用平均速度45 km/h (12.5 m/s) 作为基准
            double avgSpeed = 12.5; // 45 km/h
            double maxSpeed = 16.7; // 60 km/h
            
            // 基于平均速度计算基础距离
            maxReasonableDistance = timeDiffSeconds * avgSpeed;
            
            // 考虑最大速度情况下的距离
            double maxDistance = timeDiffSeconds * maxSpeed;
            
            // 综合考虑两种速度情况，设置更合理的距离范围
            // 至少1500米，最多根据时间计算
            maxReasonableDistance = Math.max(1500, Math.min(maxReasonableDistance * 1.2, maxDistance));
        }
        
        // 计算基于距离和时间的评分
        double distanceScore;
        if (distance <= maxReasonableDistance * 0.8) {
            // 距离小于最大合理距离的80%，概率为1.0
            distanceScore = 1.0;
        } else if (distance <= maxReasonableDistance) {
            // 距离在最大合理距离的80%到最大合理距离之间，线性下降
            distanceScore = 1.0 - (distance - maxReasonableDistance * 0.8) / (maxReasonableDistance * 0.2);
        } else {
            // 超过最大合理距离，指数衰减但不低于0.3
            distanceScore = 0.3 + 0.7 * Math.exp(-(distance - maxReasonableDistance) / maxReasonableDistance);
        }
        
        return Math.max(0.0, Math.min(1.0, distanceScore));
    }
    
    /**
     * 计算道路切换概率（基于距离和时间）- 兼容旧版本API
     * 
     * @param distance 两点间距离（米）
     * @param timeDiff 两点间时间差（毫秒）
     * @return 道路切换概率（0.0-1.0）
     */
    public double calculateRoadTransitionProbability(double distance, long timeDiff) {
        // 默认使用普通道路标准
        return calculateRoadTransitionProbability(distance, timeDiff, null);
    }
    
    /**
     * 评估道路一致性（考虑前后高置信度点）
     * 
     * @param points 轨迹点列表
     * @param currentIndex 当前点索引
     * @param confidences 置信度数组
     * @return 道路一致性评分（0.0-1.0）
     */
    public double evaluateRoadConsistencyWithConfidence(List<Map<String, Object>> points, int currentIndex, double[] confidences) {
        if (points == null || points.isEmpty() || currentIndex < 0 || currentIndex >= points.size()) {
            return 1.0;
        }
        
        // 获取当前点的道路ID
        String currentRoadId = safeString(points.get(currentIndex).get("road_id"));
        if (currentRoadId == null || currentRoadId.isEmpty()) {
            return 1.0; // 如果没有道路ID，返回默认值1.0而不是0.0
        }
        
        // 查找前后高置信度点
        int prevHighConfidenceIndex = findPreviousHighConfidencePoint(currentIndex, confidences);
        int nextHighConfidenceIndex = findNextHighConfidencePoint(currentIndex, confidences);
        
        // 计算与前一个高置信度点的一致性
        double prevConsistency = 1.0;
        if (prevHighConfidenceIndex >= 0) {
            String prevRoadId = safeString(points.get(prevHighConfidenceIndex).get("road_id"));
            if (prevRoadId != null && !prevRoadId.equals(currentRoadId)) {
                prevConsistency = 0.5; // 不同的道路，返回中等评分
            }
        }
        
        // 计算与后一个高置信度点的一致性
        double nextConsistency = 1.0;
        if (nextHighConfidenceIndex >= 0 && nextHighConfidenceIndex < points.size()) {
            String nextRoadId = safeString(points.get(nextHighConfidenceIndex).get("road_id"));
            if (nextRoadId != null && !nextRoadId.equals(currentRoadId)) {
                nextConsistency = 0.5; // 不同的道路，返回中等评分
            }
        }
        
        // 综合前后一致性评分
        return (prevConsistency + nextConsistency) / 2.0;
    }
    
    /**
     * 评估道路一致性（向后兼容）
     * 
     * @param roadId 当前点的道路ID
     * @param prevRoadId 前一点的道路ID
     * @return 道路一致性评分（0.0-1.0）
     */
    public double evaluateRoadConsistency(String roadId, String prevRoadId) {
        if (roadId == null || roadId.isEmpty()) {
            return 1.0; // 如果没有道路ID，返回默认值1.0而不是0.0
        }
        
        if (prevRoadId != null && prevRoadId.equals(roadId)) {
            return 1.0; // 同一条道路
        } else {
            return 0.5; // 不同的道路，返回中等评分
        }
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
     * 安全提取String值
     */
    private String safeString(Object obj) {
        if (obj instanceof String) {
            return (String) obj;
        }
        return "";
    }
}