FROM python:3-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache build-base libffi-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything into container
COPY . .

# Set PYTHONPATH so Flask sees modules inside /app/src as top-level
ENV PYTHONPATH=/app/src

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
