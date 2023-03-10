# pull official base image
FROM python:3.11-slim-buster

# set work directory
WORKDIR /usr/src/rssscraper

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/rssscraper/requirements.txt
RUN apt-get update && apt-get install -y libpq-dev python3-dev gcc
RUN pip install -r requirements.txt

# copy project
COPY app /usr/src/rssscraper/app/
COPY worker  /usr/src/rssscraper/worker/
#COPY worker /usr/src/rssscraper/
CMD  uwsgi --http 0.0.0.0:8000 --master -w app:app