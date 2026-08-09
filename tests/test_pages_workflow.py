"""Hermetic tests for the GitHub Pages deployment workflow (add-github-pages 1.4).

Validates .github/workflows/pages.yml structure and staged content without network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"

STAGED = ["index.html", "models/index.js", "models/bundle.js", "LICENSE", "README.md"]


@pytest.fixture(scope="module")
def wf() -> dict:
    if not WORKFLOW.exists():
        pytest.skip("pages.yml not present yet")
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_triggers_on_push_main_and_dispatch(wf):
    on = wf.get("on") or wf.get(True)  # YAML 1.1 parses the key `on` as boolean True
    assert "main" in on["push"]["branches"]
    assert "workflow_dispatch" in on


def test_permissions_grant_pages_and_idtoken(wf):
    perms = wf["permissions"]
    assert perms["contents"] == "read"
    assert perms["pages"] == "write"
    assert perms["id-token"] == "write"


def test_official_actions_in_order(wf):
    steps = wf["jobs"]["deploy"]["steps"]
    uses = [s["uses"] for s in steps if "uses" in s]
    assert uses == [
        "actions/checkout@v4",
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
    ]


def test_environment_and_url_output(wf):
    env = wf["jobs"]["deploy"]["environment"]
    assert env["name"] == "github-pages"
    assert "deployment.outputs.page_url" in env["url"]


def test_staged_paths_exist():
    for rel in STAGED:
        assert (ROOT / rel).exists(), f"missing staged path: {rel}"
    assert (ROOT / "models" / "meta.json").exists()


def test_deploy_info_written_by_stage_step(wf):
    stage = next(s for s in wf["jobs"]["deploy"]["steps"] if s.get("name") == "Stage static site")
    run = stage["run"]
    assert "_site/deploy_info.json" in run
    assert "GITHUB_SHA" in run and "deployed_at" in run
