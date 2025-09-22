package com.maptools.gpstools;

import java.time.LocalDateTime;

public class GPSDataPoint {
    private String plateNumber; // 车牌号
    private LocalDateTime datetime; // 日期时间
    private String date; // 日期
    private String time; // 时间
    private String recordType; // 记录类型 (H or L)
    private double longitude; // 经度
    private double latitude; // 纬度
    private double speed; // 速度
    private double heading; // 方向
    private String reservedField; // 保留字段
    private int locationFlag; // 定位状态
    private boolean isValid; // 是否有效
    private String sourceFile; // 源文件

    public GPSDataPoint() {
    }

    public GPSDataPoint(String plateNumber, LocalDateTime datetime, String date, String time,
                       String recordType, double longitude, double latitude, double speed,
                       double heading, String reservedField, int locationFlag, boolean isValid,
                       String sourceFile) {
        this.plateNumber = plateNumber;
        this.datetime = datetime;
        this.date = date;
        this.time = time;
        this.recordType = recordType;
        this.longitude = longitude;
        this.latitude = latitude;
        this.speed = speed;
        this.heading = heading;
        this.reservedField = reservedField;
        this.locationFlag = locationFlag;
        this.isValid = isValid;
        this.sourceFile = sourceFile;
    }

    // Getters and setters
    public String getPlateNumber() {
        return plateNumber;
    }

    public void setPlateNumber(String plateNumber) {
        this.plateNumber = plateNumber;
    }

    public LocalDateTime getDatetime() {
        return datetime;
    }

    public void setDatetime(LocalDateTime datetime) {
        this.datetime = datetime;
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public String getTime() {
        return time;
    }

    public void setTime(String time) {
        this.time = time;
    }

    public String getRecordType() {
        return recordType;
    }

    public void setRecordType(String recordType) {
        this.recordType = recordType;
    }

    public double getLongitude() {
        return longitude;
    }

    public void setLongitude(double longitude) {
        this.longitude = longitude;
    }

    public double getLatitude() {
        return latitude;
    }

    public void setLatitude(double latitude) {
        this.latitude = latitude;
    }

    public double getSpeed() {
        return speed;
    }

    public void setSpeed(double speed) {
        this.speed = speed;
    }

    public double getHeading() {
        return heading;
    }

    public void setHeading(double heading) {
        this.heading = heading;
    }

    public String getReservedField() {
        return reservedField;
    }

    public void setReservedField(String reservedField) {
        this.reservedField = reservedField;
    }

    public int getLocationFlag() {
        return locationFlag;
    }

    public void setLocationFlag(int locationFlag) {
        this.locationFlag = locationFlag;
    }

    public boolean isValid() {
        return isValid;
    }

    public void setValid(boolean valid) {
        isValid = valid;
    }

    public String getSourceFile() {
        return sourceFile;
    }

    public void setSourceFile(String sourceFile) {
        this.sourceFile = sourceFile;
    }

    @Override
    public String toString() {
        return "GPSDataPoint{" +
                "plateNumber='" + plateNumber + '\'' +
                ", datetime=" + datetime +
                ", date='" + date + '\'' +
                ", time='" + time + '\'' +
                ", recordType='" + recordType + '\'' +
                ", longitude=" + longitude +
                ", latitude=" + latitude +
                ", speed=" + speed +
                ", heading=" + heading +
                ", reservedField='" + reservedField + '\'' +
                ", locationFlag=" + locationFlag +
                ", isValid=" + isValid +
                ", sourceFile='" + sourceFile + '\'' +
                '}';
    }
}