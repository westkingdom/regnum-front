# --- Build stage: compile dependencies into an isolated virtualenv ---
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Runtime stage: no compiler, runs as an unprivileged user ---
FROM python:3.11-slim

RUN groupadd --system app && useradd --system --gid app --home-dir /app --no-create-home app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . .

# Set environment variables for production
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV STREAMLIT_ENV=production

# Streamlit configuration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# Don't show Python tracebacks (paths, config, secrets in locals) to visitors
ENV STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=none
ENV STREAMLIT_CLIENT_TOOLBAR_MODE=viewer

USER app

# Expose port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
