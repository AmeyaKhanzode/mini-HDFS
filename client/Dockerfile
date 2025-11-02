FROM python:3.11-slim

WORKDIR /app

COPY client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY client/ /app/client/

WORKDIR /app

CMD ["uvicorn", "client.central_server:app", "--host", "0.0.0.0", "--port", "8000"]
