FROM python:3-alpine

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev build-base libffi-dev openssl-dev python3-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything into container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH so Flask sees modules inside /app/src as top-level
ENV PYTHONPATH=/app/src

EXPOSE 8080

# Command to run the application using Gunicorn
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8080", "app:app"]

