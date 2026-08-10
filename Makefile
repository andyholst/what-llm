# what-llm Makefile — the single entry point for the gate AND the nerdctl workflow.
# GitHub Actions runs `make ci`; the same command works locally with docker.
# Crawler/serve targets run through nerdctl (aliased `docker` on the host) with bind
# mounts for models/ (JSON output) and data/ (checkpoint + HF cache).
DOCKER ?= docker
NERDCTL ?= docker
IMAGE ?= what-llm:latest
LIMIT ?= 150
SERVE_PORT ?= 8000
UID_GID := $(shell id -u):$(shell id -g)
COMPOSE_FILE := docker-compose-files/ci.yaml
COMPOSE := $(DOCKER) compose -f $(COMPOSE_FILE)

.PHONY: ci py-test node-test build crawl refresh serve clean help

help: ## Show available targets
	@echo "make ci         - FULL GATE: build + run py and node test containers (what GitHub Actions runs)"
	@echo "make py-test    - Python test suite in its container"
	@echo "make node-test  - jsdom + Playwright + node --check + openspec validate in the node container"
	@echo "make build      - nerdctl build the crawler image"
	@echo "make crawl      - nerdctl run the crawler (--limit $(LIMIT)); trending HF models into ./models"
	@echo "make refresh    - nerdctl update EXISTING models in ./models (metadata, downloads, trending)"
	@echo "make serve      - nerdctl run http.server on :$(SERVE_PORT) serving the frontend"
	@echo "make clean      - nerdctl rmi the crawler image"

ci: ## Full gate: build both images, run both test services
	$(COMPOSE) build
	$(COMPOSE) run --rm py
	$(COMPOSE) run --rm node

py-test: ## Python tests only
	$(COMPOSE) run --rm py

node-test: ## Node-side checks only
	$(COMPOSE) run --rm node

build: ## Build the crawler image via nerdctl
	$(NERDCTL) build -t $(IMAGE) -f docker/crawler.Dockerfile .

crawl: ## Run the crawler in the container; models/ + data/ are bind-mounted
	mkdir -p models data
	$(NERDCTL) run --rm --network host --user $(UID_GID) \
		-v $(CURDIR)/models:/app/models \
		-v $(CURDIR)/data:/app/data \
		$(IMAGE) --limit $(LIMIT)

refresh: ## Update EXISTING models' metadata from HF (downloads, trending, license, context)
	mkdir -p models data
	$(NERDCTL) run --rm --network host --user $(UID_GID) \
		-v $(CURDIR)/models:/app/models \
		-v $(CURDIR)/data:/app/data \
		$(IMAGE) --refresh --out /app/models --in /app/models

serve: ## Serve the frontend (index.html + models/) via the container
	mkdir -p models
	$(NERDCTL) run --rm --network host --user $(UID_GID) \
		-v $(CURDIR):/app \
		--entrypoint python \
		$(IMAGE) -m http.server $(SERVE_PORT) --bind 0.0.0.0 --directory /app

clean: ## Remove the crawler image (never touches models/ or data/)
	$(NERDCTL) rmi -f $(IMAGE)
