package com.maptools.gpstools.util;

import org.bson.Document;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.FindIterable;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.Date;

import com.maptools.gpstools.model.GPSDataPoint;

/**
 * 轨迹修正工具类
 * 提供距离计算、点过滤、数据转换等辅助功能
 */
public class TrajectoryCorrectionUtils {
    
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    private static final double MIN_DISTANCE_THRESHOLD = 1.0; // 最小距离阈值（米）
    private static final double MAX_DISTANCE_THRESHOLD = 10000.0; // 最大距离阈值（米）
    
    /**
     * 计算两点间距离（米）
     */
    public static double calculateDistance(double lon1, double lat1, double lon2, double lat2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS * c;
    }
    
    /**
     * 验证轨迹点的有效性
     */
    public static boolean isValidTrajectoryPoint(Map<String, Object> point) {
        if (point == null) return false;
        
        try {
            Double longitude = (Double) point.get("longitude");
            Double latitude = (Double) point.get("latitude");
            
            if (longitude == null || latitude == null) return false;
            
            // 检查坐标范围
            if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) {
                return false;
            }
            
            // 检查是否有车牌号
            String plateNumber = (String) point.get("plate_number");
            if (plateNumber == null || plateNumber.trim().isEmpty()) {
                return false;
            }
            
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 过滤无效的轨迹点
     */
    public static List<Map<String, Object>> filterValidPoints(List<Map<String, Object>> points) {
        List<Map<String, Object>> validPoints = new ArrayList<>();
        
        for (Map<String, Object> point : points) {
            if (isValidTrajectoryPoint(point)) {
                validPoints.add(point);
            }
        }
        
        return validPoints;
    }
    
    /**
     * 按时间排序轨迹点
     */
    public static void sortTrajectoryPointsByTime(List<Map<String, Object>> points) {
        points.sort((p1, p2) -> {
            Object timeObj1 = p1.get("datetime");
            Object timeObj2 = p2.get("datetime");
            
            if (timeObj1 == null && timeObj2 == null) return 0;
            if (timeObj1 == null) return 1; // null值排在后面
            if (timeObj2 == null) return -1;
            
            try {
                // 尝试解析时间
                Date date1 = parseDateTime(timeObj1);
                Date date2 = parseDateTime(timeObj2);
                
                if (date1 == null && date2 == null) return 0;
                if (date1 == null) return 1;
                if (date2 == null) return -1;
                
                return date1.compareTo(date2);
            } catch (Exception e) {
                // 如果解析失败，回退到字符串比较
                String time1 = timeObj1.toString();
                String time2 = timeObj2.toString();
                return time1.compareTo(time2);
            }
        });
    }
    
    /**
     * 解析时间对象为Date
     */
    private static Date parseDateTime(Object datetimeObj) {
        if (datetimeObj == null) {
            return null;
        }
        
        // 如果已经是Date对象，直接返回
        if (datetimeObj instanceof java.util.Date) {
            return (java.util.Date) datetimeObj;
        }
        
        // 如果是字符串，尝试解析
        String datetimeStr = datetimeObj.toString();
        
        // 尝试多种时间格式
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
                java.text.SimpleDateFormat sdf;
                if (format.equals("EEE MMM dd HH:mm:ss zzz yyyy")) {
                    // Date.toString()格式需要ENGLISH locale
                    sdf = new java.text.SimpleDateFormat(format, java.util.Locale.ENGLISH);
                } else {
                    sdf = new java.text.SimpleDateFormat(format);
                }
                sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                return sdf.parse(datetimeStr);
            } catch (Exception e) {
                // 继续尝试下一个格式
            }
        }
        
