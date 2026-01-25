# Video Format Validation

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

While researching a bug where videos were not playing (which has now been fixed), this note appeared in the analysis:

> The bug report mentions `crash_into_pole.mpeg` which is an MPEG-1 format that browsers don't support in HTML5 video. However, there is a valid test file `test_video_5s.mp4` available. The fix should work with properly supported formats (MP4/WebM).

Please implement video format validation (server-side, probably using ffprobe which we already rely on) to only allow uploads of videos that will actually play in the frontend (i.e. are a supported format/codec). If the user uploads a video that isn't supported, they should get a clear error message explaining why and which formats are supported. Please ensure that you add (if not already present) integration tests for actual uploads through the frontend of a supported and unsupported video, and that the tests verify the proper error message for the unsupported video format upload.
