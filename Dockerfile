FROM python:3.13-alpine

WORKDIR /app

# Python Print to stdout
ENV PYTHONUNBUFFERED=1

# Copy everything into the container
COPY . .

# install python deps
RUN pip install --no-cache-dir -r requirements.txt

# run with Gunicorn
CMD ["gunicorn", "-t", "60", "-w", "2", "-n", "ESports-PyManager", "--bind", "0.0.0.0:5000", "app:app", "--log-level", "warning"]