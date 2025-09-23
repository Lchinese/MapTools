package com.maptools.gpstools;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.InputStreamReader;
import java.io.FileInputStream;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;

public class GPSDataParser {
    private PrintWriter logWriter;
    
    public GPSDataParser() {
        try {
            // 创建日志文件写入器
            this.logWriter = new PrintWriter(new FileWriter("logs/parsing_errors.log", true));
        } catch (IOException e) {
            System.err.println("无法创建解析错误日志文件: " + e.getMessage());
            this.logWriter = null;
        }
    }
    
    /**
     * 解析GPS数据文件
     * 
     * @param filePath 文件路径
     * @return GPS轨迹点列表
     * @throws IOException 文件读取异常
     */
    public List<GPSDataPoint> parseFile(String filePath) throws IOException {
        return parseFile(filePath, false, null);
    }
    
    /**
     * 解析GPS数据文件，可选择是否进行地理筛选
     * 
     * @param filePath 文件路径
     * @param filterByArea 是否按区域筛选
     * @param areaCode 区域代码，如"156440300"代表深圳市
     * @return GPS轨迹点列表
     * @throws IOException 文件读取异常
     */
    public List<GPSDataPoint> parseFile(String filePath, boolean filterByArea, String areaCode) throws IOException {
        List<GPSDataPoint> gpsPoints = new ArrayList<>();
        String fileName = filePath.substring(filePath.lastIndexOf("\\") + 1);
        
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(filePath), "UTF-8"))) {
            String line;
            int lineNumber = 0;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                GPSDataPoint point = parseLine(line, lineNumber, fileName);
                if (point != null) {
                    gpsPoints.add(point);
                }
            }
        }
        
        // 如果需要按区域筛选，则进行筛选
        if (filterByArea && areaCode != null && !areaCode.isEmpty()) {
            int originalCount = gpsPoints.size();
            gpsPoints = GeoFilter.filterPointsByArea(gpsPoints, areaCode);
            int filteredCount = gpsPoints.size();
            
            // 记录筛选日志
            synchronized (this) {
                if (logWriter != null) {
                    logWriter.println("[" + fileName + "] 地理筛选: 原始点数=" + originalCount + ", 筛选后点数=" + filteredCount);
                    logWriter.flush();
                }
            }
        }
        
        return gpsPoints;
    }
    
    private GPSDataPoint parseLine(String line, int lineNumber, String sourceFile) {
        try {
            String[] parts = line.split(",");
            if (parts.length != 10) {
                // 将错误信息写入日志文件而不是终端输出
                synchronized (this) {
                    if (logWriter != null) {
                        logWriter.println("[" + sourceFile + ":" + lineNumber + "] 字段数不为10，跳过");
                        logWriter.flush();
                    }
                }
                return null;
            }
            
            String dateStr = parts[0].trim();
            String timeStr = parts[1].trim();
            String recordType = parts[2].trim();
            String plateNumber = parts[3].trim();
            double longitude = Double.parseDouble(parts[4].trim());
            double latitude = Double.parseDouble(parts[5].trim());
            double speed = Double.parseDouble(parts[6].trim());
            double heading = Double.parseDouble(parts[7].trim());
            String reservedField = parts[8].trim();
            int locationFlag = Integer.parseInt(parts[9].trim());
            
            // 构建时间
            LocalDateTime datetime;
            try {
                // 处理时间字段，确保是6位数字格式
                String paddedTime = padTime(timeStr);
                DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
                datetime = LocalDateTime.parse(dateStr + paddedTime, formatter);
            } catch (DateTimeParseException e) {
                // 将时间格式错误信息写入日志文件而不是终端输出
                synchronized (this) {
                    if (logWriter != null) {
                        logWriter.println("[" + sourceFile + ":" + lineNumber + "] 时间格式错误，跳过");
                        logWriter.flush();
                    }
                }
                return null;
            }
            
            boolean isValid = (locationFlag == 1);
            
            return new GPSDataPoint(plateNumber, datetime, dateStr, timeStr, recordType,
                                  longitude, latitude, speed, heading, reservedField, 
                                  locationFlag, isValid, sourceFile);
        } catch (Exception e) {
            // 将解析失败信息写入日志文件而不是终端输出
            synchronized (this) {
                if (logWriter != null) {
                    logWriter.println("[" + sourceFile + ":" + lineNumber + "] 解析失败: " + e.getMessage());
                    logWriter.flush();
                }
            }
            return null;
        }
    }
    
    /**
     * 补全时间字符串为6位数字格式
     * 
     * @param timeStr 时间字符串
     * @return 6位数字格式的时间字符串
     */
    private String padTime(String timeStr) {
        // 确保时间是6位数字格式
        while (timeStr.length() < 6) {
            timeStr = "0" + timeStr;
        }
        return timeStr;
    }
    
    public void close() {
        // 关闭日志文件写入器
        if (logWriter != null) {
            logWriter.close();
        }
    }
}