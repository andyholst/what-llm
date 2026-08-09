# what-llm Makefile — the single entry point for the gate. GitHub Actions runs `make ci`;
# run the same command locally with docker (or nerdctl aliased as docker).
DOCKER ?= docker
COMPOSE_FILE := docker-compose-files/ci.yaml
COMPOSE := $(DOCKER) compose -f $(COMPOSE_FILE)

.PHONY: ci py-test node-test help

help: ## Show available targets
	@echo "make ci         - FULL GATE: build + run py and node test containers (what GitHub Actions runs)"
	@echo "make py-test    - run the Python test suite in its container"
	@echo "make node-test  - run jsdom + Playwright + node --check + openspec validate in the node container"
	@echo "make help       - this list"

ci: ## Full gate: build both images, run both test services
	$(COMPOSE) build
	$(COMPOSE) run --rm py
	$(COMPOSE) run --rm node

py-test: ## Python tests only
	$(COMPOSE) run --rm py

node-test: ## Node-side checks only
	$(COMPOSE) run --rm node
