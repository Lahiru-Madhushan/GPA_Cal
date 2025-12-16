FROM python:3.12-slim

# Avoid Python buffering logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies for pdfplumber / Pillow (fonts, images) and common build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tcl8.6-dev \
    tk8.6-dev \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose default Streamlit port
EXPOSE 8501

# Streamlit configuration to allow running in Docker
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Entrypoint to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]


