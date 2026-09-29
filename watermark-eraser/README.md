# Watermark Eraser

A single web page that removes a logo or stamp sitting in one fixed spot on a video.
Everything runs in the browser; the video is never uploaded.

## How to use it

1. Open `index.html` in Chrome, Edge, Firefox or Safari (or use the published Artifact link).
2. Click **Choose video** (or drop a file on the frame).
3. Drag a box a little bigger than the logo. Toggle **Before / After** to check the fill.
4. Click **Remove watermark**. The video plays through once while it is processed, so a
   3-minute clip takes about 3 minutes. Keep the tab open and visible.
5. Play the result, then click **Save video**.

## What to expect

- **Works well:** a logo, channel name or date stamp in one fixed spot over a fairly plain
  area (sky, wall, floor, blurred background).
- **Leaves a soft patch:** over faces, text or busy detail the box shows a smooth smudge.
- **Won't work:** watermarks that move, or one logo repeated across the whole picture.

Output is MP4 in Chrome, Edge and Safari and WebM in Firefox, with the sound kept.

Use it on videos you made or have permission to edit.

## How it works

Each box is filled by blending the pixels just outside its four edges (weighted by
distance, like FFmpeg's `delogo` filter), then smoothed with a few relaxation passes. The
page draws every frame to a canvas, fills the boxes, and records the canvas plus the
original audio with the browser's `MediaRecorder`. Browser-recorded WebM files get their
duration written into the header so players can seek them.
