import { create } from 'zustand';

const useMapStore = create((set, get) => ({
  // 地图状态
  center: [22.5431, 114.0579], // 深圳
  zoom: 12,
  bounds: null,
  
  // 轨迹数据
  originalTrajectory: null,
  correctedTrajectory: null,
  roadNetwork: null,
  
  // 显示选项
  showOriginal: false,
  showCorrected: true,
  showOSRMRoute: false,
  showRoadNetwork: false,
  
  // 地图操作
  setCenter: (center) => set({ center }),
  setZoom: (zoom) => set({ zoom }),
  setBounds: (bounds) => set({ bounds }),
  
  // 轨迹数据操作
  setOriginalTrajectory: (trajectory) => set({ originalTrajectory: trajectory }),
  setCorrectedTrajectory: (trajectory) => set({ correctedTrajectory: trajectory }),
  setRoadNetwork: (network) => set({ roadNetwork: network }),
  
  // 显示选项操作
  setShowOriginal: (show) => set({ showOriginal: show }),
  setShowCorrected: (show) => set({ showCorrected: show }),
  setShowOSRMRoute: (show) => set({ showOSRMRoute: show }),
  setShowRoadNetwork: (show) => set({ showRoadNetwork: show }),
  toggleOriginal: () => set(state => ({ showOriginal: !state.showOriginal })),
  toggleCorrected: () => set(state => ({ showCorrected: !state.showCorrected })),
  toggleOSRMRoute: () => set(state => ({ showOSRMRoute: !state.showOSRMRoute })),
  toggleRoadNetwork: () => set(state => ({ showRoadNetwork: !state.showRoadNetwork })),
  
  // 重置地图到初始位置
  resetMap: () => set({
    center: [22.5431, 114.0579], // 深圳
    zoom: 12,
    bounds: null,
  }),
  
  // 重置数据
  resetData: () => set({
    originalTrajectory: null,
    matchedTrajectory: null,
    roadNetwork: null,
  }),
  
  // 重置所有
  reset: () => set({
    center: [22.5431, 114.0579], // 深圳
    zoom: 12,
    bounds: null,
    originalTrajectory: null,
    matchedTrajectory: null,
    roadNetwork: null,
    showOriginal: false,
    showCorrected: true,
    showOSRMRoute: false,
    showRoadNetwork: false,
  }),
}));

export { useMapStore };
export default useMapStore;