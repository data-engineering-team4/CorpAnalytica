FROM python:3.8-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get -y update && apt-get -y install vim && apt-get clean
WORKDIR /app
COPY requirements.txt /app/

RUN pip install -r requirements.txt
COPY . /app/