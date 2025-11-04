FROM python:3.11-slim

WORKDIR /app

# Copy shared modules and datanode code
COPY shared /app/shared/
COPY datanode /app/datanode/

# Install Python dependencies (if any)
COPY datanode/requirements.txt /app/datanode/requirements.txt
RUN pip install --no-cache-dir -r /app/datanode/requirements.txt || true

ENV PYTHONPATH="/app"

WORKDIR /app/datanode

# Run the datanode socket handler
CMD ["python", "server.py"]
