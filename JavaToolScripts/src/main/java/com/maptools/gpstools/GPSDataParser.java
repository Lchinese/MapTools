package com.maptools.gpstools;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
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
    
    public List<GPSDataPoint> parseFile(String filePath) throws IOException {
        List<GPSDataPoint> gpsPoints = new ArrayList<>();
        String fileName = filePath.substring(filePath.lastIndexOf("\\") + 1);
        
        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
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
     * 将时间字符串补全为6位数字格式
     * @param timeStr 时间字符串
     * @return 6位数字格式的时间字符串
     */
    private String padTime(String timeStr) {
        try {
            // 如果已经是6位数字，直接返回
            if (timeStr.length() == 6 && timeStr.matches("\\d{6}")) {
                return timeStr;
            }
            
            // 处理科学计数法等特殊情况
            if (timeStr.contains(".") || timeStr.contains("E") || timeStr.contains("e")) {
                double timeValue = Double.parseDouble(timeStr);
                // 对于非常小的数值（如1.7E-5），当作0处理
                if (Math.abs(timeValue) < 1) {
                    return "000000";
                }
                // 其他情况转换为整数再处理
                int timeInt = (int) Math.round(timeValue);
                return String.format("%06d", timeInt);
            }
            
            // 处理普通的数字字符串
            int timeValue = Integer.parseInt(timeStr);
            // 确保不超过6位数
            if (timeValue > 999999) {
                timeValue = timeValue % 1000000;
            }
            return String.format("%06d", timeValue);
        } catch (NumberFormatException e) {
            // 如果解析失败，默认返回000000
            synchronized (this) {
                if (logWriter != null) {
                    logWriter.println("无法解析时间字段: " + timeStr + "，使用默认值000000");
                    logWriter.flush();
                }
            }
            return "000000";
        }
    }
    
    public void close() {
        // 关闭日志文件写入器
        if (logWriter != null) {
            logWriter.close();
        }
    }
}