FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create health check endpoint
RUN echo 'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/health")\ndef health_check():\n    return {"status": "healthy"}' > health_check.py

# Expose port 5000
EXPOSE 5000

# Start the FastAPI server
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
