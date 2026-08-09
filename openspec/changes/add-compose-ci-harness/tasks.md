## 1. Compose services — ships with the interactive milestone PR

- [x] 1.1 Add `docker/py.Dockerfile` (python:3.12-slim; requirements + requirements-dev + editable install; CMD pytest)
  - [x] Verify: image builds and pytest passes inside it (CI proves; `make py-test` locally)
- [x] 1.2 Add `docker/node.Dockerfile` (node:20-slim; Playwright Chromium with deps; npm ci; openspec CLI installed; CMD runs jsdom + playwright + node --check + openspec validate)
  - [x] Verify: image builds; `make node-test` runs all node-side checks green
- [x] 1.3 Add `docker-compose-files/ci.yaml` (services py + node; bind-mount repo at /app; mask /app/.venv and /app/node_modules)
  - [x] Verify: `docker compose -f docker-compose-files/ci.yaml config` is valid; GH Actions run green
- [x] 1.4 Add `Makefile` targets: `ci`, `py-test`, `node-test` (compose-backed; the gate)
  - [x] Verify: `make -n ci` prints compose commands; CI (GitHub Actions) runs `make ci`
- [x] 1.5 Rewrite `.github/workflows/ci.yml` to a thin `make ci` wrapper
  - [x] Verify: workflow YAML valid; a PR run executes the compose gate
- [x] 1.6 Add Playwright: `playwright.config.mjs`, `tests/e2e/serve.mjs`, `tests/e2e/whatllm.spec.mjs` (smoke: served page renders; file:// opens without blank screen); package.json devDep @playwright/test; .gitignore test-results/
  - [x] Verify: smoke spec green in the node container (and locally where browsers available)
- [x] 1.7 Commit, push branch, PR, CI green, merge
  - [x] Verify: CI passes on the PR; PR merged

## 2. Local parity

- [x] 2.1 Document local runs in README (`make ci` with docker; nerdctl-compose TTY/collision caveats; `script -qec` wrapper note)
  - [x] Verify: README section matches the Makefile and compose file
