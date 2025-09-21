FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN mkdir -p /etc && echo "docker-container-$(date +%s)" > /etc/machine-id
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
