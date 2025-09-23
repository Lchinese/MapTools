package com.maptools.gpstools;

import java.io.File;
import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class GPSDataProcessor {
    private static final int THREAD_POOL_SIZE = 10; // 线程池大小
    
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
        
        String dataDirectory = args[0];
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
        
        processor.processData(dataDirectory);
    }
    
    public void processData(String dataDirectory) {
        File dir = new File(dataDirectory);
        if (!dir.exists() || !dir.isDirectory()) {
            System.err.println("Invalid directory: " + dataDirectory);
            return;
        }
        
        System.out.println("开始处理目录: " + dir.getName());
        if (geoFilterEnabled) {
            System.out.println("地理筛选已启用，区域代码: " + filterAreaCode);
        } else {
            System.out.println("地理筛选已禁用");
        }
        
        // 创建线程池
        ExecutorService executor = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
        
        MongoDataStore dataStore = new MongoDataStore();
        
        try {
            processDirectory(dir, dataStore, executor);
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
        System.out.println("Processing directory: " + dir.getName());
        
        // 获取目录名作为集合名 (01, 02, 03等)
        String dirName = dir.getName();
        String collectionName = "gps_points_" + dirName;
        
        // 修改文件过滤规则，使其能处理sample-utf.txt文件
        File[] files = dir.listFiles((d, name) -> name.endsWith("-utf.txt") || name.equals("sample-utf.txt"));
        if (files == null || files.length == 0) {
            System.out.println("No GPS data files found in " + dir.getName());
            return;
        }
        
        System.out.println("Found " + files.length + " files in " + dir.getName());
        
        // 计数器，用于跟踪已完成的文件数
        AtomicInteger completedFiles = new AtomicInteger(0);
        
        // 使用线程池处理每个文件
        for (int i = 0; i < files.length; i++) {
            final File file = files[i];
            final int fileIndex = i + 1;
            
            executor.submit(() -> {
                GPSDataParser parser = new GPSDataParser();
                try {
                    System.out.println("Starting to process file (" + fileIndex + "/" + files.length + "): " + file.getName());
                    long startTime = System.currentTimeMillis();
                    
                    // 解析文件，根据设置决定是否进行地理筛选
                    java.util.List<GPSDataPoint> points = parser.parseFile(file.getAbsolutePath(), geoFilterEnabled, filterAreaCode);
                    
                    // 保存数据
                    dataStore.saveGPSPoints(points, collectionName, file.getName());
                    
                    long endTime = System.currentTimeMillis();
                    int completed = completedFiles.incrementAndGet();
                    System.out.println("Completed processing file (" + fileIndex + "/" + files.length + "): " + file.getName() + 
                                     " (" + points.size() + " points, " + (endTime - startTime) + "ms)" +
                                     " [" + completed + "/" + files.length + " files completed]");
                } catch (IOException e) {
                    System.err.println("Error processing file (" + fileIndex + "/" + files.length + "): " + file.getName() + " - " + e.getMessage());
                    completedFiles.incrementAndGet();
                } finally {
                    parser.close();
                }
            });
        }
        
        System.out.println("All " + files.length + " files submitted to thread pool for processing in " + dir.getName());
    }
}