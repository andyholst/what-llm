## ADDED Requirements

### Requirement: Pages deployment workflow
A `pages` workflow MUST exist at `.github/workflows/pages.yml`.
- MUST trigger on `push` to `main` (covers every PR merge) and on `workflow_dispatch`.
- MUST declare `permissions: contents: read, pages: write, id-token: write`.
- MUST use the official actions in order: `actions/configure-pages`,
  `actions/upload-pages-artifact`, `actions/deploy-pages`.
- MUST stage `index.html`, `models/`, `LICENSE`, `README.md` and a
  `deploy_info.json` ({sha, deployed_at, ref}) into the artifact directory.
- MUST run in an `environment: github-pages` with the deployment URL exposed.

#### Scenario: deploy after a merge
- **WHEN** a pull request merges into `main`
- **THEN** the workflow runs and deploys the staged site to GitHub Pages
- **AND** the live URL shows the merged code

#### Scenario: manual re-deploy
- **WHEN** a maintainer triggers `workflow_dispatch`
- **THEN** the same deploy job runs without a code change

### Requirement: Hermetic workflow tests
A pytest module MUST validate the workflow without network:
- the YAML parses and its job list contains the three official actions in order;
- the triggers include `push.main` and `workflow_dispatch`;
- permissions grant `pages: write` and `id-token: write`;
- every staged path exists relative to the repo root.

#### Scenario: CI validates the workflow
- **WHEN** the CI gate runs `pytest`
- **THEN** `tests/test_pages_workflow.py` passes against the committed workflow file

### Requirement: Live verification
The deployed site MUST be reachable: GET https://andyholst.github.io/what-llm/
SHALL return HTTP 200 with the site HTML.

#### Scenario: site responds
- **WHEN** the workflow has run successfully
- **THEN** GET https://andyholst.github.io/what-llm/ returns HTTP 200
- **AND** the response contains the what-llm page HTML
