# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 🏗 Builder stage
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ARG USERNAME=code
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ARG POETRY_FLAGS=""
ARG POETRY_VIRTUALENVS_CREATE=false

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

# 👤 Create non-root user
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash

# ♻️ Update and install system deps
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends curl build-essential git libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 🔑 Configure git credentials
RUN --mount=type=secret,id=github_token \
    git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/"

# ♻️ Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# 📦 Copy dependency files
COPY ../pyproject.toml ../poetry.lock /src/

# ♻️ Install Poetry dependencies
RUN poetry install --no-root $POETRY_FLAGS && \
    poetry cache clear . --all --no-interaction


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 🧩 Final image
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS final

ARG USERNAME=code
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/src

WORKDIR /src

# ♻️ Install runtime deps for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 📦 Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 🧹 Remove poetry from final image
RUN rm -f /usr/local/bin/poetry

# 📦 Copy application source
COPY ../src /src
COPY ../alembic.ini /src
COPY ../alembic /src/alembic

# 👤 Use non-root user
COPY --from=builder /etc/group /etc/group
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /home/$USERNAME /home/$USERNAME
USER $USERNAME

EXPOSE 8000

# 🚀 Run application
CMD ["uvicorn", "main:app", "--workers=1", "--host", "0.0.0.0", "--port", "8000"]
