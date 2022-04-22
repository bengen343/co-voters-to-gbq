# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY config.py main.py sos_fetch.py load_co_voter_file.py save_to_bq.py ./
