package com.maptools.gpstools;

import org.bson.Document;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.FindIterable;
import org.locationtech.jts.geom.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 轨迹修正处理器
 * 检测远距离点并应用路径规划算法进行修正
 */
public class TrajectoryCorrector {
    
    private static final double DISTANCE_THRESHOLD = 500.0; // 500米阈值
    private static final double SPEED_THRESHOLD = 200.0; // 200km/h以上视为异常速度（更宽松的阈值）
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    private PathPlanner pathPlanner;
    private MongoClient mongoClient;
    private MongoDatabase database;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalCorrected = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalDuplicatesRemoved = new AtomicLong(0);
    private AtomicLong totalAnomalousPointsRemoved = new AtomicLong(0);
    
    public TrajectoryCorrector() {
        this.pathPlanner = new PathPlanner();
        this.mongoClient = MongoClients.create("mongodb://localhost:27017");
        this.database = mongoClient.getDatabase("MapTools");
        this.pathPlanner = new PathPlanner(database); // 重新初始化带database的PathPlanner
    }
    
    /**
     * 修正单个轨迹
     */
    public List<Map<String, Object>> correctTrajectory(List<Map<String, Object>> originalPoints) {
        if (originalPoints == null || originalPoints.size() < 2) {
            return originalPoints;
        }
        
        int originalCount = originalPoints.size();
        List<Map<String, Object>> correctedPoints = new ArrayList<>();
        
        // 第一步：检测并移除异常点
        List<Map<String, Object>> filteredPoints = removeAnomalousPoints(originalPoints);
        int afterAnomalousFilter = filteredPoints.size();
        
        // 第二步：移除重复的相邻点
        List<Map<String, Object>> deduplicatedPoints = removeDuplicatePoints(filteredPoints);
        int afterDeduplication = deduplicatedPoints.size();
        
        // 第三步：检测远距离点并应用路径规划
        for (int i = 0; i < deduplicatedPoints.size(); i++) {
            Map<String, Object> currentPoint = deduplicatedPoints.get(i);
            correctedPoints.add(currentPoint);
            
            // 检查是否需要路径规划
            if (i < deduplicatedPoints.size() - 1) {
                Map<String, Object> nextPoint = deduplicatedPoints.get(i + 1);
                
                double distance = calculateDistance(
                    (Double) currentPoint.get("longitude"),
                    (Double) currentPoint.get("latitude"),
                    (Double) nextPoint.get("longitude"),
                    (Double) nextPoint.get("latitude")
                );
                
                if (distance > DISTANCE_THRESHOLD) {
                    // 对于远距离点，使用简化的线性插值而不是复杂的路径规划
                    List<Map<String, Object>> interpolatedPoints = createLinearInterpolation(currentPoint, nextPoint);
                    
                    // Add interpolated points (excluding start and end points as they are already added)
                    for (int j = 1; j < interpolatedPoints.size() - 1; j++) {
                        correctedPoints.add(interpolatedPoints.get(j));
                    }
                    
                    totalCorrected.incrementAndGet();
                }
            }
        }
        
        totalProcessed.incrementAndGet();
        
        // 调试输出：显示点数量变化
        if (originalCount != correctedPoints.size()) {
            System.out.println(String.format("轨迹点数量变化: %d -> %d (异常点过滤: %d, 去重: %d, 路径规划增加: %d)", 
                originalCount, correctedPoints.size(), 
                originalCount - afterAnomalousFilter, 
                afterAnomalousFilter - afterDeduplication,
                correctedPoints.size() - afterDeduplication));
        }
        
        return correctedPoints;
    }
    
    /**
     * 检测并移除异常点（速度异常）
     */
    private List<Map<String, Object>> removeAnomalousPoints(List<Map<String, Object>> points) {
        if (points.size() < 2) {
            return points;
        }
        
        List<Map<String, Object>> filteredPoints = new ArrayList<>();
        Map<String, Object> prevPoint = null;
        
        for (int i = 0; i < points.size(); i++) {
            Map<String, Object> currentPoint = points.get(i);
            
            if (prevPoint != null) {
                // 计算距离和时间差
                Double prevLon = (Double) prevPoint.get("longitude");
                Double prevLat = (Double) prevPoint.get("latitude");
                Double currLon = (Double) currentPoint.get("longitude");
                Double currLat = (Double) currentPoint.get("latitude");
                
                if (prevLon == null || prevLat == null || currLon == null || currLat == null) {
                    // 跳过坐标不完整的点
                    totalAnomalousPointsRemoved.incrementAndGet();
                    continue;
                }
                
                double distance = calculateDistance(prevLon, prevLat, currLon, currLat);
                
                long timeDiff = calculateTimeDifference(prevPoint, currentPoint);
                
                // 检查速度是否异常
                if (timeDiff > 0) {
                    double speedKmh = (distance / 1000.0) / (timeDiff / 3600000.0); // km/h
                    if (speedKmh > SPEED_THRESHOLD) {
                        // 只跳过当前异常点，继续处理后续点
                        totalAnomalousPointsRemoved.incrementAndGet();
                        continue; // 跳过当前点，继续下一个点
                    }
                } else if (timeDiff == 0 && distance > 5000) {
                    // 时间为0但距离很大（5公里以上），可能是异常点
                    totalAnomalousPointsRemoved.incrementAndGet();
                    continue;
                }
            }
            
            filteredPoints.add(currentPoint);
            prevPoint = currentPoint;
        }
        
        return filteredPoints;
    }
    
