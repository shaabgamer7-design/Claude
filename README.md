# Avatar Studio

Your own talking-avatar video generator, like HeyGen, but **free, unlimited and running on your own PC**.
No GPU, no subscription, no paid API.

- **Unlimited avatars.** Each one is a face (your selfie video or any portrait / AI photo), a voice and a
  personality (tone, niche, audience, catchphrases, call to action).
- **Lip-synced 720p videos** in 9:16 (Reels / Shorts / TikTok), 4:5, 1:1 or 16:9, up to 15 s by default
  (configurable up to 60 s).
- **Voices:** free Microsoft neural voices (English, **Urdu**, Hindi, Arabic and 100+ more), your own
  recording, or offline **voice cloning** (optional add-on).
- **Scripts in the avatar's voice:** offline with a local AI (Ollama), or one click to copy a
  ready-made prompt for Claude.
- **Reels-style captions** with word-by-word highlight, Urdu/Arabic included.
- Built for an **Intel i7-4790 + 16 GB RAM, CPU only**: a 15 s Studio-quality video renders in roughly
  8-12 minutes, Fast mode in about 1 minute.

## How the output is made to look good

A basic lip-sync tool pastes a blurry 96x96 mouth over the face. Avatar Studio does more:

| Step | What it does |
|---|---|
| Base clip | Your face video (or an animated photo with natural breathing / sway) is prepared **once** and reused, so every video has real, natural motion. |
| Stable tracking | The face is detected in every frame, gaps are interpolated and the track is smoothed, so nothing jitters. |
| Wav2Lip-GAN | Generates mouth movement from the audio. |
| Mouth-only compositing | Only nose-to-chin is replaced, through a feathered, head-tilt-aware mask. Eyes, skin texture and hair stay 100% original. |
| Colour match | The model's colour drift is measured on the untouched half of the face and removed, so there's no visible patch. |
| GFPGAN 1.4 restoration | Re-creates sharp lips, teeth and skin detail at 512 px ("Studio" quality). |
| Studio audio | High-pass, denoise (recordings), compression and -14 LUFS loudness, the level Instagram, TikTok and YouTube expect. |
| Film finish | Light sharpening and fine temporal grain make the restored mouth blend with the camera footage and hide the "AI look". |
| Encoding | x264 High profile, CRF 17, `+faststart`, AAC 192k: uploads cleanly to every platform. |

## Install (Windows)

1. Install **Python 3.11** from <https://www.python.org/downloads/>. In the installer, tick
   **"Add python.exe to PATH"**.
2. Download this project (green **Code** button, then **Download ZIP**) and unzip it to a simple
   path such as `C:\AvatarStudio`.
3. Double-click **`setup_windows.bat`**. It installs everything (about 250 MB) and downloads the AI
   models (about 480 MB). Do this once.
4. Double-click **`start_windows.bat`**. Your browser opens <http://127.0.0.1:7860>.

Linux/macOS: `./setup.sh`, then `./start.sh`.

### Optional add-ons

| Add-on | What you get | How |
|---|---|---|
| Voice cloning | The avatar speaks any script in **your** voice, fully offline. It also enables "make it sound like my avatar" voice conversion on top of neural voices or recordings. | Double-click `install_voice_clone_windows.bat` (about 5 GB; uses Chatterbox, MIT licence). Slow on CPU: 1-3 min per 15 s. |
| Local AI scriptwriter | "Write with local AI" writes the script in the avatar's persona, offline. | Install [Ollama](https://ollama.com), then run `ollama pull qwen2.5:3b` in a terminal. |

## Using it

1. **Avatars, then New avatar:** drop a 10-20 s selfie video (best) or a portrait photo, add a voice
   sample if you'll use cloning, and fill in the persona.
2. **Create video:**
   1. Pick the avatar.
   2. Write the script, or generate it (about 35 words = 15 s).
   3. Pick the voice.
   4. Pick format, captions and quality.
   5. Click **Render**.
3. The finished MP4 plays right there. Every video is also kept in the **Library**.

### Tips for the best results

- **Face video:** face the camera with even light on your face. Keep your mouth mostly closed or talk
  softly, with small natural head movements, and no hands in front of the face. Record in the
  format you'll post (vertical for Reels).
