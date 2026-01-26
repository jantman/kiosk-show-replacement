# Video URL Slides Missing Duration Detection and Format Check

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

When a video slide is added or edited using a URL instead of a file upload, the video duration detection and video format validation do not occur. These checks only appear to run for uploaded video files.

This means:
- Video slides added via URL will not have their duration automatically detected
- Invalid or unsupported video formats provided via URL are not caught during slide creation/editing

The duration detection and format checking logic needs to be extended to also handle video URLs.
