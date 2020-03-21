FROM python:3.7-slim-buster as base

WORKDIR /opt/


FROM base as builder

# Install poetry
COPY get-poetry.py /
RUN python get-poetry.py --version 1.0.5 -y

# Force poetry to install to venv virtualenv
RUN python -m venv venv
ENV PATH="/root/.poetry/bin:/venv/bin:$PATH"
RUN poetry config virtualenvs.create false

# Install python packages
COPY pyproject.toml poetry.lock /
RUN cd build && \
    poetry install -v --no-root --no-dev

# Run preprocessing and modelling code
ENV SQL_SERVER_URL='mysql+pymysql://root:root@host.docker.internal:3306' \
    SQL_DATABASE='HousePrices' \
    SQL_SCHEMA='build'
COPY src/database.py src/preprocessing.py src/model.py  /src/
RUN mkdir /src/app /src/app/pickle && \
    poetry run python /src/preprocessing.py && \
    poetry run python /src/model.py


FROM base as release

# Copy virtualenv from installer
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy source code from docker build context - flatten the app/ folder structure
COPY src/database.py src/preprocessing.py src/model.py src/app  /app/

# Copy created models from builder
COPY --from=builder /src/app/pickle /app/pickle

# Run flask app
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "--chdir", "/app/", "main:app"]
