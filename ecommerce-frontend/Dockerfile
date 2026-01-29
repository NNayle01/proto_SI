# Dockerfile pour le frontend Python/Flask
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pour le développement, nous utilisons des volumes, donc nous ne copions pas le code ici
# COPY . .

EXPOSE 5001

CMD ["python", "app.py"]