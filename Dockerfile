# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster

EXPOSE 80

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-m" , "server"]