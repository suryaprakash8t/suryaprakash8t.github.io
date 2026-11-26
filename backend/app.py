from pathlib import Path
from datetime import datetime, timezone
from threading import Lock
import os
import uuid
import subprocess
import shutil

import psutil
import torch
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import runtime

BASE = Path("/kaggle/working/AI_Video_Studio")
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
UPLOADS.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("AI_STUDIO_API_KEY", "")
jobs = {}
jobs_lock = Lock()
generation_lock = Lock()

app = FastAPI(title="AI Video Studio API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_key(x_api_key: str = Header(default="")):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key.")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "model_loaded": runtime.PIPELINE is not None,
    }


@app.get("/api/models")
def models():
    return [
        {
            "id": "svd_xt",
            "name": "Stable Video Diffusion XT",
            "status": "ready",
            "prompt_supported": False,
            "note": "Image-conditioned; SVD-XT does not use text prompts.",
        },
        {
            "id": "cogvideox_5b_i2v",
            "name": "CogVideoX-5B-I2V",
            "status": "planned",
            "prompt_supported": True,
            "note": "Not enabled in this build.",
        },
        {
            "id": "wan21_i2v_14b",
            "name": "Wan 2.1 I2V",
            "status": "planned",
            "prompt_supported": True,
            "note": "Not enabled in this build.",
        },
        {
            "id": "ltx_video_i2v",
            "name": "LTX-Video I2V",
            "status": "planned",
            "prompt_supported": True,
            "note": "Not enabled in this build.",
        },
    ]


@app.get("/api/system")
def system():
    vm = psutil.virtual_memory()
    data = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.15),
        "ram_total_gb": round(vm.total / 1024**3, 2),
        "ram_used_gb": round((vm.total - vm.available) / 1024**3, 2),
        "ram_available_gb": round(vm.available / 1024**3, 2),
        "disk_free_gb": round(shutil.disk_usage(str(BASE)).free / 1024**3, 2),
        "gpus": [],
    }
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            data["gpus"].append(
                {
                    "name": p.name,
                    "vram_total_gb": round(p.total_memory / 1024**3, 2),
                    "vram_allocated_gb": round(torch.cuda.memory_allocated(i) / 1024**3, 2),
                    "vram_reserved_gb": round(torch.cuda.memory_reserved(i) / 1024**3, 2),
                }
            )
    return data


def run_generation(job_id, image_path, steps, motion, seed):
    with jobs_lock:
        jobs[job_id]["status"] = "queued"
        jobs[job_id]["message"] = "Waiting for GPU"

    # One SVD-XT generation at a time; two concurrent full jobs can exhaust T4 memory.
    with generation_lock:
        with jobs_lock:
            jobs[job_id]["status"] = "running"
            jobs[job_id]["message"] = "Generating with SVD-XT"
        try:
            out = OUTPUTS / f"{job_id}.mp4"

            def report_progress(percent):
                with jobs_lock:
                    if job_id in jobs:
                        jobs[job_id]["progress"] = min(99, max(0, int(percent)))
                        jobs[job_id]["message"] = f"Generating with SVD-XT ({int(percent)}%)"

            runtime.generate_svd(
                image_path,
                str(out),
                steps,
                motion,
                seed,
                progress_callback=report_progress,
            )
            with jobs_lock:
                jobs[job_id].update(
                    status="completed",
                    progress=100,
                    output=out.name,
                    message="Video ready",
                )
        except Exception as exc:
            with jobs_lock:
                jobs[job_id].update(status="failed", message=str(exc))


@app.post("/api/generate")
async def generate(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    model_id: str = Form("svd_xt"),
    prompt: str = Form(""),
    steps: int = Form(10),
    motion: int = Form(127),
    seed: int = Form(42),
    x_api_key: str = Header(default=""),
):
    require_key(x_api_key)
    if model_id != "svd_xt":
        raise HTTPException(status_code=501, detail="This model is planned, not enabled.")
    if runtime.PIPELINE is None:
        raise HTTPException(status_code=503, detail="SVD-XT is not loaded in this Kaggle session.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")
    if not 0 <= motion <= 255:
        raise HTTPException(status_code=400, detail="Motion must be between 0 and 255.")

    requested_steps = int(steps)
    actual_steps = max(5, min(requested_steps, 10))
    job_id = uuid.uuid4().hex
    ext = Path(image.filename or "upload.png").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        ext = ".png"

    content = await image.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 20 MB or smaller.")

    image_path = UPLOADS / f"{job_id}{ext}"
    image_path.write_bytes(content)

    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Queued",
            "prompt_note": prompt[:2000],
            "steps_requested": requested_steps,
            "steps_used": actual_steps,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    background_tasks.add_task(
        run_generation, job_id, str(image_path), actual_steps, motion, seed
    )
    return {
        "job_id": job_id,
        "prompt_supported": False,
        "steps_used": actual_steps,
        "notice": "SVD-XT does not use text prompts. Your prompt is retained as a note only.",
    }


