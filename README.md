# AI Video Studio

A GitHub Pages dashboard with a Kaggle GPU backend for image-to-video generation and basic video editing.

## Current capability status

- **SVD-XT image-to-video:** integrated. It generates 25 frames. The dashboard uses a 5–10 step setting for a faster first test.
- **CogVideoX-5B I2V, Wan 2.1 I2V, LTX-Video I2V:** planned only; they are not implemented or selectable as working models yet.
- **Video editor:** upload clips, preview the original locally, trim by start/end time, resize to 480p/720p/1080p or custom dimensions, join selected clips, preview the result and download MP4.
- **System dashboard:** CPU, RAM, free disk, GPU count and VRAM status from the Kaggle backend.

SVD-XT does not understand text prompts. The prompt field is a note and does not control its output.

## Project structure

```text
AI_Video_Studio/
├── backend/
│   ├── app.py
│   ├── runtime.py
│   └── __init__.py
├── kaggle/
│   └── AI_Video_Studio_Kaggle.ipynb
├── site/
│   ├── index.html
│   └── tunnel-config.json
├── .github/workflows/deploy-pages.yml
├── requirements-kaggle.txt
└── README.md
```

## Publish the website

1. Extract this ZIP.
2. Open your existing local repository folder: `D:\AI VIDEO STUDIO\AI_Video_Studio_Starter`.
3. Copy the extracted project contents into that repository root, replacing files when Windows asks. Do not create an extra nested `AI_Video_Studio` folder.
4. Open GitHub Desktop, review the changed files, enter a summary such as `Repair AI Video Studio project`, then commit and push.
5. In GitHub, confirm `backend/`, `kaggle/`, `site/`, `.github/`, and `requirements-kaggle.txt` are directly visible at repository root.
6. Wait for the GitHub Pages Actions workflow to finish, then open `https://suryaprakash8t.github.io/`.

Do not publish API keys or Hugging Face/GitHub tokens. `site/tunnel-config.json` contains only the public Cloudflare API URL.

## Start the Kaggle backend

1. Open `kaggle/AI_Video_Studio_Kaggle.ipynb` in Kaggle.
2. Select GPU T4 x2 and enable Internet.
3. Confirm Kaggle Secrets are named `AI_VIDEO_API_KEY`, `HF_TOKEN`, and `GITHUB_TOKEN`, and notebook access is enabled. Never paste secret values into the notebook.
4. Run the eight Kaggle phases in order. Phase 5 downloads/loads SVD-XT; the first run can take a while.
5. Phase 7 starts the Cloudflare Quick Tunnel and updates the public `site/tunnel-config.json`.
6. Refresh the website. The tunnel URL should populate automatically. Enter the same value stored in the Kaggle `AI_VIDEO_API_KEY` secret in the password field and click **Connect & refresh status**. Do not put the key in GitHub files.
7. Keep Kaggle running while using the website. A new Kaggle session creates a new tunnel URL.

## Easy editor workflow

1. Open **Easy video editor** and choose one or more video files.
2. Click **Add selected videos**.
3. Select the clip you want to edit.
4. For trimming, enter the start and end time in seconds, then click **Trim selected clip**.
5. For resizing, choose 480p, 720p, 1080p, or Custom, then click **Resize selected clip**.
6. To join clips, tick at least two clips and click **Join selected clips**.
7. Preview the result and click **Download edited MP4**.

The editor previews uploaded originals locally in your browser and keeps the uploaded originals unchanged. Joining is most reliable when source clips have matching codecs, frame rates and dimensions. If joining fails, resize/re-encode clips to the same preset first.

## Important limits

- Kaggle sessions are temporary. Download important videos before stopping the session.
- Two T4 GPUs do not combine into one 30 GB GPU; each has separate VRAM.
- The SVD-XT pipeline uses the GPU/offload configuration in `backend/runtime.py`. Actual generation time depends on the image, hardware availability and current Kaggle limits.
- The first working milestone is SVD-XT. The other three models require separate implementation and GPU validation.
