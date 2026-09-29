"""GFPGAN 1.4 face restoration on ONNX Runtime (CPU).

Wav2Lip generates the mouth at 96x96 pixels, which looks soft at 720p.
GFPGAN re-synthesises teeth, lips and skin detail at 512x512.
"""
import cv2
import numpy as np

from . import models_dl
from .lipsync import session_options

# FFHQ 5-point alignment template for a 512x512 face crop.
FFHQ_512 = np.array([[192.98138, 239.94708], [318.90277, 240.19360],
                     [256.63416, 314.01935], [201.26117, 371.41043],
                     [313.08905, 371.15118]], np.float32)
SIZE = 512


def _soft_square_mask(size, border):
    mask = np.zeros((size, size), np.float32)
    mask[border:-border, border:-border] = 1.0
    return cv2.GaussianBlur(mask, (0, 0), border / 2)


class FaceRestorer:
    def __init__(self, threads: int = 0):
        import onnxruntime as ort
        path = models_dl.path_if_ready("gfpgan")
        if not path:
            raise RuntimeError("Face restoration model missing (download it in Settings).")
        self.sess = ort.InferenceSession(str(path), session_options(threads),
                                         providers=["CPUExecutionProvider"])
        self.input = self.sess.get_inputs()[0].name
        self.crop_mask = _soft_square_mask(SIZE, 24)

    def restore_crop(self, crop_bgr: np.ndarray) -> np.ndarray:
        x = crop_bgr[:, :, ::-1].astype(np.float32) / 255.0
        x = (x - 0.5) / 0.5
        x = x.transpose(2, 0, 1)[None]
        y = self.sess.run(None, {self.input: x})[0][0]
        y = (np.clip(y, -1, 1) + 1) / 2
        return (y.transpose(1, 2, 0)[:, :, ::-1] * 255.0).clip(0, 255).astype(np.uint8)

    def restore(self, frame, landmarks, region_mask, strength=0.85):
        """Restore the face in `frame` and blend it in only where region_mask>0.

        region_mask is a float32 HxW map (0..1) in frame coordinates.
        """
        matrix, _ = cv2.estimateAffinePartial2D(landmarks, FFHQ_512, method=cv2.LMEDS)
        if matrix is None:
            return frame
        crop = cv2.warpAffine(frame, matrix, (SIZE, SIZE), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
        restored = self.restore_crop(crop)
        inverse = cv2.invertAffineTransform(matrix)
        h, w = frame.shape[:2]
        # Only warp back the bounding region of the mask, for speed.
        ys, xs = np.nonzero(region_mask > 0.01)
        if len(xs) == 0:
            return frame
        x1, x2 = max(xs.min() - 2, 0), min(xs.max() + 3, w)
        y1, y2 = max(ys.min() - 2, 0), min(ys.max() + 3, h)
        shift = np.array([[1, 0, -x1], [0, 1, -y1]], np.float32)
        inv_roi = shift @ np.vstack([inverse, [0, 0, 1]])
        size = (x2 - x1, y2 - y1)
        back = cv2.warpAffine(restored, inv_roi, size, flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
        valid = cv2.warpAffine(self.crop_mask, inv_roi, size, flags=cv2.INTER_LINEAR)
        alpha = (region_mask[y1:y2, x1:x2] * valid * strength)[:, :, None]
        out = frame.copy()
        roi = out[y1:y2, x1:x2].astype(np.float32)
        out[y1:y2, x1:x2] = (roi * (1 - alpha) + back.astype(np.float32) * alpha).astype(np.uint8)
        return out
