# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Initialize databases inside image build step
RUN python database_setup.py && python vector_setup.py

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start Uvicorn server
CMD ["python", "main.py"]