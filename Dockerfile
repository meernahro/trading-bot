# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the dependencies file to the working directory.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the working directory contents into the container.
COPY . .

# Expose port 80 for the web server.
EXPOSE 80

# Run the application.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
