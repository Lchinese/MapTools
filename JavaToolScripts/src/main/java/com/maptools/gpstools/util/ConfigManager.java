package com.maptools.gpstools.util;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * 配置管理器
 * 管理应用程序的各种配置参数
 */
public class ConfigManager {
    private static final String CONFIG_FILE = "application.properties";
    private static ConfigManager instance;
    private Properties properties;
    
    private ConfigManager() {
        loadProperties();
    }
    
    public static synchronized ConfigManager getInstance() {
        if (instance == null) {
            instance = new ConfigManager();
        }
        return instance;
    }
    
    private void loadProperties() {
        properties = new Properties();
        try (InputStream input = getClass().getClassLoader().getResourceAsStream(CONFIG_FILE)) {
            if (input == null) {
                System.err.println("无法找到配置文件: " + CONFIG_FILE);
                return;
            }
            properties.load(input);
        } catch (IOException ex) {
            System.err.println("加载配置文件时出错: " + ex.getMessage());
        }
    }
    
    // MongoDB配置
    public String getMongoDBConnectionString() {
        return properties.getProperty("mongodb.connection.string", "mongodb://localhost:27017");
    }
    
    public String getMongoDBDatabaseName() {
        return properties.getProperty("mongodb.database.name", "MapTools");
    }
    
    // 天地图API配置
    public String getTiandituApiKey() {
        return properties.getProperty("tianditu.api.key", "your_tianditu_api_key_here");
    }
    
    public String getTiandituAdminApiUrl() {
        return properties.getProperty("tianditu.admin.api.url", "http://api.tianditu.gov.cn/v2/administrative");
    }
    
    // 地理筛选配置
    public String getDefaultAreaCode() {
        return properties.getProperty("default.area.code", "156440300");
    }
    
    public String getDefaultAreaName() {
        return properties.getProperty("default.area.name", "深圳市");
    }
    
    // API请求频率控制
    public long getApiRateLimitMinInterval() {
        return Long.parseLong(properties.getProperty("api.rate.limit.min.interval", "1000"));
    }
    
    public int getApiRateLimitDailyMax() {
        return Integer.parseInt(properties.getProperty("api.rate.limit.daily.max", "10000"));
    }
    
    // 日志配置
    public String getLogDirectory() {
        return properties.getProperty("log.directory", "logs");
    }
    
    /**
     * 重新加载配置文件
     */
    public void reload() {
        loadProperties();
    }
}