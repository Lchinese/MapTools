package com.maptools.gpstools;

/**
 * API请求频率控制器
 * 控制对天地图API的请求频率，避免因请求过于频繁而被限制
 */
public class APIRateLimiter {
    // 使用配置管理器获取配置参数
    private static ConfigManager config = ConfigManager.getInstance();
    
    // 最小请求间隔（毫秒）
    private static final long MIN_REQUEST_INTERVAL = config.getApiRateLimitMinInterval();
    
    // 最后一次请求的时间戳
    private static volatile long lastRequestTime = 0;
    
    // 天地图API的请求配额信息
    private static final int MAX_DAILY_REQUESTS = config.getApiRateLimitDailyMax();
    private static volatile int dailyRequestCount = 0;
    private static volatile long lastRequestDate = 0;
    
    /**
     * 等待下一次API请求
     * 确保请求间隔不小于最小间隔时间
     */
    public static synchronized void waitForNextRequest() {
        long now = System.currentTimeMillis();
        long timeSinceLastRequest = now - lastRequestTime;
        
        // 检查是否需要等待
        if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
            long waitTime = MIN_REQUEST_INTERVAL - timeSinceLastRequest;
            try {
                Thread.sleep(waitTime);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
        
        // 更新最后请求时间
        lastRequestTime = System.currentTimeMillis();
        
        // 更新每日请求计数
        updateDailyRequestCount();
    }
    
    /**
     * 更新每日请求计数
     */
    private static void updateDailyRequestCount() {
        long now = System.currentTimeMillis();
        long currentDate = now / (24 * 60 * 60 * 1000); // 以天为单位的日期
        
        // 如果是新的一天，重置计数器
        if (currentDate > lastRequestDate) {
            dailyRequestCount = 0;
            lastRequestDate = currentDate;
        }
        
        // 增加请求计数
        dailyRequestCount++;
    }
    
    /**
     * 检查是否超过每日请求限制
     * 
     * @return 如果超过限制返回true，否则返回false
     */
    public static boolean isDailyLimitExceeded() {
        long now = System.currentTimeMillis();
        long currentDate = now / (24 * 60 * 60 * 1000); // 以天为单位的日期
        
        // 如果是新的一天，重置计数器
        if (currentDate > lastRequestDate) {
            dailyRequestCount = 0;
            lastRequestDate = currentDate;
        }
        
        return dailyRequestCount >= MAX_DAILY_REQUESTS;
    }
    
    /**
     * 获取当前每日请求计数
     * 
     * @return 当前每日请求计数
     */
    public static int getDailyRequestCount() {
        long now = System.currentTimeMillis();
        long currentDate = now / (24 * 60 * 60 * 1000); // 以天为单位的日期
        
        // 如果是新的一天，重置计数器
        if (currentDate > lastRequestDate) {
            dailyRequestCount = 0;
            lastRequestDate = currentDate;
        }
        
        return dailyRequestCount;
    }
    
    /**
     * 获取每日剩余请求数
     * 
     * @return 剩余请求数
     */
    public static int getRemainingDailyRequests() {
        return Math.max(0, MAX_DAILY_REQUESTS - getDailyRequestCount());
    }
    
    /**
     * 重新加载配置
     */
    public static void reloadConfig() {
        config.reload();
        // 注意：静态变量不会自动更新，需要重启应用或手动更新
    }
}