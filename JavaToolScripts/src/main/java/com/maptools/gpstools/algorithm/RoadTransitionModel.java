package com.maptools.gpstools.algorithm;

/**
 * 道路切换模型类
 * 负责计算轨迹点之间的道路切换概率
 */
public class RoadTransitionModel {
    
    /**
     * 计算道路切换概率（基于距离）
     * 
     * @param distance 两点间距离（米）
     * @param timeDiff 两点间时间差（毫秒）
     * @return 道路切换概率（0.0-1.0）
     */
    public double calculateRoadTransitionProbability(double distance, long timeDiff) {
        // 道路切换概率主要基于距离，而非速度
        double distanceScore;
        if (distance <= 1000) {
            // 1000米以内，概率为1.0
            distanceScore = 1.0;
        } else if (distance <= 2000) {
            // 1000-2000米，线性下降到0.5
            distanceScore = 1.0 - (distance - 1000) / 2000.0;
        } else {
            // 超过2000米，指数衰减但不低于0.5
            distanceScore = 0.5 + 0.5 * Math.exp(-(distance - 2000) / 1000.0);
        }
        
        return Math.max(0.0, Math.min(1.0, distanceScore));
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