# These two GET routes remain compatible with the existing static website.
# Job IDs are random 128-bit values; do not publish them or share private outputs.
@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    with jobs_lock:
        item = jobs.get(job_id)
        if not item:
            raise HTTPException(status_code=404, detail="Job not found.")
        return {"job_id": job_id, **item}


@app.get("/api/files/{filename}")
def get_file(filename: str):
    safe = Path(filename).name
    path = OUTPUTS / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, media_type="video/mp4", filename=safe)


@app.post("/api/editor/upload")
async def editor_upload(file: UploadFile = File(...), x_api_key: str = Header(default="")):
    require_key(x_api_key)
    if not file.filename:
        raise HTTPException(400, "Filename required.")
    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp4", ".mov", ".mkv", ".webm"}:
        raise HTTPException(400, "Unsupported video format.")
    content = await file.read()
    if len(content) > 500 * 1024 * 1024:
        raise HTTPException(413, "Video must be 500 MB or smaller.")
    name = f"edit_{uuid.uuid4().hex[:12]}{ext}"
    (UPLOADS / name).write_bytes(content)
    return {"filename": name}


class TrimRequest(BaseModel):
    filename: str
    start: float = Field(ge=0)
    duration: float = Field(gt=0, le=600)


class ResizeRequest(BaseModel):
    filename: str
    width: int = Field(ge=256, le=1920)
    height: int = Field(ge=256, le=1080)


class MergeRequest(BaseModel):
    filenames: list[str] = Field(min_length=2, max_length=10)


def run_ffmpeg(args):
    if not shutil.which("ffmpeg"):
        raise HTTPException(503, "FFmpeg is not installed.")
    result = subprocess.run(["ffmpeg", "-y", *args], capture_output=True, text=True)
    if result.returncode:
        raise HTTPException(400, result.stderr[-1500:])


def input_video(name):
    safe = Path(name).name
    path = UPLOADS / safe
    if not path.is_file():
        path = OUTPUTS / safe
    if not path.is_file():
        raise HTTPException(404, f"Video not found: {safe}")
    return path


@app.post("/api/editor/trim")
def trim_video(req: TrimRequest, x_api_key: str = Header(default="")):
    require_key(x_api_key)
    src = input_video(req.filename)
    out = OUTPUTS / f"trim_{uuid.uuid4().hex[:12]}.mp4"
    run_ffmpeg([
        "-ss", str(req.start), "-i", str(src), "-t", str(req.duration),
        "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
        "-movflags", "+faststart", str(out),
    ])
    return {"filename": out.name, "url": f"/api/files/{out.name}"}


@app.post("/api/editor/resize")
def resize_video(req: ResizeRequest, x_api_key: str = Header(default="")):
    require_key(x_api_key)
    src = input_video(req.filename)
    out = OUTPUTS / f"resize_{uuid.uuid4().hex[:12]}.mp4"
    vf = (
        f"scale={req.width}:{req.height}:force_original_aspect_ratio=decrease,"
        f"pad={req.width}:{req.height}:(ow-iw)/2:(oh-ih)/2"
    )
    run_ffmpeg([
        "-i", str(src), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
        "-c:a", "aac", "-movflags", "+faststart", str(out),
    ])
    return {"filename": out.name, "url": f"/api/files/{out.name}"}


@app.post("/api/editor/merge")
def merge_videos(req: MergeRequest, x_api_key: str = Header(default="")):
    require_key(x_api_key)
    paths = [input_video(name) for name in req.filenames]
    listing = UPLOADS / f"concat_{uuid.uuid4().hex[:12]}.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in paths))
    out = OUTPUTS / f"merge_{uuid.uuid4().hex[:12]}.mp4"
    try:
        run_ffmpeg([
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-c", "copy", "-movflags", "+faststart", str(out),
        ])
    finally:
        listing.unlink(missing_ok=True)
    return {"filename": out.name, "url": f"/api/files/{out.name}"}
