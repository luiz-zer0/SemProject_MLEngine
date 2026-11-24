FROM python:3.12-slim
WORKDIR /app
COPY requirements-service.lock.txt ./
RUN pip install --no-cache-dir -r requirements-service.lock.txt
COPY matching_system/ matching_system/
COPY service/ service/
ENV APP_ENV=production
EXPOSE 8000
CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8000"]
# Worker deployment uses the same image with command: python -m service.worker
