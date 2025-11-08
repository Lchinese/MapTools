package com.maptools.gpstools.util;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.ConcurrentHashMap;

import org.geotools.geometry.jts.JTSFactoryFinder;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.LinearRing;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.io.WKTReader;
import org.locationtech.jts.io.WKTWriter;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientURI;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import org.bson.Document;

import com.maptools.gpstools.model.GPSDataPoint;

/**
 * 地理位置筛选器
 * 根据行政区划边界筛选GPS轨迹点
 * 参考可行性文档中的天地图行政区划API集成方案实现
 * 实现了缓存机制以避免频繁API请求
 */
public class GeoFilter {
    
    // 使用配置管理器
    private static ConfigManager config = ConfigManager.getInstance();
    
    // 深圳市边界坐标范围（根据可行性文档中的示例数据）
    // 经度范围
    private static final double SHENZHEN_MIN_LNG = 113.812401;
    private static final double SHENZHEN_MAX_LNG = 114.269966;
    
    // 纬度范围
    private static final double SHENZHEN_MIN_LAT = 22.503099;
    private static final double SHENZHEN_MAX_LAT = 22.748068;
    
    // 本地缓存行政区划边界数据
    private static Map<String, MultiPolygon> areaBoundaryCache = new ConcurrentHashMap<>();
    
    // MongoDB连接相关
    private static final String MONGO_CONNECTION_STRING = config.getMongoDBConnectionString();
    private static final String DATABASE_NAME = config.getMongoDBDatabaseName();
    private static final String COLLECTION_NAME = "administrative_areas";
    
    private static GeometryFactory geometryFactory = JTSFactoryFinder.getGeometryFactory(null);
    private static WKTReader wktReader = new WKTReader(geometryFactory);
    private static WKTWriter wktWriter = new WKTWriter();
    
    /**
     * 筛选指定区域内的GPS轨迹点
     * 根据可行性文档中的天地图行政区划API集成方案实现
     * 
     * @param points 原始GPS轨迹点列表
     * @param areaCode 行政区划代码，如"156440300"代表深圳市
     * @return 筛选后的GPS轨迹点列表
     */
    public static List<GPSDataPoint> filterPointsByArea(List<GPSDataPoint> points, String areaCode) {
        // 对于默认区域，使用特定方法
        if (config.getDefaultAreaCode().equals(areaCode)) {
            return filterPointsInDefaultArea(points);
        }
        
        // 对于其他区域，先尝试从缓存获取边界数据
        MultiPolygon boundary = getAreaBoundaryFromCache(areaCode);
        if (boundary != null) {
            return filterPointsByMultiPolygon(points, boundary);
        }
        
        // 如果缓存中没有，则使用默认的边界框筛选
        return new ArrayList<>(points);
    }
    
    /**
     * 筛选默认区域内的GPS轨迹点
     * 
     * @param points 原始GPS轨迹点列表
     * @return 筛选后的GPS轨迹点列表
     */
    public static List<GPSDataPoint> filterPointsInDefaultArea(List<GPSDataPoint> points) {
        return filterPointsInShenzhen(points);
    }
    
    /**
     * 从缓存获取区域边界数据
     * 
     * @param areaCode 行政区划代码
     * @return 区域边界多边形，如果未找到则返回null
     */
    private static MultiPolygon getAreaBoundaryFromCache(String areaCode) {
        // 首先检查内存缓存
        if (areaBoundaryCache.containsKey(areaCode)) {
            return areaBoundaryCache.get(areaCode);
        }
        
        // 然后检查MongoDB缓存
        MultiPolygon boundary = loadBoundaryFromMongoDB(areaCode);
        if (boundary != null) {
            // 存储到内存缓存
            areaBoundaryCache.put(areaCode, boundary);
            return boundary;
        }
        
        return null;
    }
    
