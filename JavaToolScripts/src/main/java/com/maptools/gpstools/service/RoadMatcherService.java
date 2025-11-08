package com.maptools.gpstools.service;

import com.maptools.gpstools.algorithm.JavaRoadMatcher;
import java.util.List;
import java.util.Map;

/**
 * 道路匹配服务类
 * 提供道路匹配相关功能的统一接口
 */
public class RoadMatcherService {
    private JavaRoadMatcher roadMatcher;
    
    public RoadMatcherService() {
        try {
            this.roadMatcher = new JavaRoadMatcher();
        } catch (Exception e) {
            System.err.println("道路匹配器初始化失败: " + e.getMessage());
            this.roadMatcher = null;
        }
    }
    
    /**
     * 查找最近的道路
     * @param longitude 经度
     * @param latitude 纬度
     * @return 道路信息
     */
    public Object findClosestRoad(double longitude, double latitude) {
        if (roadMatcher != null) {
            return roadMatcher.findClosestRoad(longitude, latitude);
        }
        return null;
    }
    
    /**
     * 批量道路匹配
     * @param points 轨迹点列表
     * @return 匹配后的轨迹点列表
     */
    public List<Map<String, Object>> matchGpsToRoads(List<Map<String, Object>> points) {
        if (roadMatcher != null) {
            return roadMatcher.matchGpsToRoads(points);
        }
        return points;
    }
    
    /**
     * 关闭道路匹配器
     */
    public void close() {
        if (roadMatcher != null) {
            roadMatcher.close();
        }
    }
}