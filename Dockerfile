FROM python:3.12-slim

# Environment hygiene
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.3.1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cache-friendly)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

# Copy project
COPY . .

# Expose Flask port
EXPOSE 5000

# Run app
CMD ["poetry", "run", "gunicorn", "-b", "0.0.0.0:5000", "app:create_app()"]
