FROM python:3.11-slim
WORKDIR /app
COPY backend/iot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/iot/ .
COPY backend/shared ./shared
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "app.py"]
