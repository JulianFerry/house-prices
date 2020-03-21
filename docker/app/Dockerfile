# syntax = docker/dockerfile:experimental
FROM python:3.7-slim-buster as base

WORKDIR /opt/


FROM base as installer

# Install poetry
COPY get-poetry.py /opt/
RUN python get-poetry.py --version 1.0.5 -y

# Force pip and poetry to install to venv virtualenv
RUN python -m venv venv
ENV PATH="/root/.poetry/bin:/opt/venv/bin:$PATH"
RUN poetry config virtualenvs.create false

# Install python packages
COPY pyproject.toml poetry.lock /opt/
RUN --mount=type=cache,target=/root/.cache/pip \
    poetry export -f requirements.txt > requirements.txt && \
    pip install -U pip && \
    pip install -r requirements.txt


FROM base as release

# Copy virtualenv from installer
COPY --from=installer /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code from repository - flatten the app/ folder structure
COPY src/app src/database.py src/preprocessing.py src/model.py  /opt/app/

# Copy created models from S3 bucket (currently from repository)
RUN mkdir app/pickle
COPY pickle/PreProcessor.pkl pickle/Model.pkl  /opt/app/pickle/

# Run flask app
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "--chdir", "app", "main:app"]
