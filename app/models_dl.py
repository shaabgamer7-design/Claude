"""Model registry and downloader. Every model here is free and runs on CPU.

Run `python -m app.models_dl` to download everything. Each model lists several
mirrors that are tried in order. If all of them fail, download the file by
hand and put it in the `models/` folder under the file name shown.
"""
import sys
import urllib.request
from pathlib import Path

from .config import MODELS_DIR

MODELS = {
    "wav2lip": {
        "file": "wav2lip_gan.onnx",
        "title": "Wav2Lip-GAN lip-sync (ONNX)",
        "required": True,
        "size_mb": 140,
        "urls": [
            "https://huggingface.co/facefusion/models-3.0.0/resolve/main/wav2lip_gan_96.onnx",
            "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/wav2lip_gan_96.onnx",
            "https://github.com/facefusion/facefusion-assets/releases/download/models/wav2lip_gan.onnx",
        ],
    },
    "gfpgan": {
        "file": "gfpgan_1.4.onnx",
        "title": "GFPGAN 1.4 face restoration (Studio quality)",
        "required": False,
        "size_mb": 340,
        "urls": [
            "https://huggingface.co/facefusion/models-3.0.0/resolve/main/gfpgan_1.4.onnx",
            "https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/gfpgan_1.4.onnx",
            "https://github.com/facefusion/facefusion-assets/releases/download/models/gfpgan_1.4.onnx",
        ],
    },
    "yunet": {
        "file": "face_detection_yunet_2023mar.onnx",
        "title": "YuNet face detector",
        "required": False,
        "size_mb": 1,
        "urls": [
            "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
            "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx",
            "https://huggingface.co/facefusion/models-3.0.0/resolve/main/yunet_2023_mar.onnx",
        ],
    },
}


def model_path(key: str) -> Path:
    return MODELS_DIR / MODELS[key]["file"]


def path_if_ready(key: str):
    p = model_path(key)
    return p if p.exists() and p.stat().st_size > 10_000 else None


def status():
    return {
        key: {
            "title": spec["title"],
            "file": spec["file"],
            "required": spec["required"],
            "size_mb": spec["size_mb"],
            "ready": path_if_ready(key) is not None,
        }
        for key, spec in MODELS.items()
    }


def _validate(path: Path):
    import onnxruntime as ort
    ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def download(key: str, progress=None) -> Path:
    spec = MODELS[key]
    dst = model_path(key)
    if path_if_ready(key):
        return dst
    part = dst.with_suffix(dst.suffix + ".part")
    errors = []
    for url in spec["urls"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AvatarStudio/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(part, "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if progress and total:
                        progress(done / total)
            _validate(part)
            part.replace(dst)
            return dst
        except Exception as exc:  # try the next mirror
            errors.append(f"{url}: {exc}")
            part.unlink(missing_ok=True)
    raise RuntimeError(f"Could not download {spec['file']}. Tried:\n" + "\n".join(errors)
                       + f"\nDownload it manually into {MODELS_DIR}")


def download_all(progress=None, stage=None):
    keys = list(MODELS)
    failures = []
    for i, key in enumerate(keys):
        if stage:
            stage(f"Downloading {MODELS[key]['title']}")
        try:
            download(key, (lambda p, i=i: progress((i + p) / len(keys))) if progress else None)
        except RuntimeError as exc:
            failures.append(str(exc))
    return failures


if __name__ == "__main__":
    def _bar(p):
        sys.stdout.write(f"\r  {p:6.1%}")
        sys.stdout.flush()

    failed = []
    for k, s in MODELS.items():
        print(f"{s['title']} ({s['file']}, ~{s['size_mb']} MB)")
        try:
            download(k, _bar)
            print("\r  ready    ")
        except RuntimeError as e:
            print("\n" + str(e))
            failed.append(k)
    if any(MODELS[k]["required"] for k in failed):
        sys.exit(1)
