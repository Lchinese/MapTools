package com.maptools.gpstools.admin;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.LinearRing;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.impl.CoordinateArraySequence;
import org.geotools.geometry.jts.JTSFactoryFinder;

import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.Filters;
import org.bson.Document;

import com.maptools.gpstools.util.ConfigManager;
import com.maptools.gpstools.util.GeoFilter;

/**
 * 初始化行政区划边界数据
 * 预先将行政区划边界数据保存到MongoDB中，避免在处理过程中频繁请求API
 */
public class InitializeAdministrativeAreas {
    
    // 使用配置管理器
    private static ConfigManager config = ConfigManager.getInstance();
    
    public static void main(String[] args) {
        System.out.println("开始初始化行政区划边界数据...");
        
        // 初始化默认区域边界数据
        initializeDefaultAreaBoundary();
        
        System.out.println("行政区划边界数据初始化完成。");
    }
    
    /**
     * 初始化默认区域边界数据
     */
    private static void initializeDefaultAreaBoundary() {
        String areaCode = config.getDefaultAreaCode();
        String areaName = config.getDefaultAreaName();
        
        System.out.println("初始化" + areaName + "边界数据...");
        
        // 检查数据库中是否已存在边界数据
        if (checkBoundaryExists(areaCode)) {
            System.out.println(areaName + "边界数据已存在，跳过初始化。");
            return;
        }
        
        // 创建边界多边形（使用矩形近似）
        MultiPolygon polygon = createApproximateBoundary();
        
        // 保存到MongoDB
        GeoFilter.saveBoundaryToMongoDB(areaCode, areaName, polygon);
        
        System.out.println(areaName + "边界数据初始化完成。");
    }
    
    /**
     * 检查边界数据是否已存在
     * 
     * @param areaCode 行政区划代码
     * @return 如果存在返回true，否则返回false
     */
    private static boolean checkBoundaryExists(String areaCode) {
        MongoClient mongoClient = null;
        try {
            mongoClient = new MongoClient(config.getMongoDBConnectionString());
            MongoDatabase database = mongoClient.getDatabase(config.getMongoDBDatabaseName());
            MongoCollection<Document> collection = database.getCollection("administrative_areas");
            
            Document doc = collection.find(Filters.eq("gb_code", areaCode)).first();
            return doc != null;
        } catch (Exception e) {
            System.err.println("检查边界数据是否存在时出错: " + e.getMessage());
            return false;
        } finally {
            if (mongoClient != null) {
                mongoClient.close();
            }
        }
    }
    
    /**
     * 创建近似的边界（使用深圳边界范围作为示例）
     * 
     * @return 边界多边形
     */
    private static MultiPolygon createApproximateBoundary() {
        // 边界坐标范围
        double MIN_LNG = 113.812401;
        double MAX_LNG = 114.269966;
        double MIN_LAT = 22.503099;
        double MAX_LAT = 22.748068;
        
        // 创建边界多边形（使用矩形近似）
        GeometryFactory geometryFactory = JTSFactoryFinder.getGeometryFactory(null);
        
        Coordinate[] coordinates = new Coordinate[] {
            new Coordinate(MIN_LNG, MIN_LAT),
            new Coordinate(MAX_LNG, MIN_LAT),
            new Coordinate(MAX_LNG, MAX_LAT),
            new Coordinate(MIN_LNG, MAX_LAT),
            new Coordinate(MIN_LNG, MIN_LAT) // 闭合多边形
        };
        
        // 创建线性环
        CoordinateArraySequence sequence = new CoordinateArraySequence(coordinates);
        LinearRing ring = new LinearRing(sequence, geometryFactory);
        
        // 创建多边形
        Polygon polygon = geometryFactory.createPolygon(ring, null);
        
        // 创建MultiPolygon
        return geometryFactory.createMultiPolygon(new Polygon[] { polygon });
    }
}