FROM python:3.11-slim

WORKDIR /app

# Cài đặt các gói Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn vào image
COPY . .

# Chạy FastAPI server (environment vars đã inject từ docker-compose.yml)
ENV APP_ENV=production

# Chạy uvicorn với reload cho development, không reload cho production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]