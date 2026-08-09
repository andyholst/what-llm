"""Smoke tests: repo scaffolding files exist and are wired (PR-1 gate).

Deliberately imports nothing from estimator/artifacts — those land in later PRs.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_license_present():
    lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in lic
    assert "Version 2.0" in lic


def test_readme_present():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "what-llm" in readme
    assert "Apache License 2.0" in readme


def test_requirements_present():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for dep in ("huggingface_hub", "requests", "jsonschema"):
        assert dep in req


def test_gitignore_covers_secrets_and_state():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".env", "data/", "node_modules/", ".venv/"):
        assert entry in gi


def test_ci_workflow_present():
    wf = ROOT / ".github" / "workflows" / "ci.yml"
    assert wf.exists()
    assert "pytest" in wf.read_text(encoding="utf-8")


def test_openspec_change_scaffolded():
    change_dir = ROOT / "openspec" / "changes" / "add-hf-model-pipeline"
    for artifact in ("proposal.md", "design.md", "tasks.md"):
        assert (change_dir / artifact).exists()
    assert (change_dir / "specs" / "model-pipeline" / "spec.md").exists()
