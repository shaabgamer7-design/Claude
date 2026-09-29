"""Chatterbox voice cloning worker. Runs inside the separate `venv-voice`
environment created by install_voice_clone, called by app/voice.py.

  python voice_worker.py tts --text "Hi" --ref sample.wav --out out.wav [--lang en]
  python voice_worker.py vc  --src in.wav --ref sample.wav --out out.wav
  python voice_worker.py download        (fetch the model weights once)
"""
import argparse
import os

import numpy as np
import soundfile as sf
import torch

# Checkpoints may have been saved on GPU; always load them onto the CPU.
_torch_load = torch.load


def _cpu_load(*args, **kwargs):
    kwargs.setdefault("map_location", torch.device("cpu"))
    return _torch_load(*args, **kwargs)


torch.load = _cpu_load
torch.set_num_threads(os.cpu_count() or 4)


def _save(wav, sr, path):
    data = wav.detach().cpu().numpy() if hasattr(wav, "detach") else np.asarray(wav)
    sf.write(path, np.squeeze(data).astype(np.float32), sr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["tts", "vc", "download"])
    ap.add_argument("--text")
    ap.add_argument("--src")
    ap.add_argument("--ref")
    ap.add_argument("--out")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--exaggeration", type=float, default=0.5)
    a = ap.parse_args()

    if a.mode == "download":
        from chatterbox.tts import ChatterboxTTS
        from chatterbox.vc import ChatterboxVC
        ChatterboxVC.from_pretrained("cpu")
        ChatterboxTTS.from_pretrained(device="cpu")
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        except ImportError:
            print("Multilingual model not available in this chatterbox version.")
        print("Voice models ready.")
        return
    if not a.ref or not a.out:
        ap.error("--ref and --out are required")

    if a.mode == "vc":
        from chatterbox.vc import ChatterboxVC
        model = ChatterboxVC.from_pretrained("cpu")
        wav = model.generate(audio=a.src, target_voice_path=a.ref)
        _save(wav, model.sr, a.out)
        return

    if a.lang == "en":
        from chatterbox.tts import ChatterboxTTS
        model = ChatterboxTTS.from_pretrained(device="cpu")
        wav = model.generate(a.text, audio_prompt_path=a.ref, exaggeration=a.exaggeration,
                             cfg_weight=0.5)
    else:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        wav = model.generate(a.text, language_id=a.lang, audio_prompt_path=a.ref,
                             exaggeration=a.exaggeration, cfg_weight=0.5)
    _save(wav, model.sr, a.out)


if __name__ == "__main__":
    main()
