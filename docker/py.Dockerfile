# Python test container for the what-llm CI gate (and local `make py-test`).
FROM python:3.12-slim

WORKDIR /app

# make is needed by tests/test_makefile.py (make -n dry-run assertions)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates make \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt pyproject.toml ./
COPY src ./src
COPY schemas ./schemas

RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -r requirements-dev.txt \
 && pip install --no-cache-dir -e .

CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
