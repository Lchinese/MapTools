import { create } from 'zustand';
import { trajectoryAPI } from '../Services/api';

const useTrajectoryStore = create((set, get) => ({
  // 状态
  trajectories: [],
  originalTrajectories: {}, // 原始轨迹数据 {plateNumber: trajectoryPoints}
  currentTrajectory: null,
  matchingTasks: [],
  currentTask: null,
  loading: false,
  error: null,
  
  // 分页信息
  pagination: {
    page: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 0
  },

  // 获取原始轨迹数据（从数据库分页查询）
  fetchOriginalTrajectories: async (page = 1, pageSize = 20, plateNumber = null) => {
    set({ loading: true, error: null });
    try {
      const response = await trajectoryAPI.getOriginalTrajectoryData(page, pageSize, plateNumber);
      if (response.success) {
        set({
          originalTrajectories: response.data,
          pagination: response.pagination,
          loading: false
        });
        return response.data;
      } else {
        throw new Error(response.message || '获取原始轨迹数据失败');
      }
    } catch (error) {
      console.error('获取原始轨迹数据失败:', error);
      // 即使API调用失败，也设置默认的分页信息
      set({ 
        error: error.message, 
        loading: false,
        pagination: {
          page: page,
          pageSize: pageSize,
          totalCount: 0,
          totalPages: 0
        }
      });
      throw error;
    }
  },

  // 轨迹相关操作（后端接口已移除，以下返回安全默认值）
  fetchTrajectories: async () => {
    set({ trajectories: [], loading: false, error: null });
  },

  fetchTrajectory: async () => {
    set({ currentTrajectory: null, loading: false, error: null });
  },

  uploadTrajectory: async () => {
    // 后端上传接口已移除，这里仅模拟成功以保持前端流程不报错
    set({ loading: false });
    return { ok: true };
  },

  deleteTrajectory: async () => {
    set({ loading: false });
  },

  // 匹配任务相关操作（后端接口已移除）
  startMatching: async () => {
    set({ loading: false });
    return { ok: true };
  },

  fetchMatchingTasks: async () => {
    set({ matchingTasks: [], loading: false, error: null });
  },

  fetchTaskStatus: async () => {
    return { status: 'not_available' };
  },

  fetchTaskResult: async () => {
    set({ currentTask: null, loading: false });
    return null;
  },

  // 清除错误
  clearError: () => set({ error: null }),

  // 重置状态
  reset: () => set({
    trajectories: [],
    originalTrajectories: {},
    currentTrajectory: null,
    matchingTasks: [],
    currentTask: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      totalCount: 0,
      totalPages: 0
    }
  }),
}));

export { useTrajectoryStore };
export default useTrajectoryStore;