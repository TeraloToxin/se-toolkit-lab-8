# Dockerfile for nanobot gateway service
# Install nanobot-ai from PyPI, webchat and mcp from local source

# ---
# Stage 1: Build the application
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install nanobot-ai from PyPI
RUN uv pip install --system nanobot-ai

# Install webchat from local source
COPY --from=webchat . /app/webchat-source/
RUN uv pip install --system /app/webchat-source/

# Install mcp from local source
COPY --from=mcp . /app/mcp-source/
RUN uv pip install --system /app/mcp-source/

# Copy nanobot code
COPY . /app/nanobot/

# ---
# Stage 2: Final image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install packages
COPY --from=builder --chown=nonroot:nonroot /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

# Copy application
COPY --from=builder --chown=nonroot:nonroot /app/nanobot /app/nanobot

ENV PATH="/usr/local/bin:$PATH"
WORKDIR /app/nanobot

CMD ["python", "/app/nanobot/entrypoint.py"]
