FROM python:3.11-slim

WORKDIR /app

# Copy shared modules and datanode code
COPY ../shared /app/shared/
COPY . /app/namenode/

ENV PYTHONPATH="/app"

WORKDIR /app/namenode

# Run the datanode socket handler
CMD ["python", "server.py"]
