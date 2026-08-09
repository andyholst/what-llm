# Python test container for the what-llm CI gate (and local `make py-test`).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt pyproject.toml ./
COPY src ./src
COPY schemas ./schemas

RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -r requirements-dev.txt \
 && pip install --no-cache-dir -e .

CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
