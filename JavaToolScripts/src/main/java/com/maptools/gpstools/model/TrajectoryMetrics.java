package com.maptools.gpstools.model;

/**
 * 轨迹指标模型类
 * 用于存储预计算的轨迹指标，避免重复计算
 */
public class TrajectoryMetrics {
    public double[] speeds;           // 速度 (km/h)
    public double[] distances;        // 距离 (m)
    public long[] timeDiffs;          // 时间差 (ms)
    public double[] headings;         // 方向角 (度)
    public double[] headingDiffs;     // 方向变化 (度)
    
    public TrajectoryMetrics(int size) {
        this.speeds = new double[size];
        this.distances = new double[size];
        this.timeDiffs = new long[size];
        this.headings = new double[size];
        this.headingDiffs = new double[size];
    }
}