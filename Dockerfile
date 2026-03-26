FROM python:3.11-slim-bookworm

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app
COPY app.py .

RUN chown -R appuser:appgroup /app
USER appuser

CMD [ "python", "-u", "app.py"]