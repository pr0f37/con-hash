# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.14.0
FROM python:${PYTHON_VERSION}-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_COMPILE_BYTECODE=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
RUN uv venv /opt/venv
# Use the virtual environment automatically
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/pip \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project --no-editable --active

# Copy the source code into the container.
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-editable --active


FROM python:${PYTHON_VERSION}-slim AS dev
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=base /opt/venv /opt/venv
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_COMPILE_BYTECODE=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
WORKDIR /app

# Copy the source code into the container.
COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --active

FROM python:${PYTHON_VERSION}-slim AS application
# Copy the environment, but not the source code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_COMPILE_BYTECODE=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"
ARG UID=10001
RUN adduser \
  --disabled-password \
  --gecos "" \
  --home "/app" \
  --shell "/sbin/nologin" \
  --no-create-home \
  --uid "${UID}" \
  appuser

WORKDIR /app
RUN chown appuser:appuser /app
COPY --from=base --chown=appuser:appuser /opt/venv /opt/venv
COPY --chown=appuser:appuser ./static ./static
# Switch to the non-privileged user to run the application.
USER appuser
# Run the application
EXPOSE 8000

ENTRYPOINT ["uvicorn", "con_hash.main:app", "--host=0.0.0.0", "--port=8000" ]
