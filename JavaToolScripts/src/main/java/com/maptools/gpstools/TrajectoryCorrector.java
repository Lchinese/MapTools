package com.maptools.gpstools;

import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 轨迹修正处理器
 * 检测并移除异常点，进行基本的轨迹清理
 */
public class TrajectoryCorrector {
    
    private static final double SPEED_THRESHOLD = 120.0; // 120km/h以上视为异常速度（更宽松的阈值）
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    private MongoClient mongoClient;
    
    // 统计信息
    private AtomicLong totalProcessed = new AtomicLong(0);
    private AtomicLong totalSkipped = new AtomicLong(0);
    private AtomicLong totalDuplicatesRemoved = new AtomicLong(0);
    private AtomicLong totalAnomalousPointsRemoved = new AtomicLong(0);
    
    public TrajectoryCorrector() {
        this.mongoClient = MongoClients.create("mongodb://localhost:27017");
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
        
        // 第三步：直接添加所有去重后的点，不进行距离检查和插值
        correctedPoints.addAll(deduplicatedPoints);
        
        totalProcessed.incrementAndGet();
        
        // 调试输出：显示点数量变化
        if (originalCount != correctedPoints.size()) {
            System.out.println(String.format("轨迹点数量变化: %d -> %d (异常点过滤: %d, 去重: %d)", 
                originalCount, correctedPoints.size(), 
                originalCount - afterAnomalousFilter, 
                afterAnomalousFilter - afterDeduplication));
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
                if (timeDiff > 0 && timeDiff != Long.MAX_VALUE) {
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
                } else if (timeDiff == Long.MAX_VALUE) {
                    // 时间解析失败，跳过当前点
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
