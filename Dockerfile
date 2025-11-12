# Use an official Python runtime as a parent image
FROM python:3.13-alpine

# Keep Python output unbuffered and avoid writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install build dependencies temporarily
RUN apk add --no-cache --virtual .build-deps gcc

# Install curl for healthchecks
RUN apk add --no-cache curl

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies in virtual environment and remove build deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip && \
    apk del .build-deps

# Create non-root user
RUN adduser -D -u 1000 appuser

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

# Copy Reticulum config into the runtime user's home so it is available at ~/.reticulum/config
COPY --chown=appuser:appuser config /home/appuser/.reticulum/config

# Create cache directory with proper permissions
RUN mkdir -p cache && chown appuser:appuser cache
USER appuser

# Set the working directory (again for the new user)
WORKDIR /app

# Expose the port the app runs on
EXPOSE 5000

# Use waitress to serve the app with 8 threads (expects Flask app object `app` in rBrowser.py)
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=8", "rBrowser:app"]
