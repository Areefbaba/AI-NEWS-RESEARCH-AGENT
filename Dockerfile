FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Default Streamlit port
EXPOSE 8501

# Healthcheck: use Render's PORT, default to 8501 locally
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start Streamlit on Render's assigned port, or 8501 locally
CMD ["sh", "-c", "streamlit run frontend/streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
