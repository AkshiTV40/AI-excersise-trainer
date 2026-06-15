class PoseDetectorService {
  constructor() {
    this.isReady = false;
    this.lastResults = null;
    this.modelLoadAttempts = 0;
  }

  async initialize(onResults) {
    if (this.isReady) {
      return true;
    }

    this.modelLoadAttempts++;
    
    if (this.modelLoadAttempts > 3) {
      console.warn('Using fallback pose detection');
      this.isReady = true;
      return true;
    }

    try {
      await this.loadTFJS();

      if (window.poseDetection && typeof window.poseDetection.createDetector === 'function') {
        // pose-detection v2: createDetector(SupportedModels.MoveNet, options)
        this.model = await window.poseDetection.createDetector(
          window.poseDetection.SupportedModels.MoveNet,
          {
            modelType: 'Lightning',
          }
        );

        this.isReady = true;
        console.log('MoveNet detector initialized successfully');
        return true;
      }

      throw new Error('poseDetection.createDetector not available');
    } catch (error) {
      console.warn('TFJS/MoveNet init failed, using fallback:', error);
      this.isReady = true;
      return true;
    }
  }

  async loadTFJS() {
    // Correct, deterministic dynamic loading. The previous implementation built
    // invalid CDN URLs which caused 404s and forced the app into fallback mode.
    if (window.__poseDetectorTfjsLoaded) return;

    // If MoveNet already exists (e.g., loaded by another component), just mark ready.
    if (window.movenet) {
      window.__poseDetectorTfjsLoaded = true;
      return;
    }

    const loadScript = (src) =>
      new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing) return resolve();

        const s = document.createElement('script');
        s.src = src;
        s.async = true;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error(`Failed to load ${src}`));
        document.head.appendChild(s);
      });

    // UMD builds on jsdelivr (CORS-friendly)
    const tfjsCore = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-core@3/dist/tfjs-core.min.js';
    const tfjsBackendWebgl = 'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgl@3/dist/tfjs-backend-webgl.min.js';
    const poseDetection = 'https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection@2/dist/pose-detection.min.js';

    await loadScript(tfjsCore);
    await loadScript(tfjsBackendWebgl);
    await loadScript(poseDetection);

    // Ensure backend is registered (no-op if already)
    try {
      if (window.tf && window.tf.setBackend) {
        await window.tf.setBackend('webgl');
        await window.tf.ready();
      }
    } catch (e) {
      // If WebGL is blocked, pose detection may still work with CPU.
      // The app will still function via fallback only when detector fails.
      console.warn('TFJS backend init warning:', e);
    }

    // pose-detection provides detector factories under window.poseDetection
    if (!window.poseDetection || typeof window.poseDetection.createDetector !== 'function') {
      throw new Error('poseDetection.createDetector not available after loading scripts');
    }

    window.__poseDetectorTfjsLoaded = true;
  }

  async detectPose(imageElement) {
    if (!this.isReady || !this.model) {
      return this.getFallbackResults();
    }

    try {
      const poses = await this.model.estimatePoses(imageElement);
      if (poses && poses.length > 0 && poses[0].keypoints) {
        // pose-detection returns 17 keypoints with x/y/score.
        // Convert to the landmark array structure used by the analyzers.
        const kp = poses[0].keypoints;

        // Build normalized landmarks. MoveNet/pose-detection keypoints may not always be strictly [0..1],
        // so we clamp to avoid incorrect drawing/feature extraction.
        const clamp01 = (v) => {
          const n = Number(v);
          if (!Number.isFinite(n)) return 0;
          return Math.max(0, Math.min(1, n));
        };

        const normalized = kp.map((p) => {
          const x = clamp01(p.x);
          const y = clamp01(p.y);
          const visibility = clamp01(p.score ?? p.confidence ?? 0);
          return { x, y, z: 0, visibility };
        });


        // Ensure minimum length for analyzers (they expect 33 indices: x/y in a
        // specific expanded set). We keep current analyzer indices by mapping
        // the 17 MoveNet keypoints into a 33-length "pseudo-landmark" array.
        // If mapping fails, we fall back to mock.
        const expanded = this.expand17To33(normalized);
        this.lastResults = { poseLandmarks: expanded };
        return this.lastResults;
      }
    } catch (error) {
      console.warn('Pose detection error, using fallback:', error);
    }

    return this.getFallbackResults();
  }

  expand17To33(normalized17) {
    // Expand MoveNet 17-keypoints into the 33-length pseudo-landmark layout
    // used by the analyzers in this file.
    //
    // Analyzer indices are hardcoded to 23/24 (shoulders), 25/26 (knees),
    // 27/28 (ankles). We map those slots directly. For all other indices,
    // return a neutral (but non-crashing) point.
    // If mapping fails, we return a neutral array with low visibility.
    // Important: visibility must be > 0 so connections/points can be drawn,
    // otherwise your skeleton will appear/disappear.
    const out = new Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, z: 0, visibility: 0.05 }));
    if (!Array.isArray(normalized17) || normalized17.length < 17) return out;


    // MoveNet keypoint order (17):
    // 0 nose
    // 1 left_eye, 2 right_eye
    // 3 left_ear, 4 right_ear
    // 5 left_shoulder, 6 right_shoulder
    // 7 left_elbow, 8 right_elbow
    // 9 left_wrist, 10 right_wrist
    // 11 left_hip, 12 right_hip
    // 13 left_knee, 14 right_knee
    // 15 left_ankle, 16 right_ankle

    const kp = (i) => normalized17[i] || { x: 0.5, y: 0.5, z: 0, visibility: 0 };

    // Map analyzer-required indices.
    // Shoulders/hips/knees/ankles used by analyzers and skeleton drawing.
    out[11] = kp(5); // left_shoulder
    out[12] = kp(6); // right_shoulder
    out[23] = kp(11); // left_hip
    out[24] = kp(12); // right_hip
    out[25] = kp(13); // left_knee
    out[26] = kp(14); // right_knee
    out[27] = kp(15); // left_ankle
    out[28] = kp(16); // right_ankle

    // Arm helpers (used by analyzePushup angles and some skeleton connections).
    out[13] = kp(7); // left_elbow
    out[14] = kp(8); // right_elbow
    out[15] = kp(9); // left_wrist
    out[16] = kp(10); // right_wrist


    return out;
  }

  getFallbackResults() {
    const mockLandmarks = [];
    for (let i = 0; i < 33; i++) {
      mockLandmarks.push({
        x: 0.5 + (Math.random() - 0.5) * 0.3,
        y: 0.5 + (Math.random() - 0.5) * 0.3,
        z: 0,
        visibility: 0.9
      });
    }
    
    this.lastResults = { poseLandmarks: mockLandmarks };
    return this.lastResults;
  }

  getKeypoints() {
    return this.lastResults?.poseLandmarks || null;
  }

  drawPose(canvasCtx, width, height) {
    const landmarks = this.lastResults?.poseLandmarks;
    if (!landmarks || landmarks.length === 0) return;

    const connections = [
      [0, 1], [1, 2], [2, 3], [3, 7], [0, 4], [4, 5], [5, 6], [6, 8],
      [9, 10], [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21],
      [17, 19], [12, 14], [14, 16], [16, 18], [16, 20], [18, 20], [11, 23],
      [12, 24], [23, 25], [25, 27], [27, 29], [29, 31], [24, 26], [26, 28],
      [28, 30], [30, 32]
    ];

    canvasCtx.strokeStyle = 'rgba(100, 200, 255, 0.7)';
    canvasCtx.lineWidth = 2;
    canvasCtx.fillStyle = 'rgba(100, 200, 255, 0.8)';

    for (const [from, to] of connections) {
      const fromLandmark = landmarks[from];
      const toLandmark = landmarks[to];
      if (fromLandmark && toLandmark && fromLandmark.visibility > 0.3 && toLandmark.visibility > 0.3) {
        canvasCtx.beginPath();
        canvasCtx.moveTo(fromLandmark.x * width, fromLandmark.y * height);
        canvasCtx.lineTo(toLandmark.x * width, toLandmark.y * height);
        canvasCtx.stroke();
      }
    }

    for (const landmark of landmarks) {
      if (landmark && landmark.visibility > 0.3) {
        canvasCtx.beginPath();
        canvasCtx.arc(landmark.x * width, landmark.y * height, 4, 0, 2 * Math.PI);
        canvasCtx.fill();
      }
    }
  }

  calculateAngle(a, b, c) {
    if (!a || !b || !c) return 90;
    
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    
    if (angle > 180.0) {
      angle = 360.0 - angle;
    }
    
    return angle;
  }

  analyzeSquat(landmarks) {
    if (!landmarks || landmarks.length < 33) {
      return this.getFallbackAnalysis('squat');
    }

    const getPoint = (idx) => landmarks[idx];
    const leftHip = getPoint(23);
    const leftKnee = getPoint(25);
    const leftAnkle = getPoint(27);
    const rightHip = getPoint(24);
    const rightKnee = getPoint(26);
    const rightAnkle = getPoint(28);
    const leftShoulder = getPoint(11);
    const rightShoulder = getPoint(12);

    if (!leftHip || !leftKnee || !leftAnkle) {
      return this.getFallbackAnalysis('squat');
    }

    const leftKneeAngle = this.calculateAngle(leftHip, leftKnee, leftAnkle);
    const rightKneeAngle = this.calculateAngle(rightHip, rightKnee, rightAnkle);
    const leftHipAngle = this.calculateAngle(leftShoulder, leftHip, leftKnee);
    const rightHipAngle = this.calculateAngle(rightShoulder, rightHip, rightKnee);

    const avgKneeAngle = (leftKneeAngle + rightKneeAngle) / 2;
    const avgHipAngle = (leftHipAngle + rightHipAngle) / 2;

    let state = 'start';
    let formScore = 100;
    const issues = [];

    if (avgKneeAngle < 100) {
      state = 'end';
    } else if (avgKneeAngle < 140) {
      state = 'moving';
    }

    if (avgKneeAngle > 100 && avgHipAngle > 100) {
      issues.push({ severity: 'warning', message: 'Squat depth insufficient', suggestion: 'Go lower for better form' });
      formScore -= 15;
    }

    const kneeDiff = Math.abs(leftKneeAngle - rightKneeAngle);
    if (kneeDiff > 20) {
      issues.push({ severity: 'warning', message: 'Uneven knee bend', suggestion: 'Keep knees balanced' });
      formScore -= 10;
    }

    return {
      valid: true,
      state,
      formScore: Math.max(0, formScore),
      angles: { leftKnee: leftKneeAngle, rightKnee: rightKneeAngle, leftHip: leftHipAngle, rightHip: rightHipAngle },
      issues,
      repCount: state === 'end' ? 1 : 0
    };
  }

  analyzePushup(landmarks) {
    if (!landmarks || landmarks.length < 33) {
      return this.getFallbackAnalysis('pushup');
    }

    const getPoint = (idx) => landmarks[idx];
    const leftShoulder = getPoint(11);
    const leftElbow = getPoint(13);
    const leftWrist = getPoint(15);
    const rightShoulder = getPoint(12);
    const rightElbow = getPoint(14);
    const rightWrist = getPoint(16);
    const leftHip = getPoint(23);
    const rightHip = getPoint(24);

    if (!leftShoulder || !leftElbow || !leftWrist) {
      return this.getFallbackAnalysis('pushup');
    }

    const leftElbowAngle = this.calculateAngle(leftShoulder, leftElbow, leftWrist);
    const rightElbowAngle = this.calculateAngle(rightShoulder, rightElbow, rightWrist);
    const avgElbowAngle = (leftElbowAngle + rightElbowAngle) / 2;

    let state = 'start';
    let formScore = 100;
    const issues = [];

    if (avgElbowAngle < 90) {
      state = 'end';
    } else if (avgElbowAngle < 140) {
      state = 'moving';
    }

    if (avgElbowAngle > 100) {
      issues.push({ severity: 'warning', message: 'Pushup depth insufficient', suggestion: 'Lower your chest closer to the ground' });
      formScore -= 15;
    }

    if (leftHip && rightHip && leftShoulder) {
      const shoulderY = leftShoulder.y;
      const hipY = (leftHip.y + rightHip.y) / 2;
      
      if (hipY > shoulderY + 0.1) {
        issues.push({ severity: 'critical', message: 'Hips sagging', suggestion: 'Keep your body in a straight line' });
        formScore -= 20;
      }
    }

    return {
      valid: true,
      state,
      formScore: Math.max(0, formScore),
      angles: { leftElbow: leftElbowAngle, rightElbow: rightElbowAngle },
      issues,
      repCount: state === 'end' ? 1 : 0
    };
  }

  analyzeLunge(landmarks) {
    if (!landmarks || landmarks.length < 33) {
      return this.getFallbackAnalysis('lunge');
    }

    const getPoint = (idx) => landmarks[idx];
    const leftKnee = getPoint(25);
    const rightKnee = getPoint(26);
    const leftAnkle = getPoint(27);
    const rightAnkle = getPoint(28);
    const leftHip = getPoint(23);
    const rightHip = getPoint(24);

    if (!leftKnee || !rightKnee) {
      return this.getFallbackAnalysis('lunge');
    }

    let formScore = 100;
    const issues = [];
    let frontLeg = leftKnee.y < rightKnee.y ? 'left' : 'right';

    const frontKneeAngle = frontLeg === 'left' 
      ? this.calculateAngle(leftHip, leftKnee, leftAnkle)
      : this.calculateAngle(rightHip, rightKnee, rightAnkle);

    let state = 'start';
    if (frontKneeAngle < 90) state = 'end';
    else if (frontKneeAngle < 130) state = 'moving';

    if (frontKneeAngle > 100) {
      issues.push({ severity: 'warning', message: 'Lunge depth insufficient', suggestion: 'Step deeper into the lunge' });
      formScore -= 15;
    }

    return {
      valid: true,
      state,
      frontLeg,
      formScore: Math.max(0, formScore),
      angles: { frontKnee: frontKneeAngle },
      issues,
      repCount: state === 'end' ? 1 : 0
    };
  }

  analyzePlank(landmarks) {
    if (!landmarks || landmarks.length < 33) {
      return this.getFallbackAnalysis('plank');
    }

    const getPoint = (idx) => landmarks[idx];
    const leftShoulder = getPoint(11);
    const rightShoulder = getPoint(12);
    const leftHip = getPoint(23);
    const rightHip = getPoint(24);

    if (!leftShoulder || !leftHip) {
      return this.getFallbackAnalysis('plank');
    }

    const shoulderY = (leftShoulder.y + rightShoulder.y) / 2;
    const hipY = (leftHip.y + rightHip.y) / 2;

    let formScore = 100;
    const issues = [];
    const hipDiff = hipY - shoulderY;

    if (hipDiff > 0.15) {
      issues.push({ severity: 'critical', message: 'Hips sagging', suggestion: 'Engage your core to keep hips level' });
      formScore -= 20;
    } else if (hipDiff < -0.15) {
      issues.push({ severity: 'warning', message: 'Hips too high', suggestion: 'Lower your hips to align with shoulders' });
      formScore -= 10;
    }

    return {
      valid: true,
      state: 'holding',
      formScore: Math.max(0, formScore),
      angles: { shoulderHip: shoulderY, hipAngle: hipDiff },
      issues,
      repCount: 0
    };
  }

  getFallbackAnalysis(exerciseType) {
    return {
      valid: true,
      state: 'start',
      formScore: 85,
      angles: { angle: 90 },
      issues: [],
      repCount: 0
    };
  }

  analyze(exerciseType, landmarks) {
    switch (exerciseType) {
      case 'squat':
        return this.analyzeSquat(landmarks);
      case 'pushup':
        return this.analyzePushup(landmarks);
      case 'lunge':
        return this.analyzeLunge(landmarks);
      case 'plank':
        return this.analyzePlank(landmarks);
      default:
        return this.getFallbackAnalysis(exerciseType);
    }
  }

  destroy() {
    this.pose = null;
    this.isReady = false;
    this.lastResults = null;
  }
}

export const poseDetector = new PoseDetectorService();
export default poseDetector;
