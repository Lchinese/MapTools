package com.maptools.gpstools;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import org.bson.Document;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.LineString;

import java.util.*;
import java.util.concurrent.*;

/**
 * Java道路匹配器 - 完全重写，参照Python数据结构
 * 支持多线程处理，避免类型转换问题
 */
public class JavaRoadMatcher {
    
    private static final String MONGO_CONNECTION_STRING = "mongodb://localhost:27017";
    private static final String DATABASE_NAME = "MapTools";
    private static final String COLLECTION_NAME = "road_network";
    private static final int THREAD_POOL_SIZE = 8;
    
    private MongoClient mongoClient;
    private List<Map<String, Object>> roads;
    private GeometryFactory geometryFactory;
    private ExecutorService executorService;
    
    public JavaRoadMatcher() {
        this.geometryFactory = new GeometryFactory();
        this.executorService = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        this.roads = new ArrayList<>();
        loadRoadsFromMongoDB();
    }
    
    /**
     * 从MongoDB加载道路数据
     */
    private void loadRoadsFromMongoDB() {
        try {
            mongoClient = new MongoClient(new MongoClientURI(MONGO_CONNECTION_STRING));
            MongoDatabase database = mongoClient.getDatabase(DATABASE_NAME);
            MongoCollection<Document> collection = database.getCollection(COLLECTION_NAME);
            
            // 查询道路数据（排除元数据文档）
            List<Document> roadDocs = collection.find(Filters.ne("type", "metadata")).into(new ArrayList<>());
            
            for (Document roadDoc : roadDocs) {
                Map<String, Object> road = new HashMap<>();
                road.put("id", roadDoc.getString("road_id"));  // 使用road_id而不是id
                road.put("name", roadDoc.getString("name"));
                road.put("type", roadDoc.getString("type"));
                
                // 解析points字段而不是geometry字段
                @SuppressWarnings("unchecked")
                List<List<Number>> points = (List<List<Number>>) roadDoc.get("points");
                if (points != null && !points.isEmpty()) {
                    Coordinate[] coords = new Coordinate[points.size()];
                    for (int i = 0; i < points.size(); i++) {
                        List<Number> point = points.get(i);
                        double x = point.get(0).doubleValue();
                        double y = point.get(1).doubleValue();
                        coords[i] = new Coordinate(x, y);
                    }
                    LineString lineString = geometryFactory.createLineString(coords);
                    road.put("geometry", lineString);
                }
                
                roads.add(road);
            }
            
            System.out.println("从MongoDB加载了 " + roads.size() + " 条道路数据");
            
        } catch (Exception e) {
            System.err.println("从MongoDB加载道路数据失败: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 找到最近的道路点 - 完全重写，避免类型转换问题
     */
    public Map<String, Object> findClosestRoad(double longitude, double latitude) {
        if (roads.isEmpty()) {
            return createDefaultMatch(longitude, latitude);
        }
        
        Point gpsPoint = geometryFactory.createPoint(new Coordinate(longitude, latitude));
        double minDistance = Double.MAX_VALUE;
        Map<String, Object> closestRoad = null;
        Coordinate closestPoint = null;
        
        for (Map<String, Object> road : roads) {
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                // 计算到整个道路线的最短距离
                double distance = gpsPoint.distance(geometry);
                if (distance < minDistance) {
                    minDistance = distance;
                    closestRoad = road;
                    // 找到最近的点
                    closestPoint = findClosestPointOnLineString(gpsPoint, geometry);
                }
            }
        }
        
        if (closestRoad != null) {
            Map<String, Object> result = new HashMap<>();
            result.put("matched_longitude", Double.valueOf(closestPoint.x));
            result.put("matched_latitude", Double.valueOf(closestPoint.y));
            result.put("road_id", closestRoad.get("id"));
            result.put("road_name", closestRoad.get("name"));
            result.put("road_type", closestRoad.get("type"));
            result.put("distance_to_road", Double.valueOf(minDistance));
            return result;
        } else {
            return createDefaultMatch(longitude, latitude);
        }
    }
    
    /**
     * 找到线段上最近的点
     */
    private Coordinate findClosestPointOnLineString(Point gpsPoint, LineString lineString) {
        Coordinate[] coords = lineString.getCoordinates();
        if (coords.length < 2) {
            return coords[0];
        }
        
        double minDistance = Double.MAX_VALUE;
        Coordinate closestPoint = coords[0];
        
        // 遍历所有线段
        for (int i = 0; i < coords.length - 1; i++) {
            Coordinate p1 = coords[i];
            Coordinate p2 = coords[i + 1];
            
            // 计算点到线段的最近点
            Coordinate closestOnSegment = findClosestPointOnSegment(
                gpsPoint.getCoordinate(), p1, p2);
            
            double distance = gpsPoint.getCoordinate().distance(closestOnSegment);
            if (distance < minDistance) {
                minDistance = distance;
                closestPoint = closestOnSegment;
            }
        }
        
        return closestPoint;
    }
    
    /**
     * 计算点到线段的最近点
     */
    private Coordinate findClosestPointOnSegment(Coordinate point, Coordinate segStart, Coordinate segEnd) {
        double dx = segEnd.x - segStart.x;
        double dy = segEnd.y - segStart.y;
        
        if (dx == 0 && dy == 0) {
            return segStart;
        }
        
        double t = ((point.x - segStart.x) * dx + (point.y - segStart.y) * dy) / (dx * dx + dy * dy);
        t = Math.max(0, Math.min(1, t));
        
        return new Coordinate(segStart.x + t * dx, segStart.y + t * dy);
    }
    
    /**
     * 创建默认匹配结果（当没有找到道路时）
     */
    private Map<String, Object> createDefaultMatch(double longitude, double latitude) {
        Map<String, Object> result = new HashMap<>();
        result.put("matched_longitude", Double.valueOf(longitude));
        result.put("matched_latitude", Double.valueOf(latitude));
        result.put("road_id", "unknown");
        result.put("road_name", "未知道路");
        result.put("road_type", "unknown");
        result.put("distance_to_road", Double.valueOf(0.0));
        return result;
    }
    
    /**
     * 批量匹配GPS点到道路（多线程版本）
     */
    public List<Map<String, Object>> matchGpsToRoads(List<Map<String, Object>> gpsPoints) {
        if (gpsPoints.isEmpty()) {
            return new ArrayList<>();
        }
        
        // 如果点数较少，使用单线程
        if (gpsPoints.size() < 100) {
            return matchGpsToRoadsSingleThread(gpsPoints);
        }
        
        // 多线程处理
        return matchGpsToRoadsMultiThread(gpsPoints);
    }
    
    /**
     * 单线程匹配GPS点到道路
     */
    private List<Map<String, Object>> matchGpsToRoadsSingleThread(List<Map<String, Object>> gpsPoints) {
        List<Map<String, Object>> matchedPoints = new ArrayList<>();
        
        for (Map<String, Object> gpsPoint : gpsPoints) {
            // 安全获取经纬度，处理类型转换
            Object lonObj = gpsPoint.get("longitude");
            Object latObj = gpsPoint.get("latitude");
            
            double longitude, latitude;
            if (lonObj instanceof Double) {
                longitude = (Double) lonObj;
            } else if (lonObj instanceof Integer) {
                longitude = ((Integer) lonObj).doubleValue();
            } else if (lonObj instanceof Number) {
                longitude = ((Number) lonObj).doubleValue();
            } else {
                longitude = 0.0;
            }
            
            if (latObj instanceof Double) {
                latitude = (Double) latObj;
            } else if (latObj instanceof Integer) {
                latitude = ((Integer) latObj).doubleValue();
            } else if (latObj instanceof Number) {
                latitude = ((Number) latObj).doubleValue();
            } else {
                latitude = 0.0;
            }
            
            Map<String, Object> matchResult = findClosestRoad(longitude, latitude);
            
            Map<String, Object> matchedPoint = new HashMap<>(gpsPoint);
            matchedPoint.put("matched_longitude", matchResult.get("matched_longitude"));
            matchedPoint.put("matched_latitude", matchResult.get("matched_latitude"));
            matchedPoint.put("road_id", matchResult.get("road_id"));
            matchedPoint.put("road_name", matchResult.get("road_name"));
            matchedPoint.put("road_type", matchResult.get("road_type"));
            matchedPoint.put("distance_to_road", matchResult.get("distance_to_road"));
            matchedPoint.put("matched", true);
            
            matchedPoints.add(matchedPoint);
        }
        
        return matchedPoints;
    }
    
    /**
     * 多线程匹配GPS点到道路
     */
    private List<Map<String, Object>> matchGpsToRoadsMultiThread(List<Map<String, Object>> gpsPoints) {
        int batchSize = Math.max(1, gpsPoints.size() / THREAD_POOL_SIZE);
        List<Future<List<Map<String, Object>>>> futures = new ArrayList<>();
        
        // 分批提交任务
        for (int i = 0; i < gpsPoints.size(); i += batchSize) {
            int endIndex = Math.min(i + batchSize, gpsPoints.size());
            List<Map<String, Object>> batch = gpsPoints.subList(i, endIndex);
            
            Future<List<Map<String, Object>>> future = executorService.submit(() -> {
                return matchGpsToRoadsSingleThread(batch);
            });
            
            futures.add(future);
        }
        
        // 收集结果
        List<Map<String, Object>> matchedPoints = new ArrayList<>();
        for (Future<List<Map<String, Object>>> future : futures) {
            try {
                matchedPoints.addAll(future.get());
            } catch (InterruptedException | ExecutionException e) {
                System.err.println("道路匹配任务执行失败: " + e.getMessage());
                e.printStackTrace();
            }
        }
        
        return matchedPoints;
    }
    
    /**
     * 关闭资源
     */
    public void close() {
        if (executorService != null) {
            executorService.shutdown();
            try {
                if (!executorService.awaitTermination(60, TimeUnit.SECONDS)) {
                    executorService.shutdownNow();
                }
            } catch (InterruptedException e) {
                executorService.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
        
        if (mongoClient != null) {
            mongoClient.close();
        }
    }
}
