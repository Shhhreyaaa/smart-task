# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# Copy the current directory contents into the container at /app
COPY . /app/

# Create necessary directories
RUN mkdir -p instance logs

# Run database migrations and initialization script
# Note: In production, it's safer to run migrations separately, but for a standalone portfolio project, this is fine.
# We map it to an entrypoint script to handle it at runtime.
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Run gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
