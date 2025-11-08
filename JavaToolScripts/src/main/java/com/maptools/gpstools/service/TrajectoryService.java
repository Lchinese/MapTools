package com.maptools.gpstools.service;

import com.maptools.gpstools.processor.TrajectoryCorrectionProcessor;
import java.util.List;
import java.util.Map;

/**
 * 轨迹服务类
 * 提供轨迹处理相关功能的统一接口
 */
public class TrajectoryService {
    private TrajectoryCorrectionProcessor trajectoryCorrector;
    
    public TrajectoryService() {
        this.trajectoryCorrector = new TrajectoryCorrectionProcessor();
    }
    
    /**
     * 修正轨迹
     * @param originalPoints 原始轨迹点
     * @return 修正后的轨迹点
     */
    public List<Map<String, Object>> correctTrajectory(List<Map<String, Object>> originalPoints) {
        return trajectoryCorrector.correctTrajectory(originalPoints);
    }
    
    /**
     * 获取处理统计信息
     * @return 统计信息Map
     */
    public Map<String, Long> getStatistics() {
        return trajectoryCorrector.getStatistics();
    }
    
    /**
     * 重置统计信息
     */
    public void resetStatistics() {
        trajectoryCorrector.resetStatistics();
    }
    
    /**
     * 关闭轨迹修正器
     */
    public void close() {
        if (trajectoryCorrector != null) {
            trajectoryCorrector.close();
        }
    }
}