- **Photo:** sharp, front-facing, mouth closed, face at least 300 px tall. AI portraits work well.
- **Voice sample:** 15-30 s of clean speech in a quiet room.
- **Urdu:** use the Urdu neural voices (Asad / Uzma), or record yourself with "My recording".
  Captions render Urdu script correctly.

## Honest limits

- The CPU-friendly lip-sync (Wav2Lip) is very good for talking-head content, but less refined than
  HeyGen on fast head turns or extreme angles. A calm, front-facing base clip gives the best results.
- Neural voices (edge-tts) are free but use Microsoft's online service, so they need internet while
  generating. Everything else works offline.
- Photo avatars get subtle, natural idle motion (breathing, sway), not full head movement or blinks.
  For that, use a video.

## Licences: please read

| Component | Licence | Commercial use |
|---|---|---|
| Avatar Studio code | Yours | Yes |
| **Wav2Lip** (lip-sync weights) | Research / **non-commercial** | Personal and non-commercial content only. For paid or brand work, contact the Wav2Lip authors (Sync Labs) or switch to a commercially licensed lip-sync model. |
| GFPGAN 1.4 | Apache 2.0 | Yes |
| YuNet (OpenCV Zoo) | MIT | Yes |
| Chatterbox | MIT | Yes |
| edge-tts voices | Microsoft service terms | Check Microsoft's terms for your use |

Use it responsibly. Only clone faces and voices you have the right to use (your own, or with written
consent). Label AI-generated content where the platform requires it (YouTube, Meta and TikTok all do).

## Manual model download

If `setup_windows.bat` can't download a model, download it in your browser and put it in the
`models\` folder with exactly this name:

| File name in `models\` | Download from (any one) |
|---|---|
| `wav2lip_gan.onnx` | `https://huggingface.co/facefusion/models-3.0.0/resolve/main/wav2lip_gan_96.onnx` |
| `gfpgan_1.4.onnx` | `https://huggingface.co/facefusion/models-3.0.0/resolve/main/gfpgan_1.4.onnx` |
| `face_detection_yunet_2023mar.onnx` | `https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx` |

`app/models_dl.py` lists extra mirrors. If you have the original PyTorch `wav2lip_gan.pth`, convert it
with `python tools/wav2lip_to_onnx.py wav2lip_gan.pth models/wav2lip_gan.onnx` (needs PyTorch).

## Troubleshooting

- **"No face found":** use a brighter, front-facing clip where the face fills at least a quarter of the
  frame.
- **Setup fails on `onnxruntime`:** install the Microsoft Visual C++ Redistributable (x64) from
  Microsoft's site, then run setup again.
- **Nothing opens in the browser:** go to <http://127.0.0.1:7860> yourself while the black
  `start_windows.bat` window is open.
- **Rendering is slow:** use **Fast** quality for drafts, and close other heavy apps. Settings has a
  CPU threads option.
- **Different port:** `start_windows.bat --port 8080`.

## Upgrading later

With an NVIDIA GPU (for example an RTX 3060 12 GB), the same app can move to higher-end models such as
LatentSync or MuseTalk for lip-sync, and LivePortrait for full head motion on photo avatars. The
pipeline is modular (`app/lipsync.py`, `app/enhance.py`), so they can be added as new quality modes.

## Project layout

```
app/
  main.py          web server + API          pipeline.py    render pipeline
  avatar_prep.py   face video/photo -> base  compose.py     mouth mask, colour match, framing
  lipsync.py       Wav2Lip (ONNX) + mel      enhance.py     GFPGAN restoration
  face.py          detection + tracking      voice.py       neural TTS, cloning, timings
  captions.py      Reels-style captions      script_writer.py persona prompts, Ollama
  static/          the web UI (no build step)
tools/             voice-cloning worker, Wav2Lip .pth -> ONNX converter
tests/             offline end-to-end test with stand-in models
data/              your avatars and videos (created on first run)
models/            downloaded AI models
```

Run the offline test:

```
python tests/make_test_models.py /tmp/as-models      # needs PyTorch + onnx
AVATAR_STUDIO_MODELS=/tmp/as-models AVATAR_STUDIO_DATA=/tmp/as-data python tests/test_e2e.py
```
