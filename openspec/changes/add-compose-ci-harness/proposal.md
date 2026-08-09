# Add Compose CI Harness

## Why

The user wants the CI jobs to run inside their own containers — Python tests in a
Python container, and the HTML/JavaScript logic tested with a **Playwright browser in a
Node.js container** (each with its own Dockerfile) — driven by a single Makefile that
GitHub Actions also runs, so the exact same gate can be executed locally. The current
CI duplicates steps inline; this makes the pipeline container-native and agnostic.

## What Changes

- `docker-compose-files/ci.yaml` with two services:
  - `py` — python:3.12-slim image (`docker/py.Dockerfile`), runs the hermetic pytest
    suite against the bind-mounted repo (`/app`, `.venv` masked).
  - `node` — node:20-slim image (`docker/node.Dockerfile`) with Playwright Chromium,
    runs jsdom tests (`npm test`), Playwright browser tests against the served
    `index.html`, `node --check` on emitted JS, and `openspec validate` for every
    active change.
- `Makefile` targets: `make ci` (builds both images and runs both services — the gate),
  `make py-test`, `make node-test` for individual runs; all usable locally.
- `.github/workflows/ci.yml` becomes a thin wrapper that runs `make ci` on the runner.
- Playwright config + smoke spec (`tests/e2e/`) with a tiny static server
  (`tests/e2e/serve.mjs`); full interaction specs grow with the frontend milestone.
- `package.json` gains `@playwright/test`; `.gitignore` covers `test-results/` and
  `playwright-report/`.

## Capabilities

- `ci-harness`: containerized, Makefile-driven CI that GitHub Actions runs and any
  developer can run locally with docker/nerdctl (`make ci`).

## Impact

- CI runtime grows (image build + Chromium download) — one-time cost, cached by GH.
- Root `.dockerignore` must NOT exclude `openspec/`/`schemas/`/`models/` (the CI images
  need them); the crawler image still bind-mounts `models/`/`data/` at run time.
- Rootless-nerdctl hosts: `docker compose run` under nerdctl hardcodes `-it` (needs a
  TTY or `script -qec` wrapper) and may hit the 10.4.0.0/24 default-bridge collision —
  documented in the README; GitHub Actions uses real Docker and is unaffected.
