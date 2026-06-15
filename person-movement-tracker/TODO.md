# TODO - person-movement-tracker

## Completed
- Added `frontend/src/components/RecordSession.jsx` with live recording UI and **Download Video** link after `session_complete`.
- Updated `frontend/src/App.jsx` to render the new `RecordSession` component.

## Next
1. Verify build (frontend) runs without import/path errors.
2. Ensure `useRecordSession` integrates correctly (start/stop + websocket lifecycle).
3. Make YOLO skeleton drawing robust for any YOLO usage in the live flow.
4. Run backend tests (if available) and/or a quick smoke test of `/ws/record-session`.

