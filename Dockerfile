# pull official base image
FROM python:3.10-slim-buster as base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/rssscraper
ENV PATH="/usr/src/rssscraper/venv/bin:$PATH"

RUN apt-get update && apt-get install libpq5 -y && apt-get clean

# builder stage (multistage for lightweight container without gcc)
FROM base as builder

RUN python -m venv venv

# install dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip \
    && apt-get install --no-install-recommends -y libpq-dev python3-dev gcc \
    && pip install -r /requirements.txt

FROM base

# copy venv from builder stage
COPY --from=builder /usr/src/rssscraper/venv /usr/src/rssscraper/venv

# copy project
COPY app /usr/src/rssscraper/app/
COPY worker  /usr/src/rssscraper/worker/

# run uwsgi
CMD  uwsgi --http 0.0.0.0:8000 --master -w app:app