        return null; // 解析失败
    }
    
    /**
     * 检测异常跳跃点
     */
    public static List<Integer> detectAnomalousJumps(List<Map<String, Object>> points, double threshold) {
        List<Integer> anomalousIndices = new ArrayList<>();
        
        for (int i = 0; i < points.size() - 1; i++) {
            Map<String, Object> currentPoint = points.get(i);
            Map<String, Object> nextPoint = points.get(i + 1);
            
            double distance = calculateDistance(
                (Double) currentPoint.get("longitude"),
                (Double) currentPoint.get("latitude"),
                (Double) nextPoint.get("longitude"),
                (Double) nextPoint.get("latitude")
            );
            
            if (distance > threshold) {
                anomalousIndices.add(i + 1); // 标记下一个点为异常点
            }
        }
        
        return anomalousIndices;
    }
    
    /**
     * 移除异常跳跃点
     */
    public static List<Map<String, Object>> removeAnomalousJumps(List<Map<String, Object>> points, double threshold) {
        List<Integer> anomalousIndices = detectAnomalousJumps(points, threshold);
        
        List<Map<String, Object>> filteredPoints = new ArrayList<>();
        
        for (int i = 0; i < points.size(); i++) {
            if (!anomalousIndices.contains(i)) {
                filteredPoints.add(points.get(i));
            }
        }
        
        return filteredPoints;
    }
    
    /**
     * 计算轨迹统计信息
     */
    public static Map<String, Object> calculateTrajectoryStatistics(List<Map<String, Object>> points) {
        Map<String, Object> stats = new HashMap<>();
        
        if (points.isEmpty()) {
            stats.put("pointCount", 0);
            stats.put("totalDistance", 0.0);
            stats.put("averageSpeed", 0.0);
            stats.put("maxSpeed", 0.0);
            stats.put("minSpeed", 0.0);
            return stats;
        }
        
        double totalDistance = 0.0;
        double totalSpeed = 0.0;
        double maxSpeed = 0.0;
        double minSpeed = Double.MAX_VALUE;
        int validSpeedCount = 0;
        
        for (int i = 0; i < points.size() - 1; i++) {
            Map<String, Object> currentPoint = points.get(i);
            Map<String, Object> nextPoint = points.get(i + 1);
            
            // 计算距离
            double distance = calculateDistance(
                (Double) currentPoint.get("longitude"),
                (Double) currentPoint.get("latitude"),
                (Double) nextPoint.get("longitude"),
                (Double) nextPoint.get("latitude")
            );
            
            totalDistance += distance;
            
            // 计算速度统计
            try {
                Double speed = (Double) currentPoint.get("speed");
                if (speed != null && speed >= 0 && speed <= 200) { // 合理的速度范围
                    totalSpeed += speed;
                    maxSpeed = Math.max(maxSpeed, speed);
                    minSpeed = Math.min(minSpeed, speed);
                    validSpeedCount++;
                }
            } catch (Exception e) {
                // 忽略速度解析错误
            }
        }
        
        stats.put("pointCount", points.size());
        stats.put("totalDistance", totalDistance);
        stats.put("averageSpeed", validSpeedCount > 0 ? totalSpeed / validSpeedCount : 0.0);
        stats.put("maxSpeed", maxSpeed == Double.MAX_VALUE ? 0.0 : maxSpeed);
        stats.put("minSpeed", minSpeed == Double.MAX_VALUE ? 0.0 : minSpeed);
        
        return stats;
    }
    
    /**
     * 将MongoDB文档转换为轨迹点
     */
    public static Map<String, Object> documentToTrajectoryPoint(Document doc) {
        Map<String, Object> point = new HashMap<>();
        
        // 安全获取数值字段，处理null值
        Double longitude = doc.getDouble("longitude");
        Double latitude = doc.getDouble("latitude");
        if (longitude == null || latitude == null) {
            return null; // 如果坐标为空，返回null
        }
        
        point.put("longitude", longitude);
        point.put("latitude", latitude);
        point.put("plate_number", doc.getString("plate_number"));
        
        // 处理datetime字段，可能是String或Date类型
        Object datetimeObj = doc.get("datetime");
        if (datetimeObj instanceof java.util.Date) {
            point.put("datetime", ((java.util.Date) datetimeObj).toString());
        } else if (datetimeObj != null) {
            point.put("datetime", datetimeObj.toString());
        } else {
            point.put("datetime", ""); // 空字符串而不是null
        }
        
        // 安全获取其他字段
        point.put("speed", doc.getDouble("speed") != null ? doc.getDouble("speed") : 0.0);
        point.put("heading", doc.getDouble("heading") != null ? doc.getDouble("heading") : 0.0);
        point.put("is_valid", doc.getBoolean("is_valid") != null ? doc.getBoolean("is_valid") : true);
        point.put("source_file", doc.getString("source_file") != null ? doc.getString("source_file") : "");
        
        // 如果有道路匹配信息
        if (doc.containsKey("road_id")) {
            point.put("road_id", doc.getString("road_id"));
            point.put("road_name", doc.getString("road_name"));
            point.put("road_type", doc.getString("road_type"));
            point.put("distance_to_road", doc.getDouble("distance_to_road"));
            point.put("matched", doc.getBoolean("matched"));
        }
        
        return point;
    }
    
    /**
     * 将轨迹点转换为MongoDB文档
     */
    public static Document trajectoryPointToDocument(Map<String, Object> point) {
        Document doc = new Document();
        
        doc.append("longitude", point.get("longitude"));
        doc.append("latitude", point.get("latitude"));
        doc.append("plate_number", point.get("plate_number"));
        
        // 修复时间格式，使其与原始轨迹保持一致
        Object datetimeObj = point.get("datetime");
        if (datetimeObj instanceof java.util.Date) {
            // 如果是Date对象，转换为标准字符串格式
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
            doc.append("datetime", sdf.format((java.util.Date) datetimeObj));
        } else if (datetimeObj != null) {
            // 如果是字符串，尝试解析后再格式化，确保格式一致
            Date parsedDate = parseDateTime(datetimeObj);
            if (parsedDate != null) {
                java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                sdf.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                doc.append("datetime", sdf.format(parsedDate));
            } else {
                // 如果解析失败，使用原始值，但确保格式正确
                String datetimeStr = datetimeObj.toString();
                // 检查是否是Date.toString()格式 (EEE MMM dd HH:mm:ss zzz yyyy)
                // 更宽松的正则表达式匹配日期格式
                if (datetimeStr.matches("[A-Z][a-z]{2} [A-Z][a-z]{2} \\\\d{1,2} \\\\d{2}:\\\\d{2}:\\\\d{2} [A-Z]{3,4} \\\\d{4}")) {
                    try {
                        // 解析Date.toString()格式
                        java.text.SimpleDateFormat inputFormat = new java.text.SimpleDateFormat("EEE MMM dd HH:mm:ss zzz yyyy", java.util.Locale.ENGLISH);
                        Date date = inputFormat.parse(datetimeStr);
                        // 转换为标准格式
                        java.text.SimpleDateFormat outputFormat = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                        outputFormat.setTimeZone(java.util.TimeZone.getTimeZone("UTC"));
                        doc.append("datetime", outputFormat.format(date));
                    } catch (Exception e) {
                        // 如果解析失败，使用原始值
                        doc.append("datetime", datetimeStr);
                    }
                } else {
                    // 不是Date.toString()格式，直接使用
                    doc.append("datetime", datetimeStr);
                }
            }
        } else {
            doc.append("datetime", "");
        }
        
        doc.append("speed", point.get("speed"));
        doc.append("heading", point.get("heading"));
        doc.append("is_valid", point.get("is_valid"));
        doc.append("source_file", point.get("source_file"));
        
        // 如果有道路匹配信息
        if (point.containsKey("road_id")) {
            doc.append("road_id", point.get("road_id"));
            doc.append("road_name", point.get("road_name"));
            doc.append("road_type", point.get("road_type"));
            doc.append("distance_to_road", point.get("distance_to_road"));
            doc.append("matched", point.get("matched"));
        }
        
        // 如果有修正标记
        if (point.containsKey("corrected")) {
            doc.append("corrected", point.get("corrected"));
        }
        
        return doc;
    }
    
    /**
     * 创建修正轨迹文档
     */
    public static Document createCorrectedTrajectoryDocument(String plateNumber, 
                                                           List<Map<String, Object>> trajectoryPoints,
                                                           String sourceCollectionName) {
        if (trajectoryPoints == null || trajectoryPoints.isEmpty()) {
            return null;
        }
        
        // 计算统计信息
        Map<String, Object> stats = calculateTrajectoryStatistics(trajectoryPoints);
        
        // 创建轨迹点文档列表
        List<Document> trajectoryPointDocs = new ArrayList<>();
        for (Map<String, Object> point : trajectoryPoints) {
            trajectoryPointDocs.add(trajectoryPointToDocument(point));
        }
        
        Document doc = new Document()
                .append("plate_number", plateNumber)
                .append("trajectory_points", trajectoryPointDocs)
                .append("point_count", trajectoryPoints.size())
                .append("type", "corrected_trajectory")
                .append("source_collection", sourceCollectionName)
                .append("correction_time", new Date())
                .append("total_distance", stats.get("totalDistance"))
                .append("average_speed", stats.get("averageSpeed"))
                .append("max_speed", stats.get("maxSpeed"))
                .append("min_speed", stats.get("minSpeed"));
        
        return doc;
    }
    
    /**
     * 格式化距离显示
     */
    public static String formatDistance(double distanceInMeters) {
        if (distanceInMeters < 1000) {
            return String.format("%.1f米", distanceInMeters);
        } else {
            return String.format("%.2f公里", distanceInMeters / 1000);
        }
    }
    
    /**
     * 格式化时间显示
     */
    public static String formatDuration(long durationInMillis) {
        long seconds = durationInMillis / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        
        if (hours > 0) {
            return String.format("%d小时%d分钟", hours, minutes % 60);
        } else if (minutes > 0) {
            return String.format("%d分钟%d秒", minutes, seconds % 60);
        } else {
            return String.format("%d秒", seconds);
        }
    }
    
    /**
     * 打印进度信息
     */
    public static void printProgress(long current, long total, String operation) {
        if (total == 0) return;
        
        double percentage = (double) current / total * 100;
        int barLength = 50;
        int filledLength = (int) (barLength * current / total);
        
        StringBuilder bar = new StringBuilder();
        bar.append("[");
        for (int i = 0; i < barLength; i++) {
            if (i < filledLength) {
                bar.append("=");
            } else {
                bar.append(" ");
            }
        }
        bar.append("]");
        
        System.out.printf("\r%s %s %.1f%% (%d/%d)", operation, bar.toString(), percentage, current, total);
        
        if (current == total) {
            System.out.println();
        }
    }
}