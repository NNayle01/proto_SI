# Dockerfile pour l'interface d'administration
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app_minimal.py app.py

EXPOSE 5002

CMD ["python", "app.py"]