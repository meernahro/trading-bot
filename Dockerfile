# Dockerfile

# Use Python 3.11
# FROM python:3.11-slim

FROM nikolaik/python-nodejs:python3.11-nodejs23-slim


# Set the working directory in the container.
WORKDIR /app

# Copy the dependencies file to the working directory.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the working directory contents into the container.
COPY . .

