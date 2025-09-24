package com.maptools.gpstools;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class GPSDataProcessor {
    // 减小线程池大小以减少内存占用
    private static final int THREAD_POOL_SIZE = 4; // 从10减小到4
    private static final int BATCH_SIZE = 1000; // 批处理大小
    
    // 使用配置管理器
    private ConfigManager config = ConfigManager.getInstance();
    
    // 是否启用地理筛选
    private boolean geoFilterEnabled = false;
    // 筛选的区域代码
    private String filterAreaCode;
    
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java GPSDataProcessor <data_directory> [options]");
            System.err.println("Options:");
            System.err.println("  --filter-area=<area_code>  按行政区划代码筛选轨迹点 (默认: " + 
                             ConfigManager.getInstance().getDefaultAreaCode() + ")");
            System.err.println("  --no-filter                禁用地理筛选");
            System.exit(1);
        }
        
        String dataPath = args[0];
        GPSDataProcessor processor = new GPSDataProcessor();
        
        // 设置默认区域代码
        processor.filterAreaCode = ConfigManager.getInstance().getDefaultAreaCode();
        
        // 解析命令行参数
        for (int i = 1; i < args.length; i++) {
            if (args[i].startsWith("--filter-area=")) {
                processor.geoFilterEnabled = true;
                processor.filterAreaCode = args[i].substring("--filter-area=".length());
            } else if ("--no-filter".equals(args[i])) {
                processor.geoFilterEnabled = false;
            }
        }
        
        File dataFile = new File(dataPath);
        if (dataFile.exists() && dataFile.isFile()) {
            // 处理单个文件
            processor.processSingleFile(dataFile);
        } else {
            // 处理目录
            processor.processData(dataPath);
        }
    }
    
    public void processData(String dataDirectory) {
        File dir = new File(dataDirectory);
        if (!dir.exists() || !dir.isDirectory()) {
            System.err.println("Invalid directory: " + dataDirectory);
            return;
        }
        
        // 保留必要的目录处理信息
        // 减少初始输出信息
        System.out.println("开始处理目录: " + dir.getName());
        if (geoFilterEnabled) {
            System.out.println("地理筛选已启用，区域代码: " + filterAreaCode);
        }
        
        // 创建线程池
        ExecutorService executor = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        
        MongoDataStore dataStore = new MongoDataStore();
        
        try {
            // 处理子目录
            File[] subDirs = dir.listFiles(File::isDirectory);
            if (subDirs != null) {
                for (File subDir : subDirs) {
                    processDirectory(subDir, dataStore, executor);
                }
            }
            
            // 处理当前目录下的文件
            File[] files = dir.listFiles((d, name) -> name.endsWith("-utf.txt"));
            
            if (files != null && files.length > 0) {
                processFiles(dir, files, "gps_points_data", dataStore, executor);
            }
        } finally {
            // 关闭线程池
            executor.shutdown();
            try {
                // 等待所有任务完成
                if (!executor.awaitTermination(60, TimeUnit.MINUTES)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException e) {
                executor.shutdownNow();
            }
            
            // 打印处理总结
            dataStore.printSummary();
            dataStore.close();
        }
    }
    
    public void processSingleFile(File file) {
        System.out.println("开始处理文件: " + file.getName());
        if (geoFilterEnabled) {
            System.out.println("地理筛选已启用，区域代码: " + filterAreaCode);
        }
        
        // 创建线程池
        ExecutorService executor = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        
        MongoDataStore dataStore = new MongoDataStore();
        
        try {
            // 创建包含单个文件的数组
            File[] files = new File[]{file};
            processFiles(file.getParentFile(), files, "gps_points_data", dataStore, executor);
        } finally {
            // 关闭线程池
            executor.shutdown();
            try {
                // 等待所有任务完成
                if (!executor.awaitTermination(60, TimeUnit.MINUTES)) {
                    executor.shutdownNow();
                }
            } catch (InterruptedException e) {
                executor.shutdownNow();
            }
            
            // 打印处理总结
            dataStore.printSummary();
            dataStore.close();
        }
    }
    
    private void processDirectory(File dir, MongoDataStore dataStore, ExecutorService executor) {
        // 获取目录名作为集合名 (01, 02, 03等)
        String dirName = dir.getName();
        String collectionName = "gps_points_" + dirName;
        
        // 修改文件过滤规则，使其能处理所有-utf.txt文件
        File[] files = dir.listFiles((d, name) -> name.endsWith("-utf.txt"));
        
        if (files != null && files.length > 0) {
            processFiles(dir, files, collectionName, dataStore, executor);
        }
    }
    
    private void processFiles(File dir, File[] files, String collectionName, MongoDataStore dataStore, ExecutorService executor) {
        System.out.println("开始处理目录 " + dir.getName() + " 下的 " + files.length + " 个文件");
        
        AtomicInteger fileCounter = new AtomicInteger(0);
        int totalFiles = files.length;
        
        // 为每个文件创建处理任务
        for (File file : files) {
            executor.submit(() -> {
                try {
                    // 检查文件是否已经处理过
                    if (dataStore.isFileProcessed(collectionName, file.getName())) {
                        int processed = fileCounter.incrementAndGet();
                        String currentTime = java.time.LocalTime.now().format(java.time.format.DateTimeFormatter.ofPattern("HH:mm:ss"));
                        System.out.println(String.format("[%s] 文件 %d/%d: %s | 已处理，跳过", 
                            currentTime, processed, totalFiles, file.getName()));
                        return;
                    }
                    
                    // 使用流式处理避免一次性加载整个文件到内存
                    processFileInBatches(file, collectionName, dataStore, fileCounter, totalFiles);
                } catch (Exception e) {
                    System.err.println("处理文件时出错: " + file.getName() + " - " + e.getMessage());
                    e.printStackTrace();
                }
            });
        }
    }
    
    /**
     * 分批处理文件以减少内存占用
     */
    private void processFileInBatches(File file, String collectionName, MongoDataStore dataStore, 
                                      AtomicInteger fileCounter, int totalFiles) throws IOException {
        GPSDataParser parser = new GPSDataParser();
        String fileName = file.getName();
        
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), "UTF-8"))) {
            
            String line;
            int lineNumber = 0;
            int totalPoints = 0;
            int validPointCount = 0;
            
            // 分批处理数据
            java.util.List<GPSDataPoint> batchPoints = new java.util.ArrayList<>(BATCH_SIZE);
            
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                GPSDataPoint point = parser.parseLine(line, lineNumber, fileName);
                if (point != null) {
                    totalPoints++;
                    batchPoints.add(point);
                    
                    // 当批次达到指定大小时进行处理
                    if (batchPoints.size() >= BATCH_SIZE) {
                        validPointCount += processBatch(batchPoints, collectionName, fileName, dataStore);
                        batchPoints.clear(); // 清空批次以释放内存
                    }
                }
            }
            
            // 处理剩余的数据
            if (!batchPoints.isEmpty()) {
                validPointCount += processBatch(batchPoints, collectionName, fileName, dataStore);
            }
            
            // 输出处理信息
            int processed = fileCounter.incrementAndGet();
            String currentTime = java.time.LocalTime.now().format(java.time.format.DateTimeFormatter.ofPattern("HH:mm:ss"));
            System.out.println(String.format("[%s] 文件 %d/%d: %s | 总点数: %d | 合法点数: %d", 
                currentTime, processed, totalFiles, fileName, totalPoints, validPointCount));
        } finally {
            parser.close();
        }
    }
    
    /**
     * 处理一批数据
     */
    private int processBatch(java.util.List<GPSDataPoint> batchPoints, String collectionName, 
                             String fileName, MongoDataStore dataStore) {
        // 如果需要地理筛选，进行筛选
        java.util.List<GPSDataPoint> pointsToSave = batchPoints;
        if (geoFilterEnabled && filterAreaCode != null) {
            pointsToSave = GeoFilter.filterPointsByArea(batchPoints, filterAreaCode);
        }
        
        // 保存到MongoDB
        dataStore.saveGPSPoints(pointsToSave, collectionName, fileName);
        return pointsToSave.size();
    }
}