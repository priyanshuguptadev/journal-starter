FROM python:3.11-slim

WORKDIR /app

# Install and setup uv
RUN apt-get update && apt-get install curl -y \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

RUN uv --version

COPY pyproject.toml uv.lock /app/

RUN uv sync

COPY /api /app/api/

EXPOSE 8000

CMD [ "uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000" ]