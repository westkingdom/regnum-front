# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for production
ENV PYTHONPATH=/app
ENV STREAMLIT_ENV=production
ENV REGNUM_API_URL=https://regnum-api-njxuammdla-uw.a.run.app
ENV BASE_URL=https://wkregnum-njxuammdla-uw.a.run.app
ENV REDIRECT_URL=https://wkregnum-njxuammdla-uw.a.run.app
ENV REGNUM_ADMIN_GROUP=00kgcv8k1r9idky

# Authentication is enabled by default (no bypass)
ENV BYPASS_AUTH=false
ENV BYPASS_GROUP_CHECK=false
ENV USE_MOCK_DATA=false

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]