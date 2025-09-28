# Use an official Python runtime as a parent image
FROM python:3.13-slim-bullseye

# Keep Python output unbuffered and avoid writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install minimal build/runtime deps (no recommended extras) and clean apt lists to reduce size.
# Adjust packages if your requirements need additional system libs (e.g. libssl-dev, libxml2-dev).
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (no cache).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy the rest of the application code
COPY . .

# Copy Reticulum config into the runtime user's home so it is available at ~/.reticulum/config
# (we will set secure permissions and chown after creating the runtime user below)
COPY config /home/appuser/.reticulum/config

# Create a non-root user and set ownership of the application directory and config
RUN useradd -m -u 1000 appuser || true && \
    chown -R appuser:appuser /app /home/appuser/.reticulum || true && \
    chmod 600 /home/appuser/.reticulum/config || true
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Use the flask CLI to run the app (expects Flask app object `app` in rBrowser.py)
ENV FLASK_APP=rBrowser:app
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
