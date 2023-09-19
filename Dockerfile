FROM docker.io/library/python:3.11.3-alpine3.16@sha256:0ba61d06b14e5438aa3428ee46c7ccdc8df5b63483bc91ae050411407eb5cbf4

RUN pip install poetry==1.5.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

COPY zap_bot ./zap_bot

RUN poetry install

# -u "Force the stdout and stderr streams to be unbuffered"
ENTRYPOINT ["poetry", "run", "python", "-u", "-m", "zap_bot.bot_stream"]