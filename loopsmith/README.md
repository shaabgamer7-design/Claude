# Loopsmith GIF Studio

A browser-based studio that turns a text prompt or photos into seamless looping animations, published as a claude.ai artifact.

- **Create**: prompt → four takes (Claude directs when available, otherwise a built-in keyword director), 12 one-click styles, meme/reaction captions, 22 templates, photo-to-GIF effects and slideshows.
- **Edit**: layer list and inspector for every property, drag objects on the preview, natural-language refine, undo/redo, JSON recipes.
- **Export**: GIF encoder written from scratch (median-cut palette, ordered or diffusion dithering, changed-pixel frame diffing, transparency, boomerang, motion blur, file-size cap), MP4/WebM via MediaRecorder, sprite sheets, PNG frame ZIPs and stills.

## Build

```bash
./loopsmith/build.sh
```

`src/p1_head.html` and `src/p2_body.html` hold the markup and styles; `src/p3`–`p10` are the script, concatenated in order inside one IIFE. The output is `loopsmith/index.html`, a single self-contained page.
