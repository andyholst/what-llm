# what-llm crawler image — built & run with rootless nerdctl on the host (make build/crawl/serve).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY src ./src
COPY schemas ./schemas
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .

RUN groupadd -g 1000 appuser \
    && useradd -m -u 1000 -g appuser -s /usr/sbin/nologin appuser

ENV HF_HOME=/app/data/hf-cache \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PYTHONUNBUFFERED=1

USER appuser
ENTRYPOINT ["python", "-m", "whatllm.crawl_models"]
CMD ["--help"]
