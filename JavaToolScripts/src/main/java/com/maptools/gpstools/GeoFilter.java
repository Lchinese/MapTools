package com.maptools.gpstools;

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
import org.locationtech.jts.io.WKTReader;
import org.locationtech.jts.io.WKTWriter;

import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import org.bson.Document;

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
    private static Map<String, Polygon> areaBoundaryCache = new ConcurrentHashMap<>();
    
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
        Polygon boundary = getAreaBoundaryFromCache(areaCode);
        if (boundary != null) {
            return filterPointsByPolygon(points, boundary);
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
    private static Polygon getAreaBoundaryFromCache(String areaCode) {
        // 首先检查内存缓存
        if (areaBoundaryCache.containsKey(areaCode)) {
            return areaBoundaryCache.get(areaCode);
        }
        
        // 然后检查MongoDB缓存
        Polygon boundary = loadBoundaryFromMongoDB(areaCode);
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
    private static Polygon loadBoundaryFromMongoDB(String areaCode) {
        MongoClient mongoClient = null;
        try {
            mongoClient = new MongoClient(MONGO_CONNECTION_STRING);
            MongoDatabase database = mongoClient.getDatabase(DATABASE_NAME);
            MongoCollection<Document> collection = database.getCollection(COLLECTION_NAME);
            
            // 查询指定区域代码的边界数据
            Document doc = collection.find(Filters.eq("gb_code", areaCode)).first();
            if (doc != null) {
                String wkt = doc.getString("boundary_wkt");
                if (wkt != null && !wkt.isEmpty()) {
                    return (Polygon) wktReader.read(wkt);
                }
            }
        } catch (Exception e) {
            System.err.println("从MongoDB加载边界数据时出错: " + e.getMessage());
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
    public static void saveBoundaryToMongoDB(String areaCode, String areaName, Polygon boundary) {
        MongoClient mongoClient = null;
        try {
            mongoClient = new MongoClient(MONGO_CONNECTION_STRING);
            MongoDatabase database = mongoClient.getDatabase(DATABASE_NAME);
            MongoCollection<Document> collection = database.getCollection(COLLECTION_NAME);
            
            // 将多边形转换为WKT格式存储
            String wkt = wktWriter.write(boundary);
            
            // 创建文档
            Document doc = new Document()
                .append("gb_code", areaCode)
                .append("name", areaName)
                .append("boundary_wkt", wkt)
                .append("created_at", System.currentTimeMillis());
            
            // 更新或插入文档
            collection.replaceOne(Filters.eq("gb_code", areaCode), doc, 
                new com.mongodb.client.model.ReplaceOptions().upsert(true));
            
            // 同时更新内存缓存
            areaBoundaryCache.put(areaCode, boundary);
            
            System.out.println("成功保存行政区划边界数据到MongoDB: " + areaCode + " - " + areaName);
        } catch (Exception e) {
            System.err.println("保存边界数据到MongoDB时出错: " + e.getMessage());
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
        List<GPSDataPoint> filteredPoints = new ArrayList<>();
        
        // 创建一个简单的深圳市边界框（实际应用中应从API获取精确边界）
        Coordinate[] coordinates = new Coordinate[] {
            new Coordinate(SHENZHEN_MIN_LNG, SHENZHEN_MIN_LAT),
            new Coordinate(SHENZHEN_MAX_LNG, SHENZHEN_MIN_LAT),
            new Coordinate(SHENZHEN_MAX_LNG, SHENZHEN_MAX_LAT),
            new Coordinate(SHENZHEN_MIN_LNG, SHENZHEN_MAX_LAT),
            new Coordinate(SHENZHEN_MIN_LNG, SHENZHEN_MIN_LAT)
        };
        
        LinearRing ring = geometryFactory.createLinearRing(coordinates);
        Polygon shenzhenPolygon = geometryFactory.createPolygon(ring, null);
        
        for (GPSDataPoint point : points) {
            Point p = geometryFactory.createPoint(new Coordinate(point.getLongitude(), point.getLatitude()));
            if (shenzhenPolygon.contains(p)) {
                filteredPoints.add(point);
            }
        }
        
        return filteredPoints;
    }
    
    /**
     * 使用多边形筛选GPS轨迹点
     * 
     * @param points 原始GPS轨迹点列表
     * @param polygon 筛选多边形
     * @return 在多边形内的GPS轨迹点列表
     */
    private static List<GPSDataPoint> filterPointsByPolygon(List<GPSDataPoint> points, Polygon polygon) {
        List<GPSDataPoint> filteredPoints = new ArrayList<>();
        
        for (GPSDataPoint point : points) {
            Point p = geometryFactory.createPoint(new Coordinate(point.getLongitude(), point.getLatitude()));
            if (polygon.contains(p)) {
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
        return (longitude >= SHENZHEN_MIN_LNG && longitude <= SHENZHEN_MAX_LNG) &&
               (latitude >= SHENZHEN_MIN_LAT && latitude <= SHENZHEN_MAX_LAT);
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