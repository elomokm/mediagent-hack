FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY data/ data/
COPY tests/ tests/

# Install dependencies
RUN uv sync --frozen --no-dev

# Default: mode démo
CMD ["uv", "run", "python", "-m", "src.main", "--demo"]
