FROM python:3.12.5-alpine3.20

COPY requirements.txt /app/

WORKDIR /app

RUN apk update && \
    apk add gcc musl-dev linux-headers libc-dev libffi-dev openssl-dev make && \
    pip install --default-timeout=100 --upgrade pip && \
    pip install --default-timeout=100 -r requirements.txt

ENV LANG=fr_FR.UTF-8
ENV LC_ALL=fr_FR.UTF-8

COPY . /app/

CMD ["python", "-u", "main.py"]
