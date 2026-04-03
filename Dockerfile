# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14.0
ARG VIRTUAL_ENV=/opt/venv

FROM python:${PYTHON_VERSION}-slim AS base
ARG VIRTUAL_ENV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_LINK_MODE=copy \
  UV_PYTHON_DOWNLOADS=0 \
  UV_COMPILE_BYTECODE=1 \
  VIRTUAL_ENV=${VIRTUAL_ENV} \
  PATH="${VIRTUAL_ENV}/bin:$PATH"

WORKDIR /app

RUN uv venv ${VIRTUAL_ENV}

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --no-editable --active --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-editable --active --no-dev


FROM base AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --active
ENTRYPOINT ["uvicorn", "con_hash.main:app", "--host=0.0.0.0", "--port=8000", "--reload" ]


FROM python:${PYTHON_VERSION}-slim AS application
ARG VIRTUAL_ENV
ARG UID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  VIRTUAL_ENV=${VIRTUAL_ENV} \
  PATH="${VIRTUAL_ENV}/bin:$PATH"

RUN adduser \
  --disabled-password \
  --gecos "" \
  --home "/app" \
  --no-create-home \
  --uid "${UID}" \
  appuser && \
  mkdir -p /app && chown appuser:appuser /app

WORKDIR /app

COPY --from=base --chown=appuser:appuser ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=base --chown=appuser:appuser /app/static ./static

USER appuser
EXPOSE 8000

ENTRYPOINT ["uvicorn", "con_hash.main:app", "--host=0.0.0.0", "--port=8000" ]