    /**
     * 计算两个点之间的时间差（毫秒）
     */
    private long calculateTimeDifference(Map<String, Object> point1, Map<String, Object> point2) {
        try {
            String datetime1 = (String) point1.get("datetime");
            String datetime2 = (String) point2.get("datetime");
            
            if (datetime1 == null || datetime2 == null) {
                return Long.MAX_VALUE; // 无法计算时间差时返回最大值
            }
            
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            Date date1 = sdf.parse(datetime1);
            Date date2 = sdf.parse(datetime2);
            
            return Math.abs(date2.getTime() - date1.getTime());
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
     * 应用路径规划算法
     */
    private List<Map<String, Object>> applyPathPlanning(Map<String, Object> startPoint, Map<String, Object> endPoint) {
        Double startLon = (Double) startPoint.get("longitude");
        Double startLat = (Double) startPoint.get("latitude");
        Double endLon = (Double) endPoint.get("longitude");
        Double endLat = (Double) endPoint.get("latitude");
        
        if (startLon == null || startLat == null || endLon == null || endLat == null) {
            return createLinearInterpolation(startPoint, endPoint);
        }
        
        // 使用路径规划算法
        List<PathPlanner.RoadNode> path = pathPlanner.planPath(startLon, startLat, endLon, endLat);
        
        if (path.isEmpty()) {
            return createLinearInterpolation(startPoint, endPoint);
        }
        
        // 将路径转换为轨迹点
        List<Map<String, Object>> interpolatedPoints = pathPlanner.convertPathToTrajectoryPoints(path, startPoint);
        
        // 确保终点时间正确
        if (!interpolatedPoints.isEmpty()) {
            Map<String, Object> lastPoint = interpolatedPoints.get(interpolatedPoints.size() - 1);
            lastPoint.put("datetime", endPoint.get("datetime"));
            lastPoint.put("speed", endPoint.get("speed"));
            lastPoint.put("heading", endPoint.get("heading"));
        }
        
        return interpolatedPoints;
    }
    
    /**
     * 创建直线插值（备选方案）
     */
    private List<Map<String, Object>> createLinearInterpolation(Map<String, Object> startPoint, Map<String, Object> endPoint) {
        List<Map<String, Object>> interpolatedPoints = new ArrayList<>();
        
        double startLon = (Double) startPoint.get("longitude");
        double startLat = (Double) startPoint.get("latitude");
        double endLon = (Double) endPoint.get("longitude");
        double endLat = (Double) endPoint.get("latitude");
        
        // 计算插值点数量（每100米一个点）
        double distance = calculateDistance(startLon, startLat, endLon, endLat);
        int numPoints = Math.max(2, (int) (distance / 100));
        
        for (int i = 0; i <= numPoints; i++) {
            double ratio = (double) i / numPoints;
            
            Map<String, Object> interpolatedPoint = new HashMap<>();
            interpolatedPoint.put("longitude", startLon + (endLon - startLon) * ratio);
            interpolatedPoint.put("latitude", startLat + (endLat - startLat) * ratio);
            interpolatedPoint.put("plate_number", startPoint.get("plate_number"));
            interpolatedPoint.put("datetime", startPoint.get("datetime"));
            interpolatedPoint.put("speed", startPoint.get("speed"));
            interpolatedPoint.put("heading", startPoint.get("heading"));
            interpolatedPoint.put("is_valid", true);
            interpolatedPoint.put("corrected", true);
            interpolatedPoint.put("source_file", startPoint.get("source_file"));
            
            interpolatedPoints.add(interpolatedPoint);
        }
        
        return interpolatedPoints;
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
        stats.put("totalCorrected", totalCorrected.get());
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
        totalCorrected.set(0);
        totalSkipped.set(0);
        totalDuplicatesRemoved.set(0);
        totalAnomalousPointsRemoved.set(0);
    }
    
    /**
     * 关闭连接
     */
    public void close() {
        if (pathPlanner != null) {
            pathPlanner.clearMemory();
        }
        if (mongoClient != null) {
            mongoClient.close();
        }
        System.gc();
    }
}
