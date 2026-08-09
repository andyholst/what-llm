## 1. Workflow & content — ships in one PR

- [ ] 1.1 `.github/workflows/pages.yml`: trigger on push to main + workflow_dispatch;
      permissions contents:read / pages:write / id-token:write; concurrency group
      cancel-in-progress
- [ ] 1.2 Stage step: copy index.html, models/, LICENSE, README.md into `_site/` and
      write `deploy_info.json` ({sha, deployed_at, ref})
- [ ] 1.3 Deploy step: actions/configure-pages + upload-pages-artifact(path=_site) +
      deploy-pages, environment github-pages with page_url output
- [ ] 1.4 `tests/test_pages_workflow.py` (hermetic): yaml loads; triggers include
      push.main + workflow_dispatch; deploy action present; permissions include
      pages:write + id-token:write; every staged path exists (index.html, models/,
      LICENSE, README.md)
- [ ] 1.5 Verify live: after PR merge + Pages enablement, GET
      https://andyholst.github.io/what-llm/ returns 200 and loads index.html
