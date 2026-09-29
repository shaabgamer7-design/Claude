"""Compositing: where the generated mouth goes and how it is blended in.

Tricks for a clean result:
  * Only the lower face (below the nose) is replaced, through a feathered,
    head-tilt-aware ellipse. Eyes, nose, hair and background stay the original
    full-resolution pixels.
  * Wav2Lip also re-generates the upper half of the face, which we throw away,
    but it tells us the model's colour drift; we subtract that drift so the
    mouth patch matches the skin tone exactly.
"""
import cv2
import numpy as np

from .lipsync import IMG_SIZE


def wav2lip_box(box, frame_shape):
    """The crop Wav2Lip sees: the face box widened a little, padded at the chin."""
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    x1, x2 = x1 - 0.04 * bw, x2 + 0.04 * bw
    y2 = y2 + 0.10 * bh
    return (int(max(0, round(x1))), int(max(0, round(y1))),
            int(min(w, round(x2))), int(min(h, round(y2))))


def face_crop(frame, crop_box):
    x1, y1, x2, y2 = crop_box
    return cv2.resize(frame[y1:y2, x1:x2], (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)


def mouth_mask(crop_box, landmarks, scale=1.0):
    """Feathered ellipse over nose-to-chin, in crop coordinates (float32 0..1)."""
    x1, y1, x2, y2 = crop_box
    cw, ch = x2 - x1, y2 - y1
    lm = landmarks - np.array([x1, y1], np.float32)
    eye_l, eye_r, nose, m_l, m_r = lm
    mouth_c = (m_l + m_r) / 2
    top = nose[1] + 0.25 * (mouth_c[1] - nose[1])
    bottom = ch * 0.965
    half_w = max(0.34 * cw, 0.95 * abs(m_r[0] - m_l[0]))
    center = (float(mouth_c[0]), float((top + bottom) / 2))
    axes = (float(half_w * scale), float((bottom - top) / 2 * scale))
    angle = float(np.degrees(np.arctan2(eye_r[1] - eye_l[1], eye_r[0] - eye_l[0])))
    mask = np.zeros((ch, cw), np.float32)
    cv2.ellipse(mask, (center, (axes[0] * 2 * 0.86, axes[1] * 2 * 0.86), angle), 1.0, -1)
    sigma = max(2.0, 0.05 * cw)
    return cv2.GaussianBlur(mask, (0, 0), sigma)


def colour_corrected(pred, crop96):
    """Remove the model's colour cast, measured on the upper (untouched) half."""
    upper = slice(8, IMG_SIZE // 2 - 4)
    shift = (crop96[upper].astype(np.float32).mean(axis=(0, 1))
             - pred[upper].mean(axis=(0, 1)))
    return np.clip(pred + shift, 0, 255)


def paste_mouth(frame, crop_box, pred, landmarks):
    """Blend the (96x96 float) prediction into frame, in place."""
    x1, y1, x2, y2 = crop_box
    cw, ch = x2 - x1, y2 - y1
    patch = cv2.resize(pred.astype(np.float32), (cw, ch), interpolation=cv2.INTER_CUBIC)
    mask = mouth_mask(crop_box, landmarks)
    region = frame[y1:y2, x1:x2].astype(np.float32)
    a = mask[:, :, None]
    frame[y1:y2, x1:x2] = np.clip(region * (1 - a) + patch * a, 0, 255).astype(np.uint8)
    return frame


def full_frame_mask(frame_shape, crop_box, landmarks, scale):
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = crop_box
    full = np.zeros((h, w), np.float32)
    full[y1:y2, x1:x2] = mouth_mask(crop_box, landmarks, scale)
    return full


# ---- output framing ---------------------------------------------------------

ASPECTS = {
    "9:16": (720, 1280),
    "4:5": (720, 900),
    "1:1": (720, 720),
    "16:9": (1280, 720),
}


def output_size(aspect, base_w, base_h):
    if aspect in ASPECTS:
        return ASPECTS[aspect]
    return base_w - base_w % 2, base_h - base_h % 2


def crop_window(base_w, base_h, out_w, out_h, face_center):
    """A fixed crop (no camera wobble) that frames the face nicely."""
    target = out_w / out_h
    cw, ch = float(base_w), base_w / target
    if ch > base_h:
        ch, cw = float(base_h), base_h * target
    cw, ch = int(round(cw)), int(round(ch))
    # Face centred horizontally and sitting at 40% of the height: leaves the
    # lower part of the frame for captions.
    x1 = int(round(min(max(face_center[0] - cw / 2, 0), base_w - cw)))
    y1 = int(round(min(max(face_center[1] - 0.40 * ch, 0), base_h - ch)))
    return x1, y1, cw, ch


def frame_output(frame, window, out_size):
    x, y, w, h = window
    crop = frame[y:y + h, x:x + w]
    if (w, h) == tuple(out_size):
        return crop
    interp = cv2.INTER_AREA if w > out_size[0] else cv2.INTER_LANCZOS4
    return cv2.resize(crop, out_size, interpolation=interp)
