FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend ./backend

# Copy data directory (containing aeris.db SQLite cache)
COPY data ./data

# Copy built frontend dist if available for unified serving
COPY frontend/dist ./frontend/dist

# Expose FastAPI port
EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
