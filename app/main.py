"""Avatar Studio web server (FastAPI). Start it with `python -m app`."""
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.background import BackgroundTask

from . import media, models_dl, pipeline, script_writer, storage, voice
from .config import TMP_DIR, load_settings, save_settings
from .jobs import JobManager

app = FastAPI(title="Avatar Studio")
jobs = JobManager()
STATIC = Path(__file__).parent / "static"
UPLOADS = TMP_DIR / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _save_upload(upload: UploadFile, dst_dir: Path, stem: str) -> Path:
    ext = Path(upload.filename or "").suffix.lower() or ".bin"
    if len(ext) > 6 or not ext[1:].isalnum():
        ext = ".bin"
    dst = dst_dir / f"{stem}{ext}"
    with open(dst, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dst


def _avatar_or_404(avatar_id):
    try:
        a = storage.get_avatar(avatar_id)
    except ValueError:
        a = None
    if not a:
        raise HTTPException(404, "Avatar not found")
    return a


# ---- status & settings ------------------------------------------------------

@app.get("/api/status")
def status():
    try:
        ffmpeg = {"ok": True, "subtitles": media.can_burn_subtitles()}
    except RuntimeError as exc:
        ffmpeg = {"ok": False, "error": str(exc), "subtitles": False}
    return {
        "models": models_dl.status(),
        "ffmpeg": ffmpeg,
        "voice_clone": voice.clone_available(),
        "ollama": script_writer.ollama_status(),
        "settings": load_settings(),
    }


@app.post("/api/models/download")
def download_models():
    def run(job):
        failures = models_dl.download_all(job.set_progress, job.set_stage)
        if any(models_dl.MODELS[k]["required"] and not models_dl.path_if_ready(k)
               for k in models_dl.MODELS):
            raise RuntimeError("\n\n".join(failures))
        return {"failures": failures}
    return jobs.submit("download", "Downloading models", run).to_dict()


@app.post("/api/settings")
def update_settings(values: dict):
    return save_settings(values)


# ---- avatars ----------------------------------------------------------------

@app.get("/api/avatars")
def avatars():
    return storage.list_avatars()


def _persona_from_form(form: dict) -> dict:
    fields = {}
    for key, default in storage.PERSONA_FIELDS.items():
        if key in form and form[key] is not None:
            val = form[key]
            fields[key] = int(val) if isinstance(default, int) and str(val).lstrip("-").isdigit() else val
    return fields


def _start_prep(avatar_id, face_path, voice_path):
    is_image = face_path.suffix.lower() in IMAGE_EXT or not media.has_video_stream(face_path)
    if not is_image and media.probe_duration(face_path) <= 0.2:
        is_image = True
    return jobs.submit("avatar", "Preparing avatar", pipeline.prepare_avatar,
                       avatar_id, face_path, is_image, voice_path)


@app.post("/api/avatars")
async def create_avatar(face: UploadFile = File(...), voice_sample: UploadFile = File(None),
                        data: str = Form("{}")):
    import json
    fields = _persona_from_form(json.loads(data or "{}"))
    if not fields.get("name"):
        raise HTTPException(400, "Give the avatar a name.")
    avatar = storage.create_avatar(fields)
    d = storage.avatar_dir(avatar["id"])
    face_path = _save_upload(face, d, "face_source")
    voice_path = _save_upload(voice_sample, d, "voice_source") if voice_sample else None
    job = _start_prep(avatar["id"], face_path, voice_path)
    return {"avatar": avatar, "job": job.to_dict()}


@app.get("/api/avatars/{avatar_id}")
def get_avatar(avatar_id: str):
    return _avatar_or_404(avatar_id)


@app.post("/api/avatars/{avatar_id}")
async def edit_avatar(avatar_id: str, data: str = Form("{}"), face: UploadFile = File(None),
                      voice_sample: UploadFile = File(None)):
    import json
    _avatar_or_404(avatar_id)
    d = storage.avatar_dir(avatar_id)
    avatar = storage.update_avatar(avatar_id, _persona_from_form(json.loads(data or "{}")))
    job = None
    if face:
        for old in d.glob("face_source.*"):
            old.unlink()
        face_path = _save_upload(face, d, "face_source")
        voice_path = _save_upload(voice_sample, d, "voice_source") if voice_sample else None
        storage.update_avatar(avatar_id, {"status": "preparing"})
        job = _start_prep(avatar_id, face_path, voice_path)
    elif voice_sample:
        voice_path = _save_upload(voice_sample, d, "voice_source")

        def run(job):
            job.set_stage("Cleaning up the voice sample")
            media.prepare_voice(voice_path, d / "voice.wav", 30, studio=True, denoise=True)
            storage.update_avatar(avatar_id, {"has_voice_sample": True})
            return {"avatar_id": avatar_id}
        job = jobs.submit("voice", "Saving voice sample", run)
    return {"avatar": avatar, "job": job.to_dict() if job else None}


@app.delete("/api/avatars/{avatar_id}")
def delete_avatar(avatar_id: str):
    _avatar_or_404(avatar_id)
    storage.delete_avatar(avatar_id)
    return {"ok": True}


@app.get("/api/avatars/{avatar_id}/{asset}")
def avatar_asset(avatar_id: str, asset: str):
    files = {"thumb": "thumb.jpg", "voice": "voice.wav", "base": "base.mp4"}
    if asset not in files:
        raise HTTPException(404)
    path = storage.avatar_dir(avatar_id) / files[asset]
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


# ---- voices & scripts -------------------------------------------------------

@app.get("/api/voices")
def voices():
    return voice.list_tts_voices()


class PreviewReq(BaseModel):
    text: str
    voice: str
    rate: int = 0
    pitch: int = 0


@app.post("/api/voices/preview")
def preview_voice(req: PreviewReq):
    out = UPLOADS / f"preview-{uuid.uuid4().hex[:8]}.mp3"
    try:
        voice.tts(req.text[:300], req.voice, out, req.rate, req.pitch)
    except RuntimeError as exc:
        out.unlink(missing_ok=True)
        raise HTTPException(502, str(exc))
    return FileResponse(out, media_type="audio/mpeg",
                        background=BackgroundTask(out.unlink, missing_ok=True))


class ScriptReq(BaseModel):
    avatar_id: str
    topic: str
    seconds: float = 15
    hook_style: str = "question"


@app.post("/api/script/prompt")
def script_prompt(req: ScriptReq):
    a = _avatar_or_404(req.avatar_id)
    return {"prompt": script_writer.build_prompt(a, req.topic, req.seconds, req.hook_style)}


@app.post("/api/script/generate")
def script_generate(req: ScriptReq):
    a = _avatar_or_404(req.avatar_id)
    try:
        return {"script": script_writer.write_with_ollama(a, req.topic, req.seconds, req.hook_style)}
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))


