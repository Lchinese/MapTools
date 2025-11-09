package com.maptools.gpstools.algorithm;

import java.util.Set;
import java.util.HashSet;

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
        double maxReasonableDistance;
        if (isHighway) {
            // 高速公路假设最大速度为120km/h (33.3m/s)
            maxReasonableDistance = timeDiffSeconds * 33.3;
            // 至少3000米，最多根据时间计算
            maxReasonableDistance = Math.max(3000, maxReasonableDistance);
        } else {
            // 普通道路假设最大速度为60km/h (16.7m/s)
            maxReasonableDistance = timeDiffSeconds * 16.7;
            // 至少1500米，最多根据时间计算
            maxReasonableDistance = Math.max(1500, maxReasonableDistance);
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
     * 评估道路一致性
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
}