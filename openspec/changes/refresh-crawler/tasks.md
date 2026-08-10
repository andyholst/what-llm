## 1. Refresh mode — PR-O

- [ ] 1.1 `crawl_models.py`: `--refresh` + `--in` flags; `Crawler.refresh()` (re-fetch detail, update volatile fields, preserve quants/hardware, re-enrich, validate, collect); main() branches on --refresh
- [ ] 1.2 `Makefile`: `refresh` target (nerdctl, host network, mounts) + help text + .PHONY
- [ ] 1.3 Hermetic tests: tests/test_crawler_refresh.py (updates downloads/trending, preserves quants/hardware, rebuilds profile, schema-valid emit, skips artifacts, parser flags) + test_makefile.py refresh dry-run
- [ ] 1.4 README: document `make refresh`; openspec validate
