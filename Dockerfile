# Open_Educational_Resourcer/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-extras.txt ./
# Install core requirements first, then optional extraction extras
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ -f requirements-extras.txt ]; then pip install --no-cache-dir -r requirements-extras.txt; fi

# Copy project files
COPY . .

# Make the entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Set the entry point
ENTRYPOINT ["./docker-entrypoint.sh"]