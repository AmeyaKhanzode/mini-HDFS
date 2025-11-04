FROM python:3.11-slim

WORKDIR /app

# to install sqlite3 on namenode
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    libsqlite3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy shared modules and namenode code
COPY shared /app/shared/
COPY namenode /app/namenode/

# Install Python dependencies
COPY namenode/requirements.txt /app/namenode/requirements.txt
RUN pip install --no-cache-dir -r /app/namenode/requirements.txt

ENV PYTHONPATH="/app"

WORKDIR /app/namenode

# Run the namenode socket handler
CMD ["python", "server.py"]
