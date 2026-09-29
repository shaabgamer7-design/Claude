"""Wav2Lip inference on ONNX Runtime (CPU), plus the audio features it needs.

The mel-spectrogram reproduces the original Wav2Lip `audio.py` / `hparams.py`
exactly, because the model was trained on those features.
"""
import os

import numpy as np

from . import models_dl

SAMPLE_RATE = 16000
N_FFT = 800
HOP = 200
WIN = 800
N_MELS = 80
FMIN = 55
FMAX = 7600
PREEMPH = 0.97
MIN_LEVEL_DB = -100
REF_LEVEL_DB = 20
MAX_ABS = 4.0
MEL_STEP = 16
IMG_SIZE = 96

_mel_basis = None


def melspectrogram(wav: np.ndarray) -> np.ndarray:
    import librosa
    from scipy import signal

    global _mel_basis
    wav = signal.lfilter([1, -PREEMPH], [1], wav)
    stft = librosa.stft(y=wav, n_fft=N_FFT, hop_length=HOP, win_length=WIN,
                        pad_mode="reflect")
    if _mel_basis is None:
        _mel_basis = librosa.filters.mel(sr=SAMPLE_RATE, n_fft=N_FFT, n_mels=N_MELS,
                                         fmin=FMIN, fmax=FMAX)
    mel = np.dot(_mel_basis, np.abs(stft))
    min_level = np.exp(MIN_LEVEL_DB / 20 * np.log(10))
    s = 20 * np.log10(np.maximum(min_level, mel)) - REF_LEVEL_DB
    s = (2 * MAX_ABS) * ((s - MIN_LEVEL_DB) / (-MIN_LEVEL_DB)) - MAX_ABS
    return np.clip(s, -MAX_ABS, MAX_ABS).astype(np.float32)


def mel_chunks(mel: np.ndarray, fps: int):
    """One 80x16 mel window per video frame, as in Wav2Lip inference."""
    chunks = []
    step = 80.0 / fps
    i = 0
    while True:
        start = int(i * step)
        if start + MEL_STEP > mel.shape[1]:
            chunks.append(mel[:, -MEL_STEP:])
            break
        chunks.append(mel[:, start:start + MEL_STEP])
        i += 1
    return chunks


def session_options(threads: int = 0):
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = threads or (os.cpu_count() or 4)
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return opts


class Wav2Lip:
    def __init__(self, threads: int = 0):
        import onnxruntime as ort
        path = models_dl.path_if_ready("wav2lip")
        if not path:
            raise RuntimeError("Lip-sync model missing. Open Settings and click "
                               "'Download models'.")
        self.sess = ort.InferenceSession(str(path), session_options(threads),
                                         providers=["CPUExecutionProvider"])
        # Identify the inputs by shape: the face input has 6 channels.
        self.face_input = self.audio_input = None
        for inp in self.sess.get_inputs():
            if len(inp.shape) == 4 and inp.shape[1] == 6:
                self.face_input = inp.name
            else:
                self.audio_input = inp.name
        if self.face_input is None or self.audio_input is None:
            names = [i.name for i in self.sess.get_inputs()]
            self.audio_input, self.face_input = names[0], names[1]
        shape = self.sess.get_inputs()[0].shape
        self.batch = None if isinstance(shape[0], str) or shape[0] is None else int(shape[0])

    def __call__(self, mels: np.ndarray, faces: np.ndarray) -> np.ndarray:
        """mels: (B,80,16). faces: (B,96,96,3) uint8 BGR. Returns (B,96,96,3) float BGR 0-255."""
        masked = faces.copy()
        masked[:, IMG_SIZE // 2:] = 0
        face_in = np.concatenate([masked, faces], axis=3).astype(np.float32) / 255.0
        face_in = face_in.transpose(0, 3, 1, 2)
        mel_in = mels[:, None].astype(np.float32)
        if self.batch == 1:  # fixed-batch export: run one at a time
            outs = [self.sess.run(None, {self.audio_input: mel_in[i:i + 1],
                                         self.face_input: face_in[i:i + 1]})[0]
                    for i in range(len(faces))]
            out = np.concatenate(outs, axis=0)
        else:
            out = self.sess.run(None, {self.audio_input: mel_in, self.face_input: face_in})[0]
        return np.clip(out.transpose(0, 2, 3, 1) * 255.0, 0, 255)
