"""Makefile targets parse and carry the right flags (tasks 6.3-6.4).

Runs `make -n` (dry-run) — no containers are started; the crawler/serve targets must
contain the nerdctl flags we rely on (host networking, uid mapping, bind mounts,
entrypoint override for serve).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def make_n(target: str, extra: str = "") -> str:
    r = subprocess.run(
        f"make -n {target} {extra}", shell=True, capture_output=True, text=True, cwd=ROOT
    )
    assert r.returncode == 0, f"make -n {target} failed: {r.stderr}"
    return r.stdout


def test_ci_uses_compose_gate():
    out = make_n("ci")
    assert "compose" in out
    assert "ci.yaml" in out
    assert "run --rm py" in out
    assert "run --rm node" in out


def test_build_uses_nerdctl_build_and_crawler_dockerfile():
    out = make_n("build")
    assert "build -t" in out
    assert "crawler.Dockerfile" in out


def test_crawl_target_mounts_volumes_and_host_network():
    out = make_n("crawl", "LIMIT=5")
    assert "--network host" in out
    assert "--user" in out
    assert "-v" in out
    assert "/app/models" in out
    assert "/app/data" in out
    assert "--limit 5" in out


def test_refresh_target_updates_existing_models():
    out = make_n("refresh")
    assert "--refresh" in out
    assert "--out /app/models" in out
    assert "--in /app/models" in out
    assert "--network host" in out


def test_serve_overrides_entrypoint_and_serves_repo():
    out = make_n("serve")
    assert "--entrypoint python" in out
    assert "http.server" in out
    assert "--directory /app" in out


def test_clean_only_removes_image():
    out = make_n("clean")
    assert "rmi -f" in out
    assert "models" not in out
