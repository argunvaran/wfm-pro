
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (needed for PostgreSQL and others)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Entrypoint script (Entrypoint will be defined in docker-compose or k8s)
# For standalone container:
CMD ["gunicorn", "wfm_core.wsgi:application", "--bind", "0.0.0.0:8000"]
