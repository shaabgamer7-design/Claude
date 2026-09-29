"""Turns an uploaded face (video or photo) into a reusable "base clip".

The base clip is the avatar's body: every new video reuses its motion and only
the mouth is re-generated. It is prepared once, so renders stay fast.
"""
import json
import math

import cv2
import numpy as np

from . import face, media, models_dl
from .config import BASE_MAX_SECONDS, BASE_SHORT_SIDE, FPS

IMAGE_CLIP_SECONDS = 10


def _resize_short_side(img, short):
    h, w = img.shape[:2]
    s = short / min(h, w)
    size = (int(round(w * s)) // 2 * 2, int(round(h * s)) // 2 * 2)
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4
    return cv2.resize(img, size, interpolation=interp)


def _face_ellipse_mask(shape, box):
    h, w = shape[:2]
    x1, y1, x2, y2 = box
    mask = np.zeros((h, w), np.float32)
    center = (float((x1 + x2) / 2), float((y1 + y2) / 2))
    axes = (float((x2 - x1) * 0.95), float((y2 - y1) * 1.1))
    cv2.ellipse(mask, (center, axes, 0.0), 1.0, -1)
    return cv2.GaussianBlur(mask, (0, 0), max(2.0, (x2 - x1) * 0.06))


def _motion(t):
    """Subtle, natural idle motion: breathing, slow sway and drift."""
    breathe = math.sin(2 * math.pi * t / 4.2)
    return {
        "scale": 1.06 + 0.006 * breathe + 0.004 * math.sin(2 * math.pi * t / 9.7),
        "angle": 0.55 * math.sin(2 * math.pi * t / 7.3) + 0.22 * math.sin(2 * math.pi * t / 3.1 + 1.0),
        "dx": 0.0035 * math.sin(2 * math.pi * t / 8.9 + 0.5),
        "dy": 0.0025 * breathe,
    }


def _transform_points(points, matrix):
    pts = np.hstack([points, np.ones((len(points), 1), np.float32)])
    return (pts @ matrix.T).astype(np.float32)


def prepare_from_image(src, out_dir, progress=None, stage=None):
    stage and stage("Reading photo")
    img = media.imread(src)
    img = _resize_short_side(img, BASE_SHORT_SIDE)
    h, w = img.shape[:2]
    det = face.FaceDetector()
    found = det.detect(img)
    if found is None:
        raise ValueError("No face found in the photo. Use a clear, front-facing portrait.")
    box, lms = found

    if models_dl.path_if_ready("gfpgan"):
        stage and stage("Sharpening the face (one-time)")
        from .enhance import FaceRestorer
        img = FaceRestorer().restore(img, lms, _face_ellipse_mask(img.shape, box), strength=0.7)

    stage and stage("Animating idle motion")
    n = IMAGE_CLIP_SECONDS * FPS
    pivot = (float((box[0] + box[2]) / 2), float(box[3] + (box[3] - box[1]) * 0.6))
    corners = np.array([[box[0], box[1]], [box[2], box[1]],
                        [box[0], box[3]], [box[2], box[3]]], np.float32)
    frames, boxes, landmarks = [], [], []
    for i in range(n):
        m = _motion(i / FPS)
        matrix = cv2.getRotationMatrix2D(pivot, m["angle"], m["scale"])
        matrix[0, 2] += m["dx"] * w
        matrix[1, 2] += m["dy"] * h
        frames.append(cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LANCZOS4,
                                     borderMode=cv2.BORDER_REFLECT))
        c = _transform_points(corners, matrix)
        boxes.append([c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max()])
        landmarks.append(_transform_points(lms, matrix))
        if progress and i % 25 == 0:
            progress(i / n)
    stage and stage("Saving base clip")
    media.write_frames(frames, out_dir / "base.mp4", FPS)
    return _finish(out_dir, frames, np.array(boxes, np.float32),
                   np.array(landmarks, np.float32), det.name, "image")


def prepare_from_video(src, out_dir, progress=None, stage=None):
    stage and stage("Normalising video (25 fps, 720p)")
    media.normalise_video(src, out_dir / "base.mp4", FPS, BASE_SHORT_SIDE, BASE_MAX_SECONDS)
    frames = media.read_frames(out_dir / "base.mp4")
    if len(frames) < FPS:
        raise ValueError("The video is too short. Use at least 3 seconds (10-20 s is best).")
    stage and stage("Tracking the face in every frame")
    boxes, lms, det_name = face.track(frames, progress)
    return _finish(out_dir, frames, boxes, lms, det_name, "video")


def _finish(out_dir, frames, boxes, lms, det_name, kind):
    np.savez_compressed(out_dir / "faces.npz", boxes=boxes, landmarks=lms)
    mid = len(frames) // 2
    x1, y1, x2, y2 = boxes[mid]
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = max(x2 - x1, y2 - y1) * 1.9
    h, w = frames[mid].shape[:2]
    side = min(side, w, h)
    tx = int(min(max(cx - side / 2, 0), w - side))
    ty = int(min(max(cy - side / 2 - side * 0.05, 0), h - side))
    thumb = cv2.resize(frames[mid][ty:ty + int(side), tx:tx + int(side)], (360, 360),
                       interpolation=cv2.INTER_AREA)
    media.imwrite(out_dir / "thumb.jpg", thumb)
    info = {"kind": kind, "frames": len(frames), "width": int(w), "height": int(h),
            "detector": det_name, "fps": FPS}
    (out_dir / "base.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info
