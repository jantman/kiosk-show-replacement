# Video Format Validation

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

While researching a bug where videos were not playing (which has now been fixed), this note appeared in the analysis:

> The bug report mentions `crash_into_pole.mpeg` which is an MPEG-1 format that browsers don't support in HTML5 video. However, there is a valid test file `test_video_5s.mp4` available. The fix should work with properly supported formats (MP4/WebM).

Please implement video format validation (server-side, probably using ffprobe which we already rely on) to only allow uploads of videos that will actually play in the frontend (i.e. are a supported format/codec). If the user uploads a video that isn't supported, they should get a clear error message explaining why and which formats are supported. Please ensure that you add (if not already present) integration tests for actual uploads through the frontend of a supported and unsupported video, and that the tests verify the proper error message for the unsupported video format upload.

---

## Implementation Plan

### Background Research

**Current State:**
- Videos are validated by file extension and MIME type only
- ffprobe is already used for duration extraction in `kiosk_show_replacement/storage.py`
- The allowed extensions include `.mpeg`, `.mpg`, `.avi`, `.wmv`, `.flv`, `.mkv` which may use browser-incompatible codecs
- The integration test `test_add_video_item_via_file_upload` uses `crash_into_pole.mpeg` which has MPEG-1 codec (not supported by HTML5)

**Browser-Compatible Video Formats (HTML5 `<video>`):**
- **MP4** container with **H.264** (AVC) video codec - universally supported
- **WebM** container with **VP8** or **VP9** video codec - most modern browsers
- **Ogg** container with **Theora** video codec - limited support

**Test Assets Available:**
- `tests/assets/test_video_5s.mp4` - H.264 codec in MP4 container (browser supported)
- `tests/assets/crash_into_pole.mpeg` - MPEG-1 video codec (NOT browser supported)

### Implementation Approach

The validation will happen at upload time using ffprobe to extract codec information. Videos with unsupported codecs will be rejected with a clear error message.

---

## Milestones

### Milestone 1: Add Video Codec Validation to Backend (VFV-M1)

**Goal:** Add server-side validation that checks video codecs and rejects unsupported formats.

#### Task 1.1 (VFV-M1.1): Add video codec extraction function to storage.py
- Add a new `get_video_codec_info()` function that uses ffprobe to extract video codec information
- Uses ffprobe with `-show_streams` flag to get codec details
- Returns codec name and container format

#### Task 1.2 (VFV-M1.2): Add video format validation function
- Create `validate_video_format()` function that checks if codec is browser-compatible
- Supported codecs: `h264`, `vp8`, `vp9`, `theora`
- Returns tuple of (is_valid, error_message)

#### Task 1.3 (VFV-M1.3): Integrate validation into save_file()
- After initial validation passes, save file to temp location
- Call `validate_video_format()` on saved file
- If validation fails:
  - Log a detailed WARNING-level message with: filename, detected codec, container format, and file path for troubleshooting
  - Delete temp file and return error to user
- If validation passes, proceed as normal

#### Task 1.4 (VFV-M1.4): Add unit tests for codec validation
- Test `get_video_codec_info()` with mocked ffprobe responses
- Test `validate_video_format()` with various codec names
- Test error handling for ffprobe failures

**Milestone 1 Deliverables:**
- Video codec extraction and validation functions in `storage.py`
- WARNING-level logging for rejected uploads with detailed troubleshooting info
- Unit tests for new functions in `tests/unit/test_storage.py`
- All existing tests still pass

---

### Milestone 2: Update Integration Tests (VFV-M2)

**Goal:** Update existing integration tests and add new tests for format validation.

#### Task 2.1 (VFV-M2.1): Update test_add_video_item_via_file_upload
- Change from `crash_into_pole.mpeg` to `test_video_5s.mp4`
- This test now tests successful upload of a supported format

#### Task 2.2 (VFV-M2.2): Add test for unsupported video format upload
- Create new test `test_video_upload_unsupported_format_shows_error`
- Upload `crash_into_pole.mpeg` (MPEG-1 format)
- Verify error message appears in UI
- Verify error message mentions supported formats
- Verify item is NOT created via API

**Milestone 2 Deliverables:**
- Updated integration test using supported video format
- New integration test verifying rejection of unsupported format
- All tests pass

---

### Milestone 3: Acceptance Criteria (VFV-M3)

**Goal:** Final verification and documentation.

#### Task 3.1 (VFV-M3.1): Verify all nox sessions pass
- Run all nox sessions: `test-3.14`, `test-integration`, `test-e2e`, `lint`, `type_check`, `format`
- Fix any failures

#### Task 3.2 (VFV-M3.2): Update documentation
- Update `README.md` with supported video formats information
- Update `CLAUDE.md` if any development workflow changes are needed
- Update `docs/*.rst` files as appropriate (e.g., deployment docs, user guide)
- Document the supported video codecs (H.264, VP8, VP9, Theora) and container formats

#### Task 3.3 (VFV-M3.3): Move feature file to completed
- Move this file from `docs/features/` to `docs/features/completed/`

**Milestone 3 Deliverables:**
- All nox sessions passing
- Documentation updated (README.md, CLAUDE.md, docs/*.rst as appropriate)
- Feature file moved to completed directory

---

## Progress Log

### 2026-01-25 - Milestone 1 Complete
- VFV-M1.1: Added `get_video_codec_info()` function to storage.py
- VFV-M1.2: Added `validate_video_format()` function with supported codecs: h264, vp8, vp9, theora, av1
- VFV-M1.3: Integrated validation into `save_file()` with WARNING-level logging for rejected uploads
- VFV-M1.4: Added comprehensive unit tests (18 new tests) for codec extraction and validation
- All 466 unit tests passing

### [Date] - Planning Complete
- Implementation plan created and committed
- Awaiting human approval to proceed with Milestone 1
