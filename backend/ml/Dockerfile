FROM python:3.11-slim
WORKDIR /app
COPY backend/ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ml/ .
COPY backend/shared ./shared
CMD ["python", "app.py"]
