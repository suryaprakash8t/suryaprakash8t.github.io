# Installation and replacement guide

## 1. Replace the GitHub repository files

1. Extract this ZIP.
2. Copy the contents inside `AI_Video_Studio/` directly into the root of your existing local repository.
3. Merge/replace folders when Windows asks. Do not create an extra nested `AI_Video_Studio/` folder.
4. Confirm the repository root contains `backend/`, `docs/`, `kaggle/`, `site/`, `.github/`, `requirements-kaggle.txt`, and `README.md`.
5. Commit and push the changes to the `main` branch.

The included `.github/workflows/deploy-pages.yml` deploys `site/` to GitHub Pages using GitHub Actions. In Settings → Pages, keep Source set to **GitHub Actions**.

## 2. Import the Kaggle notebook

Open `kaggle/AI_Video_Studio_Kaggle.ipynb` in Kaggle. Select GPU T4 x2 and enable Internet.

## 3. Check Kaggle Secrets

Add/enable these three secrets in Kaggle Add-ons → Secrets:

- `AI_VIDEO_API_KEY`
- `HF_TOKEN` (optional for public model access; recommended if you have access)
- `GITHUB_TOKEN` (fine-grained token for this repository with Contents: Read and write)

Never paste secret values into notebook code, GitHub, or chat.

## 4. Run the notebook

Run the eight phases in order, one cell at a time. Phase 5 downloads and loads SVD-XT and may take a long time. Phase 7 creates or reuses a Cloudflare Quick Tunnel and updates `site/tunnel-config.json` through the GitHub API. Phase 8 checks the local API.

A Cloudflare HTTP 429 is an external rate limit, not a Python syntax error. Do not repeatedly rerun Phase 7; wait before a single retry.

## 5. Connect the website

Refresh `https://suryaprakash8t.github.io/` after Phase 7. The tunnel URL should fill automatically. Enter the same value stored in `AI_VIDEO_API_KEY` and click **Connect & refresh status**.

Keep the Kaggle session running while using the website. A new Kaggle session normally needs a new Quick Tunnel URL.

## Current model scope

SVD-XT is the only implemented image-to-video model. CogVideoX-5B-I2V, Wan 2.1 I2V and LTX-Video I2V are planned only. SVD-XT does not follow text prompts.

## Troubleshooting

- **401:** The website API key does not match Kaggle's `AI_VIDEO_API_KEY` secret.
- **503:** SVD-XT is not loaded. Check Phase 5.
- **Cloudflare 429:** Wait before retrying Phase 7; repeated requests can prolong rate limiting.
- **GitHub 403 in Phase 7:** Check that `GITHUB_TOKEN` belongs to this repository and has Contents: Read and write.
- **Video merge failure:** Use clips with matching codecs, frame rates and dimensions.
