# Node.js + Playwright test container for the what-llm CI gate (and local `make node-test`).
FROM node:20-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Node deps (jsdom + @playwright/test) and the OpenSpec CLI (not saved to the manifest)
COPY package.json package-lock.json ./
RUN npm ci
RUN npm install --no-save @fission-ai/openspec@latest

# Chromium for the Playwright browser tests (with OS deps)
RUN npx playwright install --with-deps chromium

CMD ["bash", "-c", "npm test && npx playwright test && (if [ -f models/index.js ]; then node --check models/index.js; fi) && (if [ -f models/bundle.js ]; then node --check models/bundle.js; fi) && ./node_modules/.bin/openspec validate add-hf-model-pipeline && ./node_modules/.bin/openspec validate expand-hardware-tiers && ./node_modules/.bin/openspec validate add-compose-ci-harness"]
