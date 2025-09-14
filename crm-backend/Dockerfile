# Base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=postgresql+psycopg2://koyeb-adm:npg_Ee2ZwayAP1Jh@ep-silent-dust-a4lfcnlq.us-east-1.pg.koyeb.app/koyebdb \
    SECRET_KEY=2703a4ceb92fe47227294748c2d03f07 \
    ALGORITHM=HS256 \
    ACCESS_TOKEN_EXPIRE_MINUTES=10 \
    DEBUG=True \
    HOST=0.0.0.0 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
