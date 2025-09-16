import { create } from 'zustand';
import { trajectoryAPI, matchingAPI } from '../Services/api';

const useTrajectoryStore = create((set, get) => ({
  // 状态
  trajectories: [],
  currentTrajectory: null,
  matchingTasks: [],
  currentTask: null,
  loading: false,
  error: null,

  // 轨迹相关操作
  fetchTrajectories: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const response = await trajectoryAPI.list(params);
      set({ trajectories: response.data || [], loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  fetchTrajectory: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await trajectoryAPI.get(id);
      set({ currentTrajectory: response.data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  uploadTrajectory: async (file, metadata = {}) => {
    set({ loading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', metadata.name || file.name);
      formData.append('description', metadata.description || '');
      formData.append('data_source', metadata.dataSource || 'auto');
      formData.append('data_category', metadata.dataCategory || 'continuous_trajectory');

      const response = await trajectoryAPI.upload(formData);
      set({ loading: false });
      
      // 刷新轨迹列表
      get().fetchTrajectories();
      
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  deleteTrajectory: async (id) => {
    set({ loading: true, error: null });
    try {
      await trajectoryAPI.delete(id);
      set({ loading: false });
      
      // 从列表中移除
      set(state => ({
        trajectories: state.trajectories.filter(t => t.trajectory_id !== id)
      }));
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // 匹配任务相关操作
  startMatching: async (trajectoryId, algorithm = 'distance_matching', parameters = {}) => {
    set({ loading: true, error: null });
    try {
      const response = await matchingAPI.start({
        trajectory_id: trajectoryId,
        algorithm,
        parameters
      });
      set({ loading: false });
      
      // 刷新任务列表
      get().fetchMatchingTasks();
      
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  fetchMatchingTasks: async (params = {}) => {
    set({ loading: true, error: null });
    try {
      const response = await matchingAPI.list(params);
      set({ matchingTasks: response.data || [], loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  fetchTaskStatus: async (taskId) => {
    try {
      const response = await matchingAPI.status(taskId);
      return response.data;
    } catch (error) {
      set({ error: error.message });
      throw error;
    }
  },

  fetchTaskResult: async (taskId) => {
    set({ loading: true, error: null });
    try {
      const response = await matchingAPI.result(taskId);
      set({ currentTask: response.data, loading: false });
      return response.data;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
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

export default useTrajectoryStore;