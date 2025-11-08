package com.maptools.gpstools.algorithm;

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
import java.lang.ref.SoftReference;

/**
 * Java道路匹配器 - 完全重写，参照Python数据结构
 * 支持多线程处理，避免类型转换问题
 * 优化内存管理，防止内存泄漏
 */
public class JavaRoadMatcher {
    
    private static final String MONGO_CONNECTION_STRING = "mongodb://localhost:27017";
    private static final String DATABASE_NAME = "MapTools";
    private static final String COLLECTION_NAME = "道路数据";
    private static final int THREAD_POOL_SIZE = 8;
    
    private MongoClient mongoClient;
    private List<Map<String, Object>> roads;
    private GeometryFactory geometryFactory;
    private ExecutorService executorService;
    // 使用SoftReference缓存，允许JVM在内存不足时回收
    private Map<String, SoftReference<Map<String, Object>>> cache;
    private final Object cacheLock = new Object();
    
    // 限制缓存大小以避免内存溢出
    private static final int MAX_CACHE_SIZE = 50000;
    
    // 空间网格索引系统 - 极致性能优化
    private static final double GRID_SIZE = 0.001; // 约100米网格
    private Map<String, List<Map<String, Object>>> spatialGrid;
    private double minLon, maxLon, minLat, maxLat;
    
    public JavaRoadMatcher() {
        this.geometryFactory = new GeometryFactory();
        this.executorService = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        this.roads = new ArrayList<>();
        this.cache = new ConcurrentHashMap<>();
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
            
            // 查询道路数据（查询GeoJSON Feature类型的文档）
            List<Document> roadDocs = collection.find(Filters.eq("type", "Feature")).into(new ArrayList<>());
            
            for (Document roadDoc : roadDocs) {
                Map<String, Object> road = new HashMap<>();
                
                // 获取properties字段
                Document properties = roadDoc.get("properties", Document.class);
                if (properties != null) {
                    road.put("id", roadDoc.getString("id"));
                    road.put("name", properties.getString("name"));
                    road.put("type", properties.getString("highway"));
                }
                
                // 解析geometry字段（GeoJSON格式）
                Document geometry = roadDoc.get("geometry", Document.class);
                if (geometry != null) {
                    String geometryType = geometry.getString("type");
                    @SuppressWarnings("unchecked")
                    List<Object> coordinates = (List<Object>) geometry.get("coordinates");
                    
                    if ("LineString".equals(geometryType) && coordinates != null && !coordinates.isEmpty()) {
                        // 处理LineString类型
                        Coordinate[] coords = new Coordinate[coordinates.size()];
                        for (int i = 0; i < coordinates.size(); i++) {
                            @SuppressWarnings("unchecked")
                            List<Number> coord = (List<Number>) coordinates.get(i);
                            if (coord.size() >= 2) {
                                double x = coord.get(0).doubleValue(); // 经度
                                double y = coord.get(1).doubleValue(); // 纬度
                                coords[i] = new Coordinate(x, y);
                            }
                        }
                        LineString lineString = geometryFactory.createLineString(coords);
                        road.put("geometry", lineString);
                        roads.add(road);
                    } else if ("MultiLineString".equals(geometryType) && coordinates != null && !coordinates.isEmpty()) {
                        // 处理MultiLineString类型 - 将每个LineString作为单独的道路
                        for (Object lineObj : coordinates) {
                            @SuppressWarnings("unchecked")
                            List<List<Number>> line = (List<List<Number>>) lineObj;
                            if (line != null && line.size() >= 2) {
                                Coordinate[] coords = new Coordinate[line.size()];
                                for (int i = 0; i < line.size(); i++) {
                                    List<Number> coord = line.get(i);
                                    if (coord.size() >= 2) {
                                        double x = coord.get(0).doubleValue(); // 经度
                                        double y = coord.get(1).doubleValue(); // 纬度
                                        coords[i] = new Coordinate(x, y);
                                    }
                                }
                                LineString lineString = geometryFactory.createLineString(coords);
                                Map<String, Object> multiRoad = new HashMap<>(road);
                                multiRoad.put("geometry", lineString);
                                roads.add(multiRoad);
                            }
                        }
                    }
                }
            }
            
            System.out.println("从MongoDB加载了 " + roads.size() + " 条道路数据");
            
            // 构建空间网格索引
            buildSpatialIndex();
            System.out.println("空间网格索引构建完成，网格数量: " + spatialGrid.size());
            
        } catch (Exception e) {
            System.err.println("从MongoDB加载道路数据失败: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * 构建空间网格索引 - 极致性能优化
     */
    private void buildSpatialIndex() {
        spatialGrid = new HashMap<>();
        minLon = Double.MAX_VALUE;
        maxLon = Double.MIN_VALUE;
        minLat = Double.MAX_VALUE;
        maxLat = Double.MIN_VALUE;
        
        // 计算边界
        for (Map<String, Object> road : roads) {
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                for (Coordinate coord : coords) {
                    minLon = Math.min(minLon, coord.x);
                    maxLon = Math.max(maxLon, coord.x);
                    minLat = Math.min(minLat, coord.y);
                    maxLat = Math.max(maxLat, coord.y);
                }
            }
        }
        
        // 将道路分配到网格
        for (Map<String, Object> road : roads) {
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                Set<String> gridKeys = new HashSet<>();
                
                // 为道路的每个点计算网格键
                for (Coordinate coord : coords) {
                    String gridKey = getGridKey(coord.x, coord.y);
                    gridKeys.add(gridKey);
                }
                
                // 将道路添加到所有相关网格
                for (String gridKey : gridKeys) {
                    spatialGrid.computeIfAbsent(gridKey, k -> new ArrayList<>()).add(road);
                }
            }
        }
    }
    
