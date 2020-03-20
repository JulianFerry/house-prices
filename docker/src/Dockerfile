# syntax=docker/dockerfile:experimental
FROM python:3.7-slim-buster as base

WORKDIR /opt/


FROM base as builder

# Install poetry
COPY get-poetry.py /opt/
RUN python /opt/get-poetry.py --version 1.0.5 -y

# Force poetry to install to /opt/venv virtualenv
RUN python -m venv /opt/venv
ENV PATH="/root/.poetry/bin:/opt/venv/bin:$PATH"
RUN poetry config virtualenvs.create false

# Install python packages - cached with BuildKit
COPY pyproject.toml poetry.lock /opt/
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    cd /opt/build && \
    poetry install -v --no-root --no-dev

# Run preprocessing and modelling code
ENV SQL_SERVER_URL='mysql+pymysql://root:root@host.docker.internal:3306' \
    SQL_DATABASE='HousePrices' \
    SQL_SCHEMA='build'
COPY src/db.py src/preprocessing.py src/model.py  /opt/src/
RUN mkdir /opt/src/app /opt/src/app/pickle && \
    poetry run python /opt/src/preprocessing.py && \
    poetry run python /opt/src/model.py


FROM base as release

# Copy virtualenv from installer
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code from docker build context - flatten the app/ folder structure
COPY src/db.py src/preprocessing.py src/model.py src/app  /opt/app/

# Copy created models from builder
COPY --from=builder /opt/src/app/pickle /opt/app/pickle

# Run flask app
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "--chdir", "/opt/app/", "main:app"]