# ---- rendering --------------------------------------------------------------

@app.post("/api/render")
async def render(data: str = Form(...), audio: UploadFile = File(None)):
    import json
    params = json.loads(data)
    a = _avatar_or_404(params.get("avatar_id", ""))
    if a.get("status") != "ready":
        raise HTTPException(400, "This avatar is still being prepared.")
    upload = _save_upload(audio, UPLOADS, uuid.uuid4().hex) if audio else None
    if upload:
        params["audio_file"] = str(upload)

    def run(job):
        try:
            return pipeline.render(job, params)
        finally:
            if upload:
                upload.unlink(missing_ok=True)

    title = f"{a['name']}: " + (params.get("script", "")[:40] or "voice upload")
    return jobs.submit("render", title, run).to_dict()


@app.get("/api/estimate")
def estimate(seconds: float = 15, quality: str = "studio"):
    studio = quality == "studio" and models_dl.path_if_ready("gfpgan") is not None
    return {"seconds": pipeline.estimate_seconds(seconds, studio)}


@app.get("/api/jobs")
def list_jobs():
    return jobs.recent()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404)
    return job.to_dict()


# ---- library ----------------------------------------------------------------

@app.get("/api/videos")
def videos():
    return storage.list_videos()


@app.delete("/api/videos/{video_id}")
def delete_video(video_id: str):
    storage.delete_video(video_id)
    return {"ok": True}


@app.get("/media/videos/{video_id}/{name}")
def video_file(video_id: str, name: str, download: int = 0):
    if name not in ("video.mp4", "thumb.jpg"):
        raise HTTPException(404)
    path = storage.video_dir(video_id) / name
    if not path.exists():
        raise HTTPException(404)
    if download:
        return FileResponse(path, filename=f"avatar-{video_id}.mp4")
    return FileResponse(path)


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
