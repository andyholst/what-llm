## ADDED Requirements

### Requirement: Containerized CI gate
The repository SHALL provide a `docker-compose-files/ci.yaml` with a `py` service (Python test container) and a `node` service (Node.js container with a Playwright browser) that together run the full verification gate: hermetic pytest suite, jsdom frontend tests, Playwright browser tests against the served `index.html`, `node --check` on emitted JS artifacts, and `openspec validate` for every active change.

#### Scenario: Compose gate runs
- **WHEN** `make ci` executes on a machine with docker (or compatible compose)
- **THEN** both images build, both services run, and a failure in any check fails the command

#### Scenario: Local parity
- **WHEN** a developer runs `make ci` locally
- **THEN** the exact same checks run as in GitHub Actions CI

### Requirement: Makefile-driven pipeline
The GitHub Actions workflow MUST delegate its checks to the Makefile (`make ci`) instead of duplicating steps, so the CI pipeline and local runs share one entry point.

#### Scenario: CI delegates to Makefile
- **WHEN** a PR branch is pushed
- **THEN** GitHub Actions runs `make ci`, which builds and runs the compose services

## ADDED Acceptance Criteria

- `make ci` (or the CI run) passes: pytest green in the py container; jsdom + Playwright + node --check + openspec validate green in the node container.
- `docker compose -f docker-compose-files/ci.yaml config` is valid.
- The smoke Playwright spec renders the served app and opens `file://` without a blank screen.
