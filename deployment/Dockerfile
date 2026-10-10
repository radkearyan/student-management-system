# Python slim base image for minimal footprint
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build dependencies if needed for NumPy/scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies list and install
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source folders
COPY backend/ /app/backend/
COPY database/ /app/database/
COPY frontend/ /app/frontend/

# Create uploads storage folder
RUN mkdir -p /app/backend/uploads

# Expose server port
EXPOSE 5000

# Environment variables configuration
ENV FLASK_APP=backend/app.py
ENV HOST=0.0.0.0
ENV PORT=5000

# Execute server boot
CMD ["python", "backend/app.py"]
