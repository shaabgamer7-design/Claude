"""Face detection and tracking.

Primary detector is OpenCV's YuNet (fast on CPU, gives 5 landmarks). If its
model file is missing we fall back to the Haar cascade that ships inside
OpenCV and estimate the landmarks from the box.

Per-frame results are interpolated over missed frames and smoothed over time,
so the pasted mouth and the restored face never jitter.
"""
import cv2
import numpy as np

from . import models_dl

# Landmark order: image-left eye, image-right eye, nose tip,
# image-left mouth corner, image-right mouth corner.
_BOX_TO_LANDMARKS = np.array([[0.31, 0.40], [0.69, 0.40], [0.50, 0.58],
                              [0.35, 0.76], [0.65, 0.76]], np.float32)


class FaceDetector:
    def __init__(self):
        path = models_dl.path_if_ready("yunet")
        self.yunet = None
        if path:
            try:
                # Loading from memory avoids OpenCV's trouble with non-ASCII paths on Windows.
                buf = np.fromfile(str(path), np.uint8)
                self.yunet = cv2.FaceDetectorYN.create("onnx", buf, np.array([], np.uint8),
                                                       (320, 320), 0.6, 0.3, 50)
            except (cv2.error, TypeError):
                self.yunet = cv2.FaceDetectorYN.create(str(path), "", (320, 320), 0.6, 0.3, 50)
        self.haar = None
        if self.yunet is None:
            if not hasattr(cv2, "CascadeClassifier"):
                raise RuntimeError("Face detector model missing: open Settings and download "
                                   "the models.")
            self.haar = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    @property
    def name(self):
        return "YuNet" if self.yunet is not None else "Haar cascade"

    def detect(self, frame, prev_center=None):
        """Return (box[x1,y1,x2,y2], landmarks[5,2]) for the main face, or None."""
        h, w = frame.shape[:2]
        faces = []
        if self.yunet is not None:
            # Detect on a <=640px copy for speed, scale results back.
            scale = min(1.0, 640.0 / max(h, w))
            small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1 else frame
            self.yunet.setInputSize((small.shape[1], small.shape[0]))
            _, dets = self.yunet.detect(small)
            if dets is not None:
                for d in dets:
                    x, y, bw, bh = d[:4] / scale
                    lm = d[4:14].reshape(5, 2) / scale
                    faces.append((np.array([x, y, x + bw, y + bh], np.float32),
                                  lm.astype(np.float32)))
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            min_size = max(40, min(h, w) // 10)
            rects = self.haar.detectMultiScale(gray, 1.1, 5, minSize=(min_size, min_size))
            for (x, y, bw, bh) in rects:
                # Haar boxes sit high on the face; shift down to cover the chin.
                y2 = y + bh * 1.12
                box = np.array([x, y + bh * 0.05, x + bw, y2], np.float32)
                faces.append((box, landmarks_from_box(box)))
        if not faces:
            return None
        if prev_center is not None:
            return min(faces, key=lambda f: np.hypot(*(box_center(f[0]) - prev_center)))
        return max(faces, key=lambda f: (f[0][2] - f[0][0]) * (f[0][3] - f[0][1]))


def landmarks_from_box(box):
    x1, y1, x2, y2 = box
    return (_BOX_TO_LANDMARKS * [x2 - x1, y2 - y1] + [x1, y1]).astype(np.float32)


def box_center(box):
    return np.array([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2], np.float32)


def _interpolate(values, valid):
    """Fill rows where valid is False by linear interpolation along axis 0."""
    idx = np.arange(len(values))
    good = idx[valid]
    flat = values.reshape(len(values), -1)
    for c in range(flat.shape[1]):
        flat[:, c] = np.interp(idx, good, flat[good, c])
    return flat.reshape(values.shape)


def _smooth(values, window):
    if len(values) < 3 or window < 2:
        return values
    pad = window // 2
    flat = values.reshape(len(values), -1)
    padded = np.pad(flat, ((pad, pad), (0, 0)), mode="edge")
    kernel = np.hanning(window + 2)[1:-1]
    kernel /= kernel.sum()
    out = np.stack([np.convolve(padded[:, c], kernel, mode="valid")
                    for c in range(flat.shape[1])], axis=1)
    return out[:len(values)].reshape(values.shape).astype(np.float32)


def track(frames, progress=None):
    """Detect the face in every frame. Returns (boxes[N,4], landmarks[N,5,2])."""
    det = FaceDetector()
    n = len(frames)
    boxes = np.zeros((n, 4), np.float32)
    lms = np.zeros((n, 5, 2), np.float32)
    valid = np.zeros(n, bool)
    prev = None
    for i, frame in enumerate(frames):
        found = det.detect(frame, prev)
        if found is not None:
            boxes[i], lms[i] = found
            valid[i] = True
            prev = box_center(found[0])
        if progress and i % 10 == 0:
            progress(i / max(n, 1))
    if not valid.any():
        raise ValueError("No face found. Use a clear, front-facing, well-lit face.")
    if valid.mean() < 0.5:
        raise ValueError("The face was only found in {:.0%} of frames. Use a clip where "
                         "the face stays visible and faces the camera.".format(valid.mean()))
    boxes = _interpolate(boxes, valid)
    lms = _interpolate(lms, valid)
    # Haar is noisier than YuNet, so it gets a wider smoothing window.
    window = 5 if det.yunet is not None else 9
    return _smooth(boxes, window), _smooth(lms, window), det.name
