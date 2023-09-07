# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster

EXPOSE 80

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Install Microsoft ODBC driver dependencies and GnuPG
RUN apt-get update && apt-get install -y curl apt-transport-https lsb-release gnupg
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | tee /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18
RUN ACCEPT_EULA=Y apt-get install -y mssql-tools18
RUN echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
RUN source ~/.bashrc

# Install unixODBC development headers
RUN apt-get install -y unixodbc-dev

# Copy your application code into the container
COPY . .

CMD ["python3", "-m", "server"]
