package com.maptools.gpstools;

import org.locationtech.jts.geom.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.FindIterable;
import org.bson.Document;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 路径规划算法类
 * 使用A*算法在道路网络中寻找最短路径
 */
public class PathPlanner {
    
    private static final double DISTANCE_THRESHOLD = 500.0; // 500米阈值
    private static final double EARTH_RADIUS = 6371000.0; // 地球半径（米）
    
    // 道路网络图
    private Map<String, RoadNode> roadGraph;
    private Map<String, List<RoadNode>> spatialIndex;
    private MongoDatabase database;
    private final Object spatialIndexLock = new Object();
    
    // 道路数据缓存
    private Map<String, List<Map<String, Object>>> roadCache = new ConcurrentHashMap<>();
    private static final int CACHE_SIZE_LIMIT = 1000; // 缓存大小限制
    
    public PathPlanner() {
        this.roadGraph = new ConcurrentHashMap<>();
        this.spatialIndex = new ConcurrentHashMap<>();
    }
    
    public PathPlanner(MongoDatabase database) {
        this.roadGraph = new ConcurrentHashMap<>();
        this.spatialIndex = new ConcurrentHashMap<>();
        this.database = database;
    }
    
    /**
     * 道路节点类
     */
    public static class RoadNode {
        public String id;
        public double longitude;
        public double latitude;
        public String roadId;
        public String roadName;
        public String roadType;
        public List<RoadNode> neighbors;
        public double gCost; // 从起点到当前节点的实际距离
        public double hCost; // 从当前节点到终点的启发式距离
        public double fCost; // f = g + h
        public RoadNode parent;
        
        public RoadNode(String id, double longitude, double latitude, String roadId, String roadName, String roadType) {
            this.id = id;
            this.longitude = longitude;
            this.latitude = latitude;
            this.roadId = roadId;
            this.roadName = roadName;
            this.roadType = roadType;
            this.neighbors = new ArrayList<>();
            this.gCost = 0;
            this.hCost = 0;
            this.fCost = 0;
            this.parent = null;
        }
        
