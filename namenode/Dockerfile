FROM python:3.11-slim

WORKDIR /app

# to install sqlite3 on namenode
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    libsqlite3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy shared modules and datanode code
COPY ../shared /app/shared/
COPY . /app/namenode/

ENV PYTHONPATH="/app"

WORKDIR /app/namenode

# Run the datanode socket handler
CMD ["python", "server.py"]
