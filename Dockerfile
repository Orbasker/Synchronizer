# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster

EXPOSE 80

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN apt-get update && apt-get install -y unixodbc-dev

COPY . .
COPY ./odbc-driver-18 /opt/microsoft/msodbcsql18
ENV PATH=$PATH:/opt/microsoft/msodbcsql18/bin

CMD ["python3", "-m" , "server"]