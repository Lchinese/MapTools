package com.maptools.gpstools.admin;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.File;

import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Polygon;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.LinearRing;
import org.geotools.geometry.jts.JTSFactoryFinder;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonArray;

import com.maptools.gpstools.util.ConfigManager;
import com.maptools.gpstools.util.GeoFilter;

/**
 * 更新行政区划边界数据
 * 从本地GeoJSON文件获取精确的行政区划边界数据并保存到MongoDB中
 */
public class UpdateAdministrativeAreas {
    
    // 使用配置管理器
    private static ConfigManager config = ConfigManager.getInstance();
    
    public static void main(String[] args) {
        System.out.println("开始更新行政区划边界数据...");
        
        // 更新默认区域边界数据
        updateDefaultAreaBoundary();
        
        System.out.println("行政区划边界数据更新完成。");
    }
    
    /**
     * 更新默认区域边界数据
     */
    private static void updateDefaultAreaBoundary() {
        String areaCode = config.getDefaultAreaCode();
        String areaName = config.getDefaultAreaName();
        
        System.out.println("正在从本地GeoJSON文件获取" + areaName + "边界数据...");
        
        try {
            // 首先尝试从本地GeoJSON文件读取数据
            MultiPolygon boundary = loadBoundaryFromGeoJSON();
            
            if (boundary != null) {
                // 保存到MongoDB
                GeoFilter.saveBoundaryToMongoDB(areaCode, areaName, boundary);
                System.out.println(areaName + "边界数据更新完成。");
            } else {
                System.err.println("从本地GeoJSON文件获取边界数据失败。");
                // 使用近似边界
                MultiPolygon approximateBoundary = createApproximateBoundary();
                GeoFilter.saveBoundaryToMongoDB(areaCode, areaName, approximateBoundary);
                System.out.println("使用近似边界数据完成更新。");
            }
        } catch (Exception e) {
            System.err.println("更新" + areaName + "边界数据时出错: " + e.getMessage());
            e.printStackTrace();
            
            // 出错时使用近似边界
            try {
                MultiPolygon approximateBoundary = createApproximateBoundary();
                GeoFilter.saveBoundaryToMongoDB(areaCode, areaName, approximateBoundary);
                System.out.println("使用近似边界数据完成更新。");
            } catch (Exception ex) {
                System.err.println("使用近似边界数据更新时也出错: " + ex.getMessage());
            }
        }
    }
    
    /**
     * 从本地GeoJSON文件加载边界数据
     * 
     * @return 边界多边形或多边形集合
     */
    private static MultiPolygon loadBoundaryFromGeoJSON() {
        try {
            // 查找GeoJSON文件
            String[] possiblePaths = {
                "../深圳市_市.geojson",
                "../../深圳市_市.geojson",
                "深圳市_市.geojson",
                "data/深圳市_市.geojson"
            };
            
            File geojsonFile = null;
            for (String path : possiblePaths) {
                File file = new File(path);
                if (file.exists()) {
                    geojsonFile = file;
                    break;
                }
            }
            
            if (geojsonFile == null) {
                System.out.println("未找到深圳市_市.geojson文件");
                return null;
            }
            
            System.out.println("读取GeoJSON文件: " + geojsonFile.getAbsolutePath());
            
            // 读取文件内容
            StringBuilder content = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new FileReader(geojsonFile))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    content.append(line);
                }
            }
            
            // 解析JSON
            JsonObject jsonObject = JsonParser.parseString(content.toString()).getAsJsonObject();
            
            // 获取features数组
            JsonArray features = jsonObject.getAsJsonArray("features");
            if (features.size() == 0) {
                System.err.println("GeoJSON文件中没有要素");
                return null;
            }
            
            // 获取第一个要素
            JsonObject feature = features.get(0).getAsJsonObject();
            JsonObject geometry = feature.getAsJsonObject("geometry");
            
            String type = geometry.get("type").getAsString();
            if (!"MultiPolygon".equals(type)) {
                System.err.println("不支持的几何类型: " + type);
                return null;
            }
            
            // 解析坐标
            JsonArray coordinatesArray = geometry.getAsJsonArray("coordinates");
            Polygon[] polygons = new Polygon[coordinatesArray.size()];
            
            GeometryFactory geometryFactory = JTSFactoryFinder.getGeometryFactory(null);
            
            for (int i = 0; i < coordinatesArray.size(); i++) {
                // 获取多边形的第一个环（外环）
                JsonArray polygonArray = coordinatesArray.get(i).getAsJsonArray().get(0).getAsJsonArray();
                
                Coordinate[] coordinates = new Coordinate[polygonArray.size()];
                for (int j = 0; j < polygonArray.size(); j++) {
                    JsonArray point = polygonArray.get(j).getAsJsonArray();
                    double lng = point.get(0).getAsDouble();
                    double lat = point.get(1).getAsDouble();
                    coordinates[j] = new Coordinate(lng, lat);
                }
                
                LinearRing ring = geometryFactory.createLinearRing(coordinates);
                polygons[i] = geometryFactory.createPolygon(ring);
            }
            
            return geometryFactory.createMultiPolygon(polygons);
            
        } catch (Exception e) {
            System.err.println("从GeoJSON文件加载边界数据时出错: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
    
    
    /**
     * 创建近似的边界（用于演示或备选方案）
     * 
     * @return 边界多边形
     */
    private static MultiPolygon createApproximateBoundary() {
        // 使用深圳边界坐标范围作为示例
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
        
        // 使用GeometryFactory直接创建LinearRing
        LinearRing ring = geometryFactory.createLinearRing(coordinates);
        Polygon polygon = geometryFactory.createPolygon(ring);
        
        return geometryFactory.createMultiPolygon(new Polygon[] { polygon });
    }
}