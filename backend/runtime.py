from pathlib import Path
import gc
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video
from PIL import Image

PIPELINE = None
MODEL_ID = "stabilityai/stable-video-diffusion-img2vid-xt"
OUTPUT_DIR = Path("/kaggle/working/AI_Video_Studio/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_svd(cache_dir: str):
    """Load SVD-XT with conservative T4-friendly memory settings."""
    global PIPELINE
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is required for SVD-XT.")
    if PIPELINE is not None:
        return PIPELINE

    PIPELINE = StableVideoDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
        cache_dir=cache_dir,
    )

    # Keep offloading for T4 16-GB cards; this is safer than moving the
    # complete pipeline onto one GPU. It may trade speed for memory safety.
    PIPELINE.enable_model_cpu_offload()
    PIPELINE.unet.enable_forward_chunking()
    return PIPELINE


def generate_svd(
    image_path: str,
    output_path: str,
    steps: int = 10,
    motion_bucket_id: int = 127,
    seed: int = 42,
    progress_callback=None,
):
    """Generate a 25-frame SVD-XT clip and report denoising progress."""
    if PIPELINE is None:
        raise RuntimeError("SVD-XT is not loaded. Run the model-loading cell.")

    # Hard cap at 10 steps in this fast preset, even if an older frontend
    # still submits 25. This avoids accidentally returning to the old setting.
    steps = max(5, min(int(steps), 10))
    image = Image.open(image_path).convert("RGB")
    image = image.resize((1024, 576), Image.Resampling.LANCZOS)
    generator = torch.Generator(device="cuda").manual_seed(int(seed))

    def report_step(pipe, step_index, timestep, callback_kwargs):
        if progress_callback:
            percent = round(((step_index + 1) / steps) * 90)
            progress_callback(min(percent, 90))
        return callback_kwargs

    with torch.inference_mode():
        result = PIPELINE(
            image,
            num_frames=25,
            num_inference_steps=steps,
            motion_bucket_id=int(motion_bucket_id),
            noise_aug_strength=0.1,
            decode_chunk_size=2,
            generator=generator,
            callback_on_step_end=report_step,
        )
        frames = result.frames[0]

    if progress_callback:
        progress_callback(95)

    export_to_video(frames, output_path, fps=7)

    del frames, result
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if progress_callback:
        progress_callback(99)
    return output_path
