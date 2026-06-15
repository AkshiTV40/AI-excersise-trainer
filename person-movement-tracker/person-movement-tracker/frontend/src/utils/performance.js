export class PerformanceMonitor {
  constructor() {
    this.metrics = {
      fps: [],
      inferenceTimes: [],
      memoryUsage: [],
      frameDrops: 0
    };
    this.maxHistory = 100;
    this.lastFrameTime = 0;
    this.frameCount = 0;
    this.isMonitoring = false;
  }

  start() {
    this.isMonitoring = true;
    this.lastFrameTime = performance.now();
    this.monitorLoop();
  }

  stop() {
    this.isMonitoring = false;
  }

  monitorLoop() {
    if (!this.isMonitoring) return;

    const currentTime = performance.now();
    const deltaTime = currentTime - this.lastFrameTime;
    
    // Calculate FPS
    const fps = 1000 / deltaTime;
    this.addMetric('fps', fps);
    
    this.lastFrameTime = currentTime;
    this.frameCount++;

    // Monitor memory if available
    if (performance.memory) {
      this.addMetric('memoryUsage', performance.memory.usedJSHeapSize / (1024 * 1024));
    }

    requestAnimationFrame(() => this.monitorLoop());
  }

  addMetric(type, value) {
    if (!this.metrics[type]) return;
    
    this.metrics[type].push(value);
    
    // Keep only recent history
    if (this.metrics[type].length > this.maxHistory) {
      this.metrics[type].shift();
    }
  }

  recordInferenceTime(time) {
    this.addMetric('inferenceTimes', time);
  }

  getAverageFPS() {
    const fps = this.metrics.fps;
    if (fps.length === 0) return 0;
    return fps.reduce((a, b) => a + b, 0) / fps.length;
  }

  getAverageInferenceTime() {
    const times = this.metrics.inferenceTimes;
    if (times.length === 0) return 0;
    return times.reduce((a, b) => a + b, 0) / times.length;
  }

  getStats() {
    return {
      averageFPS: this.getAverageFPS().toFixed(1),
      averageInferenceTime: this.getAverageInferenceTime().toFixed(2),
      frameCount: this.frameCount,
      memoryUsage: this.metrics.memoryUsage.length > 0 
        ? this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1].toFixed(2) + ' MB'
        : 'N/A'
    };
  }

  reset() {
    this.metrics = {
      fps: [],
      inferenceTimes: [],
      memoryUsage: [],
      frameDrops: 0
    };
    this.frameCount = 0;
  }
}

// Debounce function for performance optimization
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Throttle function for performance optimization
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Measure function execution time
export const measurePerformance = (fn, name) => {
  return async (...args) => {
    const start = performance.now();
    const result = await fn(...args);
    const end = performance.now();
    console.log(`${name} took ${(end - start).toFixed(2)}ms`);
    return result;
  };
};