    /**
     * 获取网格键
     */
    private String getGridKey(double lon, double lat) {
        int gridX = (int) Math.floor((lon - minLon) / GRID_SIZE);
        int gridY = (int) Math.floor((lat - minLat) / GRID_SIZE);
        return gridX + "," + gridY;
    }
    
    /**
     * 获取附近网格的道路
     */
    private List<Map<String, Object>> getNearbyRoads(double longitude, double latitude) {
        Set<Map<String, Object>> nearbyRoads = new HashSet<>();
        
        // 检查当前网格和周围8个网格
        for (int dx = -1; dx <= 1; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                int gridX = (int) Math.floor((longitude - minLon) / GRID_SIZE) + dx;
                int gridY = (int) Math.floor((latitude - minLat) / GRID_SIZE) + dy;
                String gridKey = gridX + "," + gridY;
                
                List<Map<String, Object>> gridRoads = spatialGrid.get(gridKey);
                if (gridRoads != null) {
                    nearbyRoads.addAll(gridRoads);
                }
            }
        }
        
        return new ArrayList<>(nearbyRoads);
    }
    
    /**
     * 找到最近的道路点 - 极致性能优化版本
     * 增加方向一致性检查，优先匹配同一侧道路
     * 考虑前后点尽可能在同一条路同侧
     */
    public Map<String, Object> findClosestRoad(double longitude, double latitude, double gpsHeading, 
                                              List<Map<String, Object>> trajectoryContext, int pointIndex) {
        // 创建缓存键（降低精度减少缓存键数量）
        String cacheKey = String.format("%.4f,%.4f,%.1f,%d", longitude, latitude, gpsHeading, pointIndex);
        
        // 无锁缓存检查
        SoftReference<Map<String, Object>> ref = cache.get(cacheKey);
        if (ref != null) {
            Map<String, Object> cached = ref.get();
            if (cached != null) {
                return cached;
            }
        }
        
        // 控制缓存大小，避免内存溢出
        if (cache.size() > MAX_CACHE_SIZE) {
            cache.clear();
        }
        
        if (roads.isEmpty()) {
            Map<String, Object> result = createDefaultMatch(longitude, latitude);
            cache.put(cacheKey, new SoftReference<>(result));
            return result;
        }
        
        // 使用空间索引获取附近道路 - 极致性能优化
        List<Map<String, Object>> nearbyRoads = getNearbyRoads(longitude, latitude);
        
        if (nearbyRoads.isEmpty()) {
            Map<String, Object> result = createDefaultMatch(longitude, latitude);
            cache.put(cacheKey, new SoftReference<>(result));
            return result;
        }
        
        // 使用上下文信息进行智能匹配，而非直接最短距离匹配
        Map<String, Object> result = performContextAwareMatching(
            longitude, latitude, gpsHeading, trajectoryContext, pointIndex, nearbyRoads);
        
        // 无锁缓存存储
        cache.put(cacheKey, new SoftReference<>(result));
        return result;
    }
    
    /**
     * 获取上下文中的道路ID
     */
    private String getContextRoadId(List<Map<String, Object>> trajectoryContext, int pointIndex) {
        if (trajectoryContext == null || trajectoryContext.isEmpty()) {
            return null;
        }
        
        // 优先考虑更近的点，优先级从高到低：
        // 1. 前一个点（最高优先级）
        // 2. 后一个点
        // 3. 前面的点（按距离递减）
        // 4. 后面的点（按距离递减）
        
        // 查找前一个点
        if (pointIndex > 0) {
            Map<String, Object> prevPoint = trajectoryContext.get(pointIndex - 1);
            if (prevPoint.containsKey("road_id") && !"unknown".equals(prevPoint.get("road_id"))) {
                return (String) prevPoint.get("road_id");
            }
        }
        
        // 查找后一个点
        if (pointIndex < trajectoryContext.size() - 1) {
            Map<String, Object> nextPoint = trajectoryContext.get(pointIndex + 1);
            if (nextPoint.containsKey("road_id") && !"unknown".equals(nextPoint.get("road_id"))) {
                return (String) nextPoint.get("road_id");
            }
        }
        
        // 查找前后几个点中的道路ID
        int contextWindow = 3; // 前后各3个点的窗口
        
        // 查找前面的点（按距离递增）
        for (int i = pointIndex - 2; i >= Math.max(0, pointIndex - contextWindow); i--) {
            Map<String, Object> point = trajectoryContext.get(i);
            if (point.containsKey("road_id") && !"unknown".equals(point.get("road_id"))) {
                return (String) point.get("road_id");
            }
        }
        
        // 查找后面的点（按距离递增）
        for (int i = pointIndex + 2; i <= Math.min(pointIndex + contextWindow, trajectoryContext.size() - 1); i++) {
            Map<String, Object> point = trajectoryContext.get(i);
            if (point.containsKey("road_id") && !"unknown".equals(point.get("road_id"))) {
                return (String) point.get("road_id");
            }
        }
        
        return null;
    }
    
    /**
     * 找到最近的道路点 - 重载方法，保持向后兼容
     */
    public Map<String, Object> findClosestRoad(double longitude, double latitude, double gpsHeading) {
        return findClosestRoad(longitude, latitude, gpsHeading, null, -1);
    }
    
    /**
     * 找到最近的道路点 - 重载方法，保持向后兼容
     */
    public Map<String, Object> findClosestRoad(double longitude, double latitude) {
        return findClosestRoad(longitude, latitude, -1, null, -1); // -1表示没有方向信息
    }
    
    /**
     * 计算道路方向（基于道路坐标的首尾点）
     */
    private double calculateRoadDirection(Coordinate[] coords) {
        if (coords.length < 2) {
            return 0.0;
        }
        
        // 使用首尾两个点计算方向
        Coordinate first = coords[0];
        Coordinate last = coords[coords.length - 1];
        
        double dx = last.x - first.x;
        double dy = last.y - first.y;
        
        // 计算角度（转换为度）
        double angle = Math.toDegrees(Math.atan2(dy, dx));
        
        // 转换为0-360度范围
        if (angle < 0) {
            angle += 360;
        }
        
        return angle;
    }
    
    /**
     * 快速边界框检查
     */
    private boolean isWithinBounds(double longitude, double latitude, LineString geometry, double radius) {
        Coordinate[] coords = geometry.getCoordinates();
        double minX = Double.MAX_VALUE, maxX = Double.MIN_VALUE;
        double minY = Double.MAX_VALUE, maxY = Double.MIN_VALUE;
        
        for (Coordinate coord : coords) {
            minX = Math.min(minX, coord.x);
            maxX = Math.max(maxX, coord.x);
            minY = Math.min(minY, coord.y);
            maxY = Math.max(maxY, coord.y);
        }
        
        return longitude >= minX - radius && longitude <= maxX + radius &&
               latitude >= minY - radius && latitude <= maxY + radius;
    }
    
    /**
     * 超快速距离计算 - 极致性能优化
     */
    private double ultraFastDistanceToLineString(double longitude, double latitude, Coordinate[] coords) {
        return ultraFastDistanceToLineString(longitude, latitude, coords, 1);
    }
    
    /**
     * 超快速距离计算 - 极致性能优化（支持采样步长）
     */
    private double ultraFastDistanceToLineString(double longitude, double latitude, Coordinate[] coords, int step) {
        double minDistance = Double.MAX_VALUE;
        
        // 采样策略：对于长道路只检查关键点
        step = Math.max(1, step); // 确保步长至少为1
        
        // 添加超时检查
        long startTime = System.currentTimeMillis();
        final long TIMEOUT_THRESHOLD = 500; // 500毫秒超时
        
        for (int i = 0; i < coords.length - 1; i += step) {
            // 检查是否超时
            if (System.currentTimeMillis() - startTime > TIMEOUT_THRESHOLD) {
                System.err.println("距离计算超时，返回当前最小距离");
                return minDistance;
            }
            
            int nextIndex = Math.min(i + step, coords.length - 1);
            double distance = ultraFastDistanceToSegment(longitude, latitude, 
                coords[i].x, coords[i].y, coords[nextIndex].x, coords[nextIndex].y);
            minDistance = Math.min(minDistance, distance);
            
            // 超早期退出优化（注意：这里是平方距离）
            if (minDistance < 0.00005 * 0.00005) { // 约5米的平方
                break;
            }
        }
        
        return minDistance;
    }
    
    /**
     * 快速距离计算（避免复杂几何运算）
     */
    private double fastDistanceToLineString(double longitude, double latitude, Coordinate[] coords) {
        double minDistance = Double.MAX_VALUE;
        
        for (int i = 0; i < coords.length - 1; i++) {
            double distance = fastDistanceToSegment(longitude, latitude, 
                coords[i].x, coords[i].y, coords[i + 1].x, coords[i + 1].y);
            minDistance = Math.min(minDistance, distance);
            
            // 早期退出优化
            if (minDistance < 0.0001) { // 约10米
                break;
            }
        }
        
        return minDistance;
    }
    
    /**
     * 超快速点到线段距离计算 - 极致性能优化
     */
    private double ultraFastDistanceToSegment(double px, double py, double x1, double y1, double x2, double y2) {
        double dx = x2 - x1;
        double dy = y2 - y1;
        
        // 快速零长度线段检查
        if (Math.abs(dx) < 1e-10 && Math.abs(dy) < 1e-10) {
            dx = px - x1;
            dy = py - y1;
            return dx * dx + dy * dy; // 返回平方距离，避免开方运算
        }
        
        double t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
        
        // 快速边界检查
        if (t <= 0) {
            dx = px - x1;
            dy = py - y1;
        } else if (t >= 1) {
            dx = px - x2;
            dy = py - y2;
        } else {
            dx = px - (x1 + t * dx);
            dy = py - (y1 + t * dy);
        }
        
        return dx * dx + dy * dy; // 返回平方距离，避免开方运算
    }
    
    /**
     * 快速点到线段距离计算
     */
    private double fastDistanceToSegment(double px, double py, double x1, double y1, double x2, double y2) {
        double dx = x2 - x1;
        double dy = y2 - y1;
        
        if (dx == 0 && dy == 0) {
            dx = px - x1;
            dy = py - y1;
            return Math.sqrt(dx * dx + dy * dy);
        }
        
        double t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
        t = Math.max(0, Math.min(1, t));
        
        double closestX = x1 + t * dx;
        double closestY = y1 + t * dy;
        
        dx = px - closestX;
        dy = py - closestY;
        
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    /**
     * 找到线段上最近的点 - 优化版本
     */
    private Coordinate findClosestPointOnLineString(double longitude, double latitude, Coordinate[] coords) {
        if (coords.length < 2) {
            return coords[0];
        }
        
        // 添加超时检查
        long startTime = System.currentTimeMillis();
        final long TIMEOUT_THRESHOLD = 1000; // 1秒超时
        
        double minDistance = Double.MAX_VALUE;
        Coordinate closestPoint = coords[0];
        
        // 限制处理的坐标点数量，避免在复杂道路上计算过多
        int maxSegments = Math.min(100, coords.length - 1); // 最多处理100个线段
        
        // 遍历所有线段
        for (int i = 0; i < maxSegments; i++) {
            // 检查是否超时
            if (System.currentTimeMillis() - startTime > TIMEOUT_THRESHOLD) {
                System.err.println("计算最近点超时，返回默认点");
                return closestPoint;
            }
            
            Coordinate p1 = coords[i];
            Coordinate p2 = coords[i + 1];
            
            // 计算点到线段的最近点
            Coordinate closestOnSegment = findClosestPointOnSegment(longitude, latitude, p1, p2);
            
            double dx = longitude - closestOnSegment.x;
            double dy = latitude - closestOnSegment.y;
            double distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < minDistance) {
                minDistance = distance;
                closestPoint = closestOnSegment;
            }
        }
        
        return closestPoint;
    }
    
    /**
     * 计算点到线段的最近点 - 优化版本
     */
    private Coordinate findClosestPointOnSegment(double px, double py, Coordinate segStart, Coordinate segEnd) {
        double dx = segEnd.x - segStart.x;
        double dy = segEnd.y - segStart.y;
        
        if (dx == 0 && dy == 0) {
            return segStart;
        }
        
        double t = ((px - segStart.x) * dx + (py - segStart.y) * dy) / (dx * dx + dy * dy);
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
     * 批量匹配GPS点到道路（多线程版本）并进行轨迹清理
     */
    public List<Map<String, Object>> matchGpsToRoads(List<Map<String, Object>> gpsPoints) {
        if (gpsPoints.isEmpty()) {
            return new ArrayList<>();
        }
        
        // 先进行道路匹配
        List<Map<String, Object>> matchedPoints;
        if (gpsPoints.size() < 100) {
            matchedPoints = matchGpsToRoadsSingleThread(gpsPoints);
        } else {
            matchedPoints = matchGpsToRoadsMultiThread(gpsPoints);
        }
        
        // 进行轨迹清理，过滤不符合要求的匹配点
        return cleanTrajectory(matchedPoints);
    }
    
    /**
     * 单线程匹配GPS点到道路
     */
    private List<Map<String, Object>> matchGpsToRoadsSingleThread(List<Map<String, Object>> gpsPoints) {
        List<Map<String, Object>> matchedPoints = new ArrayList<>();
        
        for (int i = 0; i < gpsPoints.size(); i++) {
            Map<String, Object> gpsPoint = gpsPoints.get(i);
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
            
            // 检查是否与前一个点重复，如果重复则跳过
            if (i > 0) {
                Map<String, Object> prevPoint = gpsPoints.get(i - 1);
                double prevLon = getDoubleValue(prevPoint, "longitude");
                double prevLat = getDoubleValue(prevPoint, "latitude");
                
                // 如果经纬度完全相同（精度到约1米），则跳过当前点
                if (Math.abs(longitude - prevLon) < 1e-5 && Math.abs(latitude - prevLat) < 1e-5) {
                    continue;
                }
            }
            
            // 获取GPS方向信息
            double gpsHeading = -1; // 默认无方向信息
            Object headingObj = gpsPoint.get("heading");
            if (headingObj instanceof Double) {
                gpsHeading = (Double) headingObj;
            } else if (headingObj instanceof Integer) {
                gpsHeading = ((Integer) headingObj).doubleValue();
            } else if (headingObj instanceof Number) {
                gpsHeading = ((Number) headingObj).doubleValue();
            }
            
            // 如果速度为0，则不参考方向信息
            Object speedObj = gpsPoint.get("speed");
            if (speedObj instanceof Number && ((Number) speedObj).doubleValue() == 0) {
                gpsHeading = -1; // 速度为0时不参考方向
            }
            
            // 考虑前后点的道路上下文进行匹配
            Map<String, Object> matchResult = findClosestRoad(longitude, latitude, gpsHeading, gpsPoints, i);
            
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
        // 限制最大批处理大小以控制内存使用
        batchSize = Math.min(batchSize, 1000);
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
                // 显式置空future以帮助GC
                future = null;
            } catch (InterruptedException | ExecutionException e) {
                System.err.println("道路匹配任务执行失败: " + e.getMessage());
                e.printStackTrace();
            }
        }
        
        // 清理futures列表以释放内存
        futures.clear();
        
        return matchedPoints;
    }
    
    /**
     * 轨迹清理方法 - 过滤不符合要求的匹配点
     * 1. 离所匹配的道路过远的点
     * 2. 相邻时序较近时间范围内，离别的匹配点过远的点
     * 3. 前后好多点都在一条路上，该点漂移到别的路上面的点
     */
    private List<Map<String, Object>> cleanTrajectory(List<Map<String, Object>> matchedPoints) {
        if (matchedPoints.size() <= 2) {
            return matchedPoints; // 点太少，不进行过滤
        }
        
        List<Map<String, Object>> cleanedPoints = new ArrayList<>();
        
        // 配置参数
        final double MAX_ROAD_DISTANCE = 100.0; // 最大道路距离（米）
        final double MAX_POINT_DISTANCE = 500.0; // 相邻点最大距离（米）
        final long TIME_WINDOW = 300; // 时间窗口（秒）
        final int ROAD_CONSISTENCY_WINDOW = 5; // 道路一致性检查窗口
        
        for (int i = 0; i < matchedPoints.size(); i++) {
            Map<String, Object> currentPoint = matchedPoints.get(i);
            boolean shouldKeep = true;
            
            // 规则1: 检查离匹配道路的距离
            if (shouldKeep) {
                shouldKeep = checkRoadDistance(currentPoint, MAX_ROAD_DISTANCE);
            }
            
            // 规则2: 检查与相邻时序点的距离
            if (shouldKeep && i > 0 && i < matchedPoints.size() - 1) {
                shouldKeep = checkTemporalDistance(matchedPoints, i, MAX_POINT_DISTANCE, TIME_WINDOW);
            }
            
            // 规则3: 检查道路一致性
            if (shouldKeep && matchedPoints.size() >= ROAD_CONSISTENCY_WINDOW) {
                shouldKeep = checkRoadConsistency(matchedPoints, i, ROAD_CONSISTENCY_WINDOW);
            }
            
            if (shouldKeep) {
                cleanedPoints.add(currentPoint);
            } else {
                System.out.println("过滤掉匹配点: 索引=" + i + ", 原因=不符合轨迹清理规则");
            }
        }
        
        System.out.println("轨迹清理完成: 原始点数=" + matchedPoints.size() + ", 清理后点数=" + cleanedPoints.size());
        return cleanedPoints;
    }
    
    /**
     * 检查点到匹配道路的距离是否合理
     */
    private boolean checkRoadDistance(Map<String, Object> point, double maxDistance) {
        Object distanceObj = point.get("distance_to_road");
        if (distanceObj instanceof Double) {
            double distance = (Double) distanceObj;
            // 转换为米（假设distance_to_road是度数，需要转换）
            double distanceInMeters = distance * 111000; // 粗略转换：1度约等于111km
            return distanceInMeters <= maxDistance;
        }
        return true; // 如果没有距离信息，保留该点
    }
    
    /**
     * 检查与相邻时序点的距离
     */
    private boolean checkTemporalDistance(List<Map<String, Object>> points, int currentIndex, 
                                        double maxDistance, long timeWindow) {
        Map<String, Object> currentPoint = points.get(currentIndex);
        
        // 获取当前点的时间和位置
        long currentTime = getPointTimestamp(currentPoint);
        double currentLon = getDoubleValue(currentPoint, "matched_longitude");
        double currentLat = getDoubleValue(currentPoint, "matched_latitude");
        
        // 检查时间窗口内的相邻点
        for (int i = Math.max(0, currentIndex - 3); i <= Math.min(points.size() - 1, currentIndex + 3); i++) {
            if (i == currentIndex) continue;
            
            Map<String, Object> neighborPoint = points.get(i);
            long neighborTime = getPointTimestamp(neighborPoint);
            
            // 检查是否在时间窗口内
            if (Math.abs(currentTime - neighborTime) <= timeWindow) {
                double neighborLon = getDoubleValue(neighborPoint, "matched_longitude");
                double neighborLat = getDoubleValue(neighborPoint, "matched_latitude");
                
                // 计算距离
                double distance = calculateDistance(currentLat, currentLon, neighborLat, neighborLon);
                if (distance > maxDistance) {
                    return false; // 距离过远，应该过滤
                }
            }
        }
        
        return true;
    }
    
    /**
     * 检查道路一致性
     */
    private boolean checkRoadConsistency(List<Map<String, Object>> points, int currentIndex, int windowSize) {
        if (currentIndex < windowSize / 2 || currentIndex >= points.size() - windowSize / 2) {
            return true; // 边界点不进行一致性检查
        }
        
        Map<String, Object> currentPoint = points.get(currentIndex);
        String currentRoadId = (String) currentPoint.get("road_id");
        
        if (currentRoadId == null) {
            return true; // 没有道路信息，保留
        }
        
        // 统计窗口内的道路分布
        Map<String, Integer> roadCounts = new HashMap<>();
        int start = currentIndex - windowSize / 2;
        int end = currentIndex + windowSize / 2;
        
        for (int i = start; i <= end; i++) {
            if (i == currentIndex) continue;
            
            String roadId = (String) points.get(i).get("road_id");
            if (roadId != null) {
                roadCounts.put(roadId, roadCounts.getOrDefault(roadId, 0) + 1);
            }
        }
        
        // 找到最常见的道路
        String mostCommonRoad = null;
        int maxCount = 0;
        for (Map.Entry<String, Integer> entry : roadCounts.entrySet()) {
            if (entry.getValue() > maxCount) {
                maxCount = entry.getValue();
                mostCommonRoad = entry.getKey();
            }
        }
        
        // 如果当前点的道路与最常见道路不同，且最常见道路占比超过70%，则过滤当前点
        if (mostCommonRoad != null && !currentRoadId.equals(mostCommonRoad)) {
            double ratio = (double) maxCount / (windowSize - 1);
            return ratio < 0.7; // 如果一致性比例超过70%，则过滤异常点
        }
        
        return true;
    }
    
    /**
     * 获取点的时间戳
     */
    private long getPointTimestamp(Map<String, Object> point) {
        // 直接从点中获取datetime，因为matchedPoint已经包含了原始GPS信息
        Object datetimeObj = point.get("datetime");
        if (datetimeObj instanceof String) {
            try {
                // 简单的时间解析，假设格式为 "2023-10-01T08:00:00"
                String datetime = (String) datetimeObj;
                // 提取小时和分钟作为简单的时间戳
                if (datetime.contains("T") && datetime.length() >= 16) {
                    String timePart = datetime.substring(datetime.indexOf("T") + 1, datetime.indexOf("T") + 6);
                    String[] parts = timePart.split(":");
                    if (parts.length >= 2) {
                        int hours = Integer.parseInt(parts[0]);
                        int minutes = Integer.parseInt(parts[1]);
                        return hours * 3600 + minutes * 60; // 转换为秒
                    }
                }
                return 0;
            } catch (Exception e) {
                return 0;
            }
        }
        return 0;
    }
    
    /**
     * 安全获取Double值
     */
    private double getDoubleValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value instanceof Double) {
            return (Double) value;
        } else if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return 0.0;
    }
    
    /**
     * 计算两点间距离（米）
     */
    private double calculateDistance(double lat1, double lon1, double lat2, double lon2) {
        final double R = 6371000; // 地球半径（米）
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
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
        
        // 清理缓存
        synchronized (cacheLock) {
            cache.clear();
        }
        
        if (mongoClient != null) {
            mongoClient.close();
        }
        
        // 清理道路数据以帮助GC
        if (roads != null) {
            roads.clear();
        }
    }
    
    /**
     * 基于上下文的道路匹配方法
     * 综合考虑上下文信息、方向一致性和距离因素
     */
    private Map<String, Object> performContextAwareMatching(double longitude, double latitude, 
                                                           double gpsHeading,
                                                           List<Map<String, Object>> trajectoryContext, 
                                                           int pointIndex,
                                                           List<Map<String, Object>> nearbyRoads) {
        // 添加超时检查，避免在复杂计算中卡住
        long startTime = System.currentTimeMillis();
        final long TIMEOUT_THRESHOLD = 5000; // 5秒超时
        
        // 初始化评分Map
        Map<Map<String, Object>, Double> roadScores = new HashMap<>();
        
        // 获取上下文中的道路ID
        String contextRoadId = getContextRoadId(trajectoryContext, pointIndex);
        
        // 限制参与评分的道路数量，避免在复杂区域计算过多
        int maxRoadsToConsider = Math.min(50, nearbyRoads.size());
        final List<Map<String, Object>> roadsToConsider;
        if (nearbyRoads.size() > maxRoadsToConsider) {
            // 只考虑距离最近的前50条道路
            roadsToConsider = new ArrayList<>();
            Map<Map<String, Object>, Double> distanceMap = new HashMap<>();
            
            for (Map<String, Object> road : nearbyRoads) {
                LineString geometry = (LineString) road.get("geometry");
                Coordinate[] coords = geometry.getCoordinates();
                double distance = ultraFastDistanceToLineString(longitude, latitude, coords);
                distanceMap.put(road, distance);
            }
            
            // 按距离排序并取前50个
            distanceMap.entrySet().stream()
                .sorted(Map.Entry.comparingByValue())
                .limit(maxRoadsToConsider)
                .map(Map.Entry::getKey)
                .forEach(roadsToConsider::add);
        } else {
            roadsToConsider = nearbyRoads;
        }
        
        // 为每条附近道路计算综合评分
        int roadIndex = 0;
        for (Map<String, Object> road : roadsToConsider) {
            // 检查是否超时
            if (System.currentTimeMillis() - startTime > TIMEOUT_THRESHOLD) {
                System.err.println("道路匹配超时，使用默认匹配: lon=" + longitude + ", lat=" + latitude);
                return createDefaultMatch(longitude, latitude);
            }
            
            // 基础距离评分（距离越近得分越高）
            LineString geometry = (LineString) road.get("geometry");
            Coordinate[] coords = geometry.getCoordinates();
            double distance = ultraFastDistanceToLineString(longitude, latitude, coords);
            
            // 如果距离太远，跳过这条道路
            if (distance > 0.01) { // 约1公里的平方
                continue;
            }
            
            double distanceScore = 1.0 / (1.0 + Math.sqrt(distance) * 1000); // 距离评分，归一化到0-1之间
            
            // 上下文评分（如果与上下文道路相同则加分）
            double contextScore = 0.0;
            if (contextRoadId != null && contextRoadId.equals(road.get("id"))) {
                contextScore = 1.0; // 与上下文道路相同，给予最高分
            }
            
            // 方向一致性评分
            double directionScore = 0.0;
            if (gpsHeading >= 0) {
                double roadDirection = calculateRoadDirection(coords);
                double directionDiff = Math.abs(gpsHeading - roadDirection);
                if (directionDiff > 180) {
                    directionDiff = 360 - directionDiff;
                }
                directionScore = 1.0 - (directionDiff / 180.0); // 方向差异越小得分越高
            }
            
            // 综合评分（可以根据需要调整权重）
            double contextWeight = 0.5;   // 上下文权重
            double directionWeight = 0.3; // 方向权重
            double distanceWeight = 0.2;  // 距离权重
            
            // 如果没有上下文信息，调整权重
            if (contextRoadId == null) {
                contextWeight = 0.0;
                directionWeight = 0.4;
                distanceWeight = 0.6;
            }
            
            // 如果没有方向信息，调整权重
            if (gpsHeading < 0) {
                contextWeight = 0.6;
                directionWeight = 0.0;
                distanceWeight = 0.4;
            }
            
            double totalScore = contextWeight * contextScore + 
                               directionWeight * directionScore + 
                               distanceWeight * distanceScore;
            
            roadScores.put(road, totalScore);
            
            // 限制评分道路数量，避免内存占用过多
            roadIndex++;
            if (roadIndex > 100) {
                break;
            }
        }
        
        // 找到评分最高的道路
        Map<String, Object> bestRoad = null;
        double maxScore = -1.0;
        
        for (Map.Entry<Map<String, Object>, Double> entry : roadScores.entrySet()) {
            if (entry.getValue() > maxScore) {
                maxScore = entry.getValue();
                bestRoad = entry.getKey();
            }
        }
        
        // 在最佳道路上进行精细匹配
        if (bestRoad != null) {
            return performPreciseMatchingOnRoad(longitude, latitude, gpsHeading, bestRoad);
        } else {
            return createDefaultMatch(longitude, latitude);
        }
    }
    
    /**
     * 在指定道路上进行精细匹配
     */
    private Map<String, Object> performPreciseMatchingOnRoad(double longitude, double latitude, 
                                                            double gpsHeading, Map<String, Object> road) {
        LineString geometry = (LineString) road.get("geometry");
        Coordinate[] coords = geometry.getCoordinates();
        
        // 找到最近点
        Coordinate closestPoint = findClosestPointOnLineString(longitude, latitude, coords);
        
        // 计算距离
        double dx = longitude - closestPoint.x;
        double dy = latitude - closestPoint.y;
        double distance = Math.sqrt(dx * dx + dy * dy) * 111000; // 转换为米
        
        Map<String, Object> result = new HashMap<>();
        result.put("matched_longitude", Double.valueOf(closestPoint.x));
        result.put("matched_latitude", Double.valueOf(closestPoint.y));
        result.put("road_id", road.get("id"));
        result.put("road_name", road.get("name"));
        result.put("road_type", road.get("type"));
        result.put("distance_to_road", Double.valueOf(distance));
        return result;
    }
    
    /**
     * 查找方向一致的道路
     */
    private Map<String, Object> findDirectionConsistentRoad(double longitude, double latitude, 
                                                           double gpsHeading, 
                                                           List<Map<String, Object>> nearbyRoads) {
        double minDirectionDiff = Double.MAX_VALUE;
        Map<String, Object> bestRoad = null;
        
        for (Map<String, Object> road : nearbyRoads) {
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                
                // 计算道路方向
                double roadDirection = calculateRoadDirection(coords);
                
                // 计算方向差异
                double directionDiff = Math.abs(gpsHeading - roadDirection);
                // 考虑方向循环特性（0度和360度是相同的）
                if (directionDiff > 180) {
                    directionDiff = 360 - directionDiff;
                }
                
                if (directionDiff < minDirectionDiff) {
                    minDirectionDiff = directionDiff;
                    bestRoad = road;
                }
            }
        }
        
        // 如果方向差异小于阈值（例如30度），则认为方向一致
        if (minDirectionDiff < 30) {
            return bestRoad;
        }
        
        return null;
    }
    
    /**
     * 最短距离匹配（作为最后的选择）
     */
    private Map<String, Object> performClosestMatching(double longitude, double latitude, 
                                                      double gpsHeading,
                                                      List<Map<String, Object>> nearbyRoads) {
        double minDistance = Double.MAX_VALUE;
        Map<String, Object> closestRoad = null;
        Coordinate closestPoint = null;
        
        for (Map<String, Object> road : nearbyRoads) {
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                double distance = ultraFastDistanceToLineString(longitude, latitude, coords);
                
                if (distance < minDistance) {
                    minDistance = distance;
                    closestRoad = road;
                    closestPoint = null; // 延迟计算精确投影点
                }
            }
        }
        
        if (closestRoad != null) {
            // 只有找到最近道路后才计算精确投影点
            if (closestPoint == null) {
                LineString geometry = (LineString) closestRoad.get("geometry");
                closestPoint = findClosestPointOnLineString(longitude, latitude, geometry.getCoordinates());
            }
            
            Map<String, Object> result = new HashMap<>();
            result.put("matched_longitude", Double.valueOf(closestPoint.x));
            result.put("matched_latitude", Double.valueOf(closestPoint.y));
            result.put("road_id", closestRoad.get("id"));
            result.put("road_name", closestRoad.get("name"));
            result.put("road_type", closestRoad.get("type"));
            result.put("distance_to_road", Double.valueOf(Math.sqrt(minDistance) * 111000)); // 开方后转换为米
            return result;
        } else {
            return createDefaultMatch(longitude, latitude);
        }
    }
}