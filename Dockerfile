# syntax=docker/dockerfile:1
FROM python:3.11-slim-buster

EXPOSE 80

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Install Microsoft ODBC driver dependencies
RUN apt-get update && apt-get install -y curl apt-transport-https lsb-release gnupg

# Download and install Microsoft ODBC driver directly
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Optional: Install mssql-tools and set PATH environment variable
RUN ACCEPT_EULA=Y apt-get install -y mssql-tools18
ENV PATH="$PATH:/opt/mssql-tools18/bin"

# Install unixODBC development headers
RUN apt-get install -y unixodbc-dev

# Copy your application code into the container
COPY . .

CMD ["python3", "-m", "server"]