        public void calculateFCost() {
            this.fCost = this.gCost + this.hCost;
        }
        
        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null || getClass() != obj.getClass()) return false;
            RoadNode that = (RoadNode) obj;
            return Objects.equals(id, that.id);
        }
        
        @Override
        public int hashCode() {
            return Objects.hash(id);
        }
    }
    
    /**
     * 构建道路网络图
     */
    public void buildRoadGraph(List<Map<String, Object>> roads) {
        // 静默构建道路网络图
        
        // 清空现有数据
        roadGraph.clear();
        spatialIndex.clear();
        
        // 创建节点
        for (Map<String, Object> road : roads) {
            String roadId = (String) road.get("id");
            String roadName = (String) road.get("name");
            String roadType = (String) road.get("type");
            
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                
                // 为每个坐标点创建节点
                for (int i = 0; i < coords.length; i++) {
                    String nodeId = roadId + "_" + i;
                    RoadNode node = new RoadNode(nodeId, coords[i].x, coords[i].y, roadId, roadName, roadType);
                    roadGraph.put(nodeId, node);
                    
                    // 添加到空间索引（线程安全）
                    String gridKey = getGridKey(coords[i].x, coords[i].y);
                    synchronized(spatialIndexLock) {
                        spatialIndex.computeIfAbsent(gridKey, k -> new ArrayList<>()).add(node);
                    }
                }
            }
        }
        
        // 构建邻接关系
        buildNeighborConnections(roads);
        
        // 静默完成
    }
    
    /**
     * 构建邻接关系
     */
    private void buildNeighborConnections(List<Map<String, Object>> roads) {
        for (Map<String, Object> road : roads) {
            String roadId = (String) road.get("id");
            LineString geometry = (LineString) road.get("geometry");
            
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                
                // 连接同一条道路上的相邻节点
                for (int i = 0; i < coords.length - 1; i++) {
                    String nodeId1 = roadId + "_" + i;
                    String nodeId2 = roadId + "_" + (i + 1);
                    
                    RoadNode node1 = roadGraph.get(nodeId1);
                    RoadNode node2 = roadGraph.get(nodeId2);
                    
                    if (node1 != null && node2 != null) {
                        double distance = calculateDistance(node1.longitude, node1.latitude, 
                                                         node2.longitude, node2.latitude);
                        
                        // 只连接距离合理的节点（避免异常数据）
                        if (distance < 1000) { // 1公里内
                            synchronized(node1.neighbors) {
                                node1.neighbors.add(node2);
                            }
                            synchronized(node2.neighbors) {
                                node2.neighbors.add(node1);
                            }
                        }
                    }
                }
            }
        }
        
        // 连接不同道路间的交叉点
        connectIntersections();
    }
    
    /**
     * 连接不同道路间的交叉点
     */
    private void connectIntersections() {
        // 静默连接道路交叉点
        
        synchronized(spatialIndexLock) {
            for (String gridKey : spatialIndex.keySet()) {
                List<RoadNode> nodesInGrid = spatialIndex.get(gridKey);
                
                if (nodesInGrid == null || nodesInGrid.isEmpty()) {
                    continue;
                }
                
                // 在同一个网格内的节点可能是交叉点
                for (int i = 0; i < nodesInGrid.size(); i++) {
                    for (int j = i + 1; j < nodesInGrid.size(); j++) {
                        RoadNode node1 = nodesInGrid.get(i);
                        RoadNode node2 = nodesInGrid.get(j);
                        
                        if (node1 == null || node2 == null) {
                            continue;
                        }
                        
                        // 如果是不同道路的节点且距离很近
                        if (!node1.roadId.equals(node2.roadId)) {
                            double distance = calculateDistance(node1.longitude, node1.latitude,
                                                             node2.longitude, node2.latitude);
                            
                            if (distance < 50) { // 50米内认为是交叉点
                                synchronized(node1.neighbors) {
                                    node1.neighbors.add(node2);
                                }
                                synchronized(node2.neighbors) {
                                    node2.neighbors.add(node1);
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // 静默完成
    }
    
    /**
     * 使用A*算法规划路径（按需加载道路数据）
     */
    public List<RoadNode> planPath(double startLon, double startLat, double endLon, double endLat) {
        // 计算搜索范围（起点终点周围2公里）
        double searchRadius = 2000.0; // 2公里
        
        // 按需加载相关道路数据
        List<Map<String, Object>> relevantRoads = loadRoadsInRange(startLon, startLat, endLon, endLat, searchRadius);
        
        if (relevantRoads.isEmpty()) {
            return new ArrayList<>();
        }
        
        // 构建局部道路网络图
        buildLocalRoadGraph(relevantRoads);
        
        // 找到最近的起点和终点节点
        RoadNode startNode = findNearestNode(startLon, startLat);
        RoadNode endNode = findNearestNode(endLon, endLat);
        
        if (startNode == null || endNode == null) {
            return new ArrayList<>();
        }
        
        if (startNode.equals(endNode)) {
            return Arrays.asList(startNode);
        }
        
        return aStarSearch(startNode, endNode);
    }
    
    /**
     * 按需加载指定范围内的道路数据（带缓存优化）
     */
    private List<Map<String, Object>> loadRoadsInRange(double startLon, double startLat, 
                                                       double endLon, double endLat, 
                                                       double searchRadius) {
        // 生成缓存键
        String cacheKey = String.format("%.6f,%.6f,%.6f,%.6f", 
            Math.min(startLon, endLon), Math.min(startLat, endLat),
            Math.max(startLon, endLon), Math.max(startLat, endLat));
        
        // 检查缓存
        if (roadCache.containsKey(cacheKey)) {
            return roadCache.get(cacheKey);
        }
        
        List<Map<String, Object>> relevantRoads = new ArrayList<>();
        
        try {
            // 计算搜索边界
            double minLon = Math.min(startLon, endLon) - searchRadius / 111000.0; // 转换为度
            double maxLon = Math.max(startLon, endLon) + searchRadius / 111000.0;
            double minLat = Math.min(startLat, endLat) - searchRadius / 111000.0;
            double maxLat = Math.max(startLat, endLat) + searchRadius / 111000.0;
            
            // 从MongoDB查询范围内的道路（优化查询）
            MongoCollection<Document> roadCollection = database.getCollection("道路数据");
            
            // 使用更高效的边界框查询
            Document query = new Document("geometry.coordinates.0.0", new Document("$gte", minLon))
                .append("geometry.coordinates.0.0", new Document("$lte", maxLon))
                .append("geometry.coordinates.0.1", new Document("$gte", minLat))
                .append("geometry.coordinates.0.1", new Document("$lte", maxLat));
            
            // 只选择需要的字段
            Document projection = new Document("id", 1)
                .append("name", 1)
                .append("type", 1)
                .append("geometry", 1);
            
            FindIterable<Document> roadDocs = roadCollection.find(query).projection(projection);
            
            for (Document doc : roadDocs) {
                Map<String, Object> road = new HashMap<>();
                road.put("id", doc.getString("id"));
                road.put("name", doc.getString("name"));
                road.put("type", doc.getString("type"));
                
                // 解析GeoJSON几何
                Document geometryDoc = doc.get("geometry", Document.class);
                if (geometryDoc != null) {
                    String type = geometryDoc.getString("type");
                    @SuppressWarnings("unchecked")
                    List<Object> coordinates = geometryDoc.getList("coordinates", Object.class);
                    
                    if ("LineString".equals(type) && coordinates != null) {
                        Coordinate[] coords = new Coordinate[coordinates.size()];
                        for (int i = 0; i < coordinates.size(); i++) {
                            @SuppressWarnings("unchecked")
                            List<Double> coord = (List<Double>) coordinates.get(i);
                            coords[i] = new Coordinate(coord.get(0), coord.get(1));
                        }
                        road.put("geometry", new GeometryFactory().createLineString(coords));
                    } else if ("MultiLineString".equals(type) && coordinates != null) {
                        // 对于MultiLineString，取第一条线段
                        if (!coordinates.isEmpty()) {
                            @SuppressWarnings("unchecked")
                            List<List<Double>> firstLine = (List<List<Double>>) coordinates.get(0);
                            Coordinate[] coords = new Coordinate[firstLine.size()];
                            for (int i = 0; i < firstLine.size(); i++) {
                                List<Double> coord = firstLine.get(i);
                                coords[i] = new Coordinate(coord.get(0), coord.get(1));
                            }
                            road.put("geometry", new GeometryFactory().createLineString(coords));
                        }
                    }
                }
                
                if (road.get("geometry") != null) {
                    relevantRoads.add(road);
                }
            }
            
            // 静默加载道路数据
            
            // 存储到缓存（限制缓存大小）
            if (roadCache.size() < CACHE_SIZE_LIMIT) {
                roadCache.put(cacheKey, relevantRoads);
            }
            
        } catch (Exception e) {
            System.err.println("按需加载道路数据失败: " + e.getMessage());
        }
        
        return relevantRoads;
    }
    
    /**
     * 构建局部道路网络图
     */
    private void buildLocalRoadGraph(List<Map<String, Object>> roads) {
        // 清空现有数据
        roadGraph.clear();
        spatialIndex.clear();
        
        // 创建节点
        for (Map<String, Object> road : roads) {
            String roadId = (String) road.get("id");
            String roadName = (String) road.get("name");
            String roadType = (String) road.get("type");
            
            LineString geometry = (LineString) road.get("geometry");
            if (geometry != null) {
                Coordinate[] coords = geometry.getCoordinates();
                
                // 为每个坐标点创建节点
                for (int i = 0; i < coords.length; i++) {
                    String nodeId = roadId + "_" + i;
                    RoadNode node = new RoadNode(nodeId, coords[i].x, coords[i].y, roadId, roadName, roadType);
                    roadGraph.put(nodeId, node);
                    
                    // 添加到空间索引（线程安全）
                    String gridKey = getGridKey(coords[i].x, coords[i].y);
                    synchronized(spatialIndexLock) {
                        spatialIndex.computeIfAbsent(gridKey, k -> new ArrayList<>()).add(node);
                    }
                }
            }
        }
        
        // 构建邻接关系
        buildNeighborConnections(roads);
    }
    private List<RoadNode> aStarSearch(RoadNode start, RoadNode goal) {
        PriorityQueue<RoadNode> openSet = new PriorityQueue<>(Comparator.comparingDouble(n -> n.fCost));
        Set<RoadNode> closedSet = new HashSet<>();
        
        // 初始化起点
        start.gCost = 0;
        start.hCost = calculateDistance(start.longitude, start.latitude, goal.longitude, goal.latitude);
        start.calculateFCost();
        start.parent = null;
        
        openSet.add(start);
        
        while (!openSet.isEmpty()) {
            RoadNode current = openSet.poll();
            
            if (current.equals(goal)) {
                return reconstructPath(current);
            }
            
            closedSet.add(current);
            
            for (RoadNode neighbor : new ArrayList<>(current.neighbors)) {
                if (closedSet.contains(neighbor)) {
                    continue;
                }
                
                double tentativeGCost = current.gCost + calculateDistance(
                    current.longitude, current.latitude,
                    neighbor.longitude, neighbor.latitude
                );
                
                if (!openSet.contains(neighbor)) {
                    neighbor.gCost = tentativeGCost;
                    neighbor.hCost = calculateDistance(neighbor.longitude, neighbor.latitude, 
                                                    goal.longitude, goal.latitude);
                    neighbor.calculateFCost();
                    neighbor.parent = current;
                    openSet.add(neighbor);
                } else if (tentativeGCost < neighbor.gCost) {
                    neighbor.gCost = tentativeGCost;
                    neighbor.hCost = calculateDistance(neighbor.longitude, neighbor.latitude, 
                                                    goal.longitude, goal.latitude);
                    neighbor.calculateFCost();
                    neighbor.parent = current;
                }
            }
        }
        
        return new ArrayList<>();
    }
    
    /**
     * 清理内存
     */
    public void clearMemory() {
        roadGraph.clear();
        spatialIndex.clear();
        roadCache.clear(); // 清理道路数据缓存
        System.gc();
    }
    
    /**
     * 重构路径
     */
    private List<RoadNode> reconstructPath(RoadNode goal) {
        List<RoadNode> path = new ArrayList<>();
        RoadNode current = goal;
        
        while (current != null) {
            path.add(current);
            current = current.parent;
        }
        
        Collections.reverse(path);
        return path;
    }
    
    /**
     * 找到最近的节点
     */
    private RoadNode findNearestNode(double longitude, double latitude) {
        RoadNode nearest = null;
        double minDistance = Double.MAX_VALUE;
        
        // 在附近网格中搜索
        for (int dx = -1; dx <= 1; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                String gridKey = getGridKey(longitude + dx * 0.001, latitude + dy * 0.001);
                List<RoadNode> nodes = spatialIndex.get(gridKey);
                
                if (nodes != null) {
                    for (RoadNode node : nodes) {
                        double distance = calculateDistance(longitude, latitude, 
                                                           node.longitude, node.latitude);
                        if (distance < minDistance) {
                            minDistance = distance;
                            nearest = node;
                        }
                    }
                }
            }
        }
        
        return nearest;
    }
    
    /**
     * 生成网格键
     */
    private String getGridKey(double longitude, double latitude) {
        int gridX = (int) Math.floor(longitude * 1000);
        int gridY = (int) Math.floor(latitude * 1000);
        return gridX + "," + gridY;
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
     * 将路径节点转换为轨迹点（带时间插值）
     */
    public List<Map<String, Object>> convertPathToTrajectoryPoints(List<RoadNode> path, 
                                                                 Map<String, Object> originalPoint) {
        List<Map<String, Object>> trajectoryPoints = new ArrayList<>();
        
        if (path.isEmpty()) {
            return trajectoryPoints;
        }
        
        // 获取起始和结束时间
        String startTime = (String) originalPoint.get("datetime");
        String endTime = startTime; // 默认使用相同时间
        
        // 尝试解析时间并计算插值
        long startTimestamp = 0;
        long endTimestamp = 0;
        boolean hasValidTime = false;
        
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            if (startTime != null && !startTime.isEmpty()) {
                startTimestamp = sdf.parse(startTime).getTime();
                endTimestamp = startTimestamp + 60000; // 默认1分钟间隔
                hasValidTime = true;
            }
        } catch (Exception e) {
            // 时间解析失败，使用默认值
        }
        
        for (int i = 0; i < path.size(); i++) {
            RoadNode node = path.get(i);
            Map<String, Object> point = new HashMap<>();
            point.put("longitude", node.longitude);
            point.put("latitude", node.latitude);
            point.put("plate_number", originalPoint.get("plate_number"));
            
            // 时间插值
            if (hasValidTime && path.size() > 1) {
                long interpolatedTime = startTimestamp + (endTimestamp - startTimestamp) * i / (path.size() - 1);
                point.put("datetime", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date(interpolatedTime)));
            } else {
                point.put("datetime", startTime);
            }
            
            point.put("speed", originalPoint.get("speed"));
            point.put("heading", originalPoint.get("heading"));
            point.put("is_valid", true);
            point.put("road_id", node.roadId);
            point.put("road_name", node.roadName);
            point.put("road_type", node.roadType);
            point.put("corrected", true); // 标记为修正点
            point.put("source_file", originalPoint.get("source_file"));
            
            trajectoryPoints.add(point);
        }
        
        return trajectoryPoints;
    }
}
