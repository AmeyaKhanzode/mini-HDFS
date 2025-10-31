FROM python:3.11-slim

WORKDIR /app

# Copy shared modules and datanode code
COPY ../shared /app/shared/
COPY . /app/datanode/

ENV PYTHONPATH="/app"

WORKDIR /app/datanode

# Run the datanode socket handler
CMD ["python", "socket_handler.py"]
