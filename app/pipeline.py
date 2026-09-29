"""The render pipeline: script/voice -> lip-sync -> restore -> frame -> encode."""
import shutil
import time

import numpy as np

from . import captions, compose, lipsync, media, models_dl, storage, voice
from .config import FPS, TMP_DIR, load_settings

BATCH = 16


# ---- avatar preparation -----------------------------------------------------

def prepare_avatar(job, avatar_id, face_file, is_image, voice_file=None):
    from . import avatar_prep
    d = storage.avatar_dir(avatar_id)
    try:
        if voice_file:
            job.section(0.0, 0.1, "Cleaning up the voice sample")
            media.prepare_voice(voice_file, d / "voice.wav", 30, studio=True, denoise=True)
            storage.update_avatar(avatar_id, {"has_voice_sample": True})
        job.section(0.1, 1.0, "Preparing the face")
        fn = avatar_prep.prepare_from_image if is_image else avatar_prep.prepare_from_video
        info = fn(face_file, d, job.set_progress, job.set_stage)
        storage.update_avatar(avatar_id, {"status": "ready", "error": None})
        return {"avatar_id": avatar_id, **info}
    except Exception as exc:
        storage.update_avatar(avatar_id, {"status": "error", "error": str(exc)})
        raise


# ---- rendering --------------------------------------------------------------

def _ping_pong(n_base, n_out):
    if n_base == 1:
        return [0] * n_out
    cycle = list(range(n_base)) + list(range(n_base - 2, 0, -1))
    return [cycle[i % len(cycle)] for i in range(n_out)]


def _make_voice(job, avatar, params, work, max_s):
    """Produce work/voice.wav (48 kHz, mastered). Returns word timings."""
    mode = params["voice_mode"]
    script = params.get("script", "").strip()
    d = storage.avatar_dir(avatar["id"])
    sample = d / "voice.wav"
    raw = work / "voice_raw"
    words = None

    if mode == "tts":
        if not script:
            raise ValueError("Write a script first.")
        job.set_stage("Generating neural voice")
        raw = raw.with_suffix(".mp3")
        words = voice.tts(script, params.get("tts_voice") or avatar["tts_voice"], raw,
                          params.get("tts_rate", avatar.get("tts_rate", 0)),
                          params.get("tts_pitch", avatar.get("tts_pitch", 0)))
    elif mode == "clone":
        if not script:
            raise ValueError("Write a script first.")
        if not sample.exists():
            raise ValueError("This avatar has no voice sample. Add one in the avatar editor.")
        job.set_stage("Cloning voice (offline, this is the slow part)")
        raw = raw.with_suffix(".wav")
        voice.clone_tts(script, sample, raw, params.get("clone_language")
                        or avatar.get("clone_language", "en"))
    elif mode == "upload":
        src = params.get("audio_file")
        if not src:
            raise ValueError("Upload or record your voice first.")
        raw = src
    else:
        raise ValueError(f"Unknown voice mode {mode}")

    if params.get("convert_voice") and mode != "clone":
        if not sample.exists():
            raise ValueError("'Make it sound like my avatar' needs a voice sample on the avatar.")
        job.set_stage("Converting to the avatar's voice")
        media.prepare_voice(raw, work / "vc_in.wav", max_s, studio=False, trim_start=mode != "tts")
        voice.convert_voice(work / "vc_in.wav", sample, work / "vc_out.wav")
        raw = work / "vc_out.wav"

    job.set_stage("Mastering audio")
    media.prepare_voice(raw, work / "voice.wav", max_s, studio=params.get("studio_audio", True),
                        denoise=mode == "upload", trim_start=mode != "tts")
    return words


