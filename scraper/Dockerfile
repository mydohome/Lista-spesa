FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nessun CMD: questo container si esegue on-demand con
# "docker compose run --rm scraper python estrai_prezzi.py ..."
