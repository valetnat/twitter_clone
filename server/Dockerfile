# Dockerfile
# Uses multi-stage builds
# See https://docs.docker.com/develop/develop-images/multistage-build/

# Creating a python base with shared environment variables
FROM python:3.10-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \

    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \

    POETRY_HOME="/opt/poetry" \
    # Create virtual environments inside the project directory rather than in the default location.
    # It loacted in a .venv folder within yoor project directory (e.g., your_project/.venv).
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # Poetry will operate in an automated mode without waiting for user input.
    # If there is a dependency conflict, Poetry will not wait for you to select how to proceed;
    # Instead, it will terminate with an error,
    POETRY_NO_INTERACTION=1 \

    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# builder-base is used to build dependencies
FROM python-base AS builder-base

RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
# https://python-poetry.org/docs/#installing-with-the-official-installer
ENV POETRY_VERSION=1.8.0
RUN curl -sSL https://install.python-poetry.org | python3 -

# We copy our Python requirements here to cache them
# and install only runtime deps using poetry
WORKDIR $PYSETUP_PATH

COPY ../poetry.lock ./
COPY ../pyproject.toml ./

RUN poetry install --without dev

# 'development' stage installs all dev deps and can be used to develop code.
# For example using docker-compose to mount local volume under /app
FROM python-base AS development
#ENV FASTAPI_ENV=development

# Copying poetry and venv into image
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# venv already has runtime deps installed we get a quicker install
WORKDIR $PYSETUP_PATH
RUN poetry install


WORKDIR /server
COPY server .

EXPOSE 5000

RUN chmod +x /server/entrypoint.sh

# Укажите ENTRYPOINT вместо CMD
ENTRYPOINT ["/server/entrypoint.sh"]

# запуск приложения  происходит в entrypoint, куда передается команда CMD
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=5000", "--reload"]