    /**
     * 从MongoDB加载行政区划边界数据
     * 
     * @param areaCode 行政区划代码
     * @return 区域边界多边形，如果未找到则返回null
     */
    private static MultiPolygon loadBoundaryFromMongoDB(String areaCode) {
        MongoClient mongoClient = null;
        try {
            System.out.println("正在连接MongoDB: " + MONGO_CONNECTION_STRING);
            mongoClient = new MongoClient(new MongoClientURI(MONGO_CONNECTION_STRING));
            
            // 测试连接
            mongoClient.getDatabase("admin").runCommand(new Document("ping", 1));
            System.out.println("MongoDB连接成功");
            
            MongoDatabase database = mongoClient.getDatabase(DATABASE_NAME);
            MongoCollection<Document> collection = database.getCollection(COLLECTION_NAME);
            
            // 查询指定区域代码的边界数据
            System.out.println("查询区域代码: " + areaCode);
            Document doc = collection.find(Filters.eq("gb_code", areaCode)).first();
            if (doc != null) {
                System.out.println("找到边界数据: " + doc.getString("name"));
                // 从GeoJSON格式读取边界数据
                Document boundaryDoc = (Document) doc.get("boundary");
                if (boundaryDoc != null) {
                    String type = boundaryDoc.getString("type");
                    System.out.println("边界类型: " + type);
                    if ("MultiPolygon".equals(type)) {
                        // 解析MultiPolygon
                        List<List<List<List<Double>>>> coordinates = 
                            (List<List<List<List<Double>>>>) boundaryDoc.get("coordinates");
                        
                        List<Polygon> polygons = new ArrayList<>();
                        for (List<List<List<Double>>> polygonCoords : coordinates) {
                            // 只处理外环（第一个环），忽略洞
                            List<List<Double>> exteriorRingCoords = polygonCoords.get(0);
                            
                            Coordinate[] coords = new Coordinate[exteriorRingCoords.size()];
                            for (int i = 0; i < exteriorRingCoords.size(); i++) {
                                List<Double> coord = exteriorRingCoords.get(i);
                                coords[i] = new Coordinate(coord.get(0), coord.get(1));
                            }
                            
                            LinearRing ring = geometryFactory.createLinearRing(coords);
                            Polygon polygon = geometryFactory.createPolygon(ring);
                            polygons.add(polygon);
                        }
                        
                        System.out.println("成功解析边界数据，多边形数量: " + polygons.size());
                        return geometryFactory.createMultiPolygon(polygons.toArray(new Polygon[0]));
                    }
                }
            } else {
                System.out.println("未找到区域代码 " + areaCode + " 的边界数据");
            }
        } catch (Exception e) {
            System.err.println("从MongoDB加载边界数据时出错: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (mongoClient != null) {
                mongoClient.close();
            }
        }
        
        return null;
    }
    
    /**
     * 将行政区划边界数据保存到MongoDB
     * 
     * @param areaCode 行政区划代码
     * @param areaName 行政区划名称
     * @param boundary 区域边界多边形
     */
    public static void saveBoundaryToMongoDB(String areaCode, String areaName, MultiPolygon boundary) {
        MongoClient mongoClient = null;
        try {
            mongoClient = new MongoClient(new MongoClientURI(MONGO_CONNECTION_STRING));
            MongoDatabase database = mongoClient.getDatabase(DATABASE_NAME);
            MongoCollection<Document> collection = database.getCollection(COLLECTION_NAME);
            
            // 将多边形转换为GeoJSON格式存储
            List<List<List<List<Double>>>> coordinates = new ArrayList<>();
            for (int i = 0; i < boundary.getNumGeometries(); i++) {
                Polygon polygon = (Polygon) boundary.getGeometryN(i);
                List<List<List<Double>>> polygonCoords = new ArrayList<>();
                
                // 添加外环坐标
                Coordinate[] exteriorCoords = polygon.getExteriorRing().getCoordinates();
                List<List<Double>> exteriorRing = new ArrayList<>();
                for (Coordinate coord : exteriorCoords) {
                    List<Double> point = new ArrayList<>();
                    point.add(coord.getX());
                    point.add(coord.getY());
                    exteriorRing.add(point);
                }
                polygonCoords.add(exteriorRing);
                
                coordinates.add(polygonCoords);
            }
            
            Document boundaryDoc = new Document()
                .append("type", "MultiPolygon")
                .append("coordinates", coordinates);
            
            // 创建文档
            Document doc = new Document()
                .append("gb_code", areaCode)
                .append("name", areaName)
                .append("boundary", boundaryDoc)
                .append("created_at", new java.util.Date());
            
            // 更新或插入文档
            collection.replaceOne(Filters.eq("gb_code", areaCode), doc, 
                new com.mongodb.client.model.ReplaceOptions().upsert(true));
            
            // 同时更新内存缓存
            areaBoundaryCache.put(areaCode, boundary);
            
            System.out.println("成功保存行政区划边界数据到MongoDB: " + areaCode + " - " + areaName);
        } catch (Exception e) {
            System.err.println("保存边界数据到MongoDB时出错: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (mongoClient != null) {
                mongoClient.close();
            }
        }
    }
    