def render(job, params):
    t0 = time.time()
    settings = load_settings()
    max_s = float(settings["max_video_seconds"])
    avatar = storage.get_avatar(params["avatar_id"])
    if not avatar or avatar.get("status") != "ready":
        raise ValueError("Avatar is not ready yet.")
    quality = params.get("quality", "studio")
    use_restore = quality == "studio" and models_dl.path_if_ready("gfpgan") is not None

    work = TMP_DIR / job.id
    work.mkdir(parents=True, exist_ok=True)
    try:
        # 1. voice
        job.section(0.0, 0.08, "Preparing voice")
        words = _make_voice(job, avatar, params, work, max_s)
        wav16 = media.load_audio_16k(work / "voice.wav")
        duration = len(wav16) / 16000.0
        if duration < 0.5:
            raise ValueError("The voice audio is empty or too short.")
        if words is None and params.get("script", "").strip():
            words = voice.estimate_word_timings(params["script"], wav16)
        words = [w for w in (words or []) if w["start"] < duration - 0.1]

        # 2. audio features
        job.section(0.08, 0.10, "Analysing speech")
        mel = lipsync.melspectrogram(wav16)
        chunks = lipsync.mel_chunks(mel, FPS)
        n_out = len(chunks)

        # 3. base clip
        job.set_stage("Loading avatar")
        d = storage.avatar_dir(avatar["id"])
        base = media.read_frames(d / "base.mp4")
        faces = np.load(d / "faces.npz")
        boxes, lms = faces["boxes"], faces["landmarks"]
        n_base = min(len(base), len(boxes))
        order = _ping_pong(n_base, n_out)
        bh, bw = base[0].shape[:2]

        # 4. framing + captions
        out_w, out_h = compose.output_size(params.get("aspect", "9:16"), bw, bh)
        centers = np.array([[(boxes[i][0] + boxes[i][2]) / 2, (boxes[i][1] + boxes[i][3]) / 2]
                            for i in set(order)])
        window = compose.crop_window(bw, bh, out_w, out_h, np.median(centers, axis=0))
        style = params.get("caption_style", "pop")
        subs = None
        if style != "none" and words:
            if media.can_burn_subtitles():
                subs = captions.build(words, style, out_w, out_h, work, duration)
            else:
                job.set_stage("Captions skipped: this FFmpeg build cannot burn subtitles")

        # 5. lip-sync + composite + restore, streamed straight into the encoder
        job.section(0.10, 0.97, "Lip-syncing" + (" + restoring face detail" if use_restore else ""))
        model = lipsync.Wav2Lip(settings["cpu_threads"])
        restorer = None
        if use_restore:
            from .enhance import FaceRestorer
            restorer = FaceRestorer(settings["cpu_threads"])
        video_id, vdir = storage.new_video_dir()
        writer = media.VideoWriter(vdir / "video.mp4", (out_w, out_h), FPS, work / "voice.wav",
                                   work, subtitles=subs, finish=params.get("film_finish", True))
        ok = False
        try:
            for b0 in range(0, n_out, BATCH):
                idx = order[b0:b0 + BATCH]
                crop_boxes = [compose.wav2lip_box(boxes[i], base[i].shape) for i in idx]
                crops = np.stack([compose.face_crop(base[i], cb) for i, cb in zip(idx, crop_boxes)])
                mels = np.stack(chunks[b0:b0 + BATCH])
                preds = model(mels, crops)
                for k, i in enumerate(idx):
                    frame = base[i].copy()
                    pred = compose.colour_corrected(preds[k], crops[k])
                    compose.paste_mouth(frame, crop_boxes[k], pred, lms[i])
                    if restorer is not None:
                        region = compose.full_frame_mask(frame.shape, crop_boxes[k], lms[i], 1.12)
                        frame = restorer.restore(frame, lms[i], region, strength=0.85)
                    writer.write(compose.frame_output(frame, window, (out_w, out_h)))
                job.set_progress(min(1.0, (b0 + len(idx)) / n_out))
            ok = True
        finally:
            try:
                writer.close()
            except RuntimeError:
                # An encoder failure explains a broken pipe better than the pipe error.
                storage.delete_video(video_id)
                raise
            if not ok:
                storage.delete_video(video_id)

        # 6. library entry
        job.section(0.97, 1.0, "Saving")
        mid = base[order[len(order) // 2]]
        media.imwrite(vdir / "thumb.jpg",
                      compose.frame_output(mid, window, (out_w, out_h)), quality=85)
        meta = {
            "id": video_id, "avatar_id": avatar["id"], "avatar_name": avatar["name"],
            "script": params.get("script", ""), "duration": round(duration, 2),
            "width": out_w, "height": out_h, "aspect": params.get("aspect", "9:16"),
            "quality": "studio" if use_restore else "fast", "voice_mode": params["voice_mode"],
            "caption_style": style if subs else "none", "created": time.time(),
            "render_seconds": round(time.time() - t0, 1),
        }
        storage.save_video_meta(video_id, meta)
        return meta
    finally:
        shutil.rmtree(work, ignore_errors=True)


def estimate_seconds(duration, studio):
    """Rough render-time estimate for a 4-core desktop CPU (i7-4790 class)."""
    frames = duration * FPS
    per_frame = 0.06 + (1.3 if studio else 0.0)
    return 20 + frames * per_frame
