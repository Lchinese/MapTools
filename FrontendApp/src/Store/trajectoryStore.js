import { create } from 'zustand';

const useTrajectoryStore = create((set, get) => ({
  // 状态
  trajectories: [],
  currentTrajectory: null,
  matchingTasks: [],
  currentTask: null,
  loading: false,
  error: null,

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
    currentTrajectory: null,
    matchingTasks: [],
    currentTask: null,
    loading: false,
    error: null,
  }),
}));

export { useTrajectoryStore };
export default useTrajectoryStore;