    /**
     * 筛选出在深圳范围内的轨迹点
     * 根据可行性文档5.3.2节的功能应用场景实现
     * 
     * @param points 原始GPS轨迹点列表
     * @return 在深圳范围内的GPS轨迹点列表
     */
    public static List<GPSDataPoint> filterPointsInShenzhen(List<GPSDataPoint> points) {
        // 强制从数据库获取精确的深圳市边界
        MultiPolygon shenzhenBoundary = getAreaBoundaryFromCache(config.getDefaultAreaCode());
        if (shenzhenBoundary != null) {
            System.out.println("使用数据库中的精确深圳边界数据进行筛选");
            return filterPointsByMultiPolygon(points, shenzhenBoundary);
        }
        
        // 如果数据库中没有边界数据，报错并返回空列表
        System.err.println("错误：数据库中未找到深圳边界数据，请先运行InitializeAdministrativeAreas初始化边界数据");
        return new ArrayList<>();
    }
    
    /**
     * 使用多边形筛选GPS轨迹点
     * 
     * @param points 原始GPS轨迹点列表
     * @param multiPolygon 筛选多边形
     * @return 在多边形内的GPS轨迹点列表
     */
    private static List<GPSDataPoint> filterPointsByMultiPolygon(List<GPSDataPoint> points, MultiPolygon multiPolygon) {
        List<GPSDataPoint> filteredPoints = new ArrayList<>();
        
        for (GPSDataPoint point : points) {
            Point p = geometryFactory.createPoint(new Coordinate(point.getLongitude(), point.getLatitude()));
            if (multiPolygon.contains(p)) {
                filteredPoints.add(point);
            }
        }
        
        return filteredPoints;
    }
    
    /**
     * 判断轨迹点是否在深圳范围内
     * 根据可行性文档5.3.3节的技术实现方案实现
     * 
     * @param longitude 经度
     * @param latitude 纬度
     * @return 如果点在深圳范围内返回true，否则返回false
     */
    public static boolean isPointInShenzhen(double longitude, double latitude) {
        // 检查经纬度是否在深圳市边界范围内
        boolean inBoundingBox = (longitude >= SHENZHEN_MIN_LNG && longitude <= SHENZHEN_MAX_LNG) &&
               (latitude >= SHENZHEN_MIN_LAT && latitude <= SHENZHEN_MAX_LAT);
        
        if (!inBoundingBox) {
            return false;
        }
        
        // 如果在边界框内，进一步检查是否在精确边界内
        MultiPolygon shenzhenBoundary = getAreaBoundaryFromCache(config.getDefaultAreaCode());
        if (shenzhenBoundary != null) {
            Point p = geometryFactory.createPoint(new Coordinate(longitude, latitude));
            return shenzhenBoundary.contains(p);
        }
        
        // 如果没有精确边界数据，则只检查边界框
        return true;
    }
    
    /**
     * 根据自定义边界多边形筛选GPS轨迹点
     * 
     * @param points 原始GPS轨迹点列表
     * @param wktPolygon 多边形的WKT表示
     * @return 在指定多边形内的GPS轨迹点列表
     */
    public static List<GPSDataPoint> filterPointsByPolygon(List<GPSDataPoint> points, String wktPolygon) {
        List<GPSDataPoint> filteredPoints = new ArrayList<>();
        
        try {
            Polygon polygon = (Polygon) wktReader.read(wktPolygon);
            
            for (GPSDataPoint point : points) {
                Point p = geometryFactory.createPoint(new Coordinate(point.getLongitude(), point.getLatitude()));
                if (polygon.contains(p)) {
                    filteredPoints.add(point);
                }
            }
        } catch (Exception e) {
            System.err.println("解析多边形边界时出错: " + e.getMessage());
            // 出错时返回所有点
            return new ArrayList<>(points);
        }
        
        return filteredPoints;
    }
    
    /**
     * 根据自定义边界框筛选GPS轨迹点
     * 
     * @param points 原始GPS轨迹点列表
     * @param minLng 最小经度
     * @param maxLng 最大经度
     * @param minLat 最小纬度
     * @param maxLat 最大纬度
     * @return 在指定边界框内的GPS轨迹点列表
     */
    public static List<GPSDataPoint> filterPointsByBoundingBox(
            List<GPSDataPoint> points, 
            double minLng, 
            double maxLng, 
            double minLat, 
            double maxLat) {
        
        List<GPSDataPoint> filteredPoints = new ArrayList<>();
        
        for (GPSDataPoint point : points) {
            if ((point.getLongitude() >= minLng && point.getLongitude() <= maxLng) &&
                (point.getLatitude() >= minLat && point.getLatitude() <= maxLat)) {
                filteredPoints.add(point);
            }
        }
        
        return filteredPoints;
    }
}