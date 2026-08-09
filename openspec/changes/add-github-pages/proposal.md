# Add GitHub Pages deployment

## Why

The user wants to open the what-llm site in a browser and try it (wizard, filters,
profile panel) without cloning the repo or running a server. GitHub Pages serves the
static site at https://andyholst.github.io/what-llm/, and deploying on every merge to
`main` means the live page always matches the shipped code + the committed dataset.

The site is fully static and uses only relative paths (`models/index.js`,
`models/bundle.js`, per-model `fetch("models/<id>.json")`, hash deep-links), so it
works unchanged under the Pages subpath.

## Requirements

- ADDED: static site deployment to GitHub Pages via a `pages` workflow that triggers
  on every push to `main` (PR merges) and via `workflow_dispatch` for manual re-runs.
- ADDED: the deployment artifact contains `index.html`, `models/`, `LICENSE`,
  `README.md`, and a `deploy_info.json` carrying the deployed commit sha + timestamp.
- ADDED: hermetic pytest coverage asserting the workflow exists, triggers on the
  right events, uses the official actions (configure-pages / upload-pages-artifact /
  deploy-pages), and that every staged path exists in the repo.

## Out of scope

- Serving the live-crawled dataset (samples stay committed; `make crawl` on the host
  regenerates models/ in a future PR).
- Enabling Pages in repo settings — one-time human step if the API call is denied.
