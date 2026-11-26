# Development workflow

## Use ChatGPT for
- architecture decisions and model/hardware compatibility research
- reviewing error logs and suggesting minimal fixes
- checking API contracts and security assumptions
- validating whether a feature is genuinely implemented

## Use Claude Code for
- opening the extracted repository folder
- editing/refactoring multiple files consistently
- running syntax checks and tests
- implementing the next model adapter and timeline UI
- reviewing Git diffs before commit

## Suggested Claude Code first prompt
Read README.md and inspect the complete project. Do not rewrite working files unnecessarily. First run static checks on backend/app.py and backend/runtime.py, identify bugs, and add tests for the health, model registry, authentication, job state, and FFmpeg editing endpoints. Preserve SVD-XT as the only enabled model until another adapter passes a real Kaggle T4 generation test. Do not expose secrets or hardcode the API key. Report every changed file and test result.

## Acceptance tests
1. GitHub Actions deploy succeeds.
2. Kaggle cell 3 loads SVD-XT.
3. `/api/health` returns status=ok and model_loaded=true.
4. Cloudflare tunnel URL opens `/docs`.
5. Website connects with session API key.
6. One real uploaded image generates an MP4.
7. MP4 preview and download work.
8. Editor trim/resize/merge return playable MP4s.
9. CPU/RAM/disk/GPU dashboard values refresh.
10. Restarting Kaggle requires a new tunnel URL and API key.
