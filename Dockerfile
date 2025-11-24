FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY app ./app

RUN mkdir -p config && pip install --upgrade pip && pip install .

CMD ["cloudflare-ddns"]
