export const detectDeviceType = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  // Check for mobile devices
  const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
  
  // Check for tablet
  const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent);
  
  // Check for touch capability
  const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  
  return {
    isMobile,
    isTablet,
    isDesktop: !isMobile && !isTablet,
    isTouch,
    userAgent
  };
};

export const getOptimalResolution = () => {
  const deviceType = detectDeviceType();
  
  if (deviceType.isMobile) {
    return { width: 640, height: 480 };
  } else if (deviceType.isTablet) {
    return { width: 960, height: 720 };
  } else {
    return { width: 1280, height: 720 };
  }
};

export const getOptimalFrameRate = () => {
  const deviceType = detectDeviceType();
  
  if (deviceType.isMobile) {
    return 15;
  } else if (deviceType.isTablet) {
    return 20;
  } else {
    return 30;
  }
};

export const checkCameraSupport = async () => {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return { supported: false, error: 'Camera API not supported' };
    }
    
    // Check for permissions
    const permissions = await navigator.permissions.query({ name: 'camera' });
    
    return {
      supported: true,
      permission: permissions.state,
      canRequest: permissions.state !== 'denied'
    };
  } catch (error) {
    return { supported: false, error: error.message };
  }
};

export const getBrowserInfo = () => {
  const userAgent = navigator.userAgent;
  let browserName = 'Unknown';
  let browserVersion = '';
  
  if (userAgent.match(/chrome|chromium|crios/i)) {
    browserName = 'Chrome';
  } else if (userAgent.match(/firefox|fxios/i)) {
    browserName = 'Firefox';
  } else if (userAgent.match(/safari/i)) {
    browserName = 'Safari';
  } else if (userAgent.match(/opr\//i)) {
    browserName = 'Opera';
  } else if (userAgent.match(/edg/i)) {
    browserName = 'Edge';
  }
  
  return {
    name: browserName,
    version: browserVersion,
    userAgent: userAgent,
    language: navigator.language,
    platform: navigator.platform
  };
};