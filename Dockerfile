# Use a stable, official lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies required for psycopg2, pymysql, and pyodbc (SQL Server drivers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gnupg2 \
    unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to utilize Docker layer caching
COPY requirements.txt /app/

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy all pipeline layers and files to the container
COPY Layer_1_Connection_Extraction/ /app/Layer_1_Connection_Extraction/
COPY Layer_2_Enterprise_Classification/ /app/Layer_2_Enterprise_Classification/
COPY Layer_3_PII_Detection/ /app/Layer_3_PII_Detection/
COPY Layer_4_Anonymization_Vault/ /app/Layer_4_Anonymization_Vault/
COPY pii_policy.json /app/
COPY .env* /app/

# Default command to run
CMD ["python", "Layer_1_Connection_Extraction/change_detector.py"]
