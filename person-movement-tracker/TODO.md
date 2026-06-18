# TODO - AI Exercise Trainer refactor

## Step 1: WebSocket lifecycle + stop button stability
- [x] Update `frontend/src/hooks/useRecordSession.js` to avoid unhandled promise rejections after stop
- [x] Update `frontend/src/components/RecordSession.jsx` so Stop stops capture loop first, then sends WS stop

- [ ] Harden backend `@app.websocket("/ws/record-session")` to send final terminal message exactly once




## Step 2: Server-side MediaPipe tracking + skeleton recording
- [ ] Update backend `@app.websocket("/ws/record-session")` to annotate frames with MediaPipe Pose
- [ ] Write annotated frames to `recorded_exercise_skeleton.mp4`
- [ ] Return a session_complete payload containing a URL/path for the recorded MP4 and feedback

## Step 3: UI updates
- [ ] Add “Download Video” button visible only after recording stops and session_complete arrives
- [ ] Update feedback rendering to handle markdown and clear old feedback immediately at session start

## Step 4: Replace Qwen/HuggingFace with Google Gemini
- [ ] Remove Qwen/HF guidance service usage from backend code path
- [ ] Ensure Gemini model `gemini-2.5-pro` is used

## Step 5: Verification
- [ ] Start recording: confirm no TFJS errors, confirm MP4 is generated server-side
- [ ] Stop recording: verify WS closes cleanly with no console promise errors
- [ ] Start a second session: confirm old feedback clears
- [ ] Confirm feedback comes from Gemini

