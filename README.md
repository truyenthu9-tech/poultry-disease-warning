poultry-disease-warning

Hệ thống cảnh báo dịch bệnh chăn nuôi gia cầm (gà, vịt, ngan...) cho người chăn nuôi. Ứng dụng chia ba: frontend (React + Vite), backend (Python/FastAPI), và cơ sở dữ liệu PostgreSQL. Người dùng đăng ký trang trại (farm), quản lý thông tin trang trại, theo dõi các vụ dịch (outbreak) và nhận cảnh báo (alert) khi có dịch bệnh gần khu vực trang trại.

Cấu trúc dự án
poultry-disease-warning/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py      # đọc biến môi trường
│   │   │   └── database.py    # kết nối SQLAlchemy
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # logic nghiệp vụ
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   └── endpoints/  # auth, farms, outbreaks, alerts
│   │   │   └── v1/api.py
│   │   └── db/                # khởi tạo DB và seed dữ liệu
│   ├── tests/
│   └── alembic/               # migration cơ sở dữ liệu
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── public/
└── docker-compose.yml         # chạy cả backend và frontend
Chạy dự án

Yêu cầu: Docker Desktop (hoặc PostgreSQL và Python 3.11+ nếu không dùng Docker).

Cách 1: Chạy bằng Docker Compose (khuyến nghị)
bash
# 1. Khởi tạo biến môi trường cho cả backend và frontend
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Khởi động toàn bộ hệ thống (backend + frontend + database)
docker-compose up -d --build

# 3. Truy cập ứng dụng
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
Cách 2: Chạy thủ công (không dùng Docker)
bash
# Setup database PostgreSQL/PostGIS (tự cài đặt hoặc dùng Docker)
# Sau đó khởi chạy backend và frontend riêng

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (tương tự)
cd ../frontend
npm install
npm run dev
Lưu ý khi chạy bằng Docker Compose

Các biến môi trường backend sẽ được inject từ docker-compose.yml:

DATABASE_URL - đường dẫn database production
TEST_DATABASE_URL - đường dẫn database test (cho pytest)
DEFAULT_ALERT_RADIUS_KM - bán kính mặc định cảnh báo (km)

Để override các biến, có thể đặt biến môi trường trước khi chạy:

bash
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypass
docker-compose up -d --build

Sau khi chạy, mở trình duyệt tại http://localhost:5173.

API chính
Phương thức	Endpoint	Mô tả
GET	/health	Health check
GET	/	Root endpoint
POST	/api/v1/auth/register	Đăng ký tài khoản
POST	/api/v1/auth/login	Đăng nhập
GET	/api/v1/auth/me	Thông tin tài khoản hiện tại
GET	/api/v1/farms	Danh sách trang trại
POST	/api/v1/farms	Tạo trang trại mới
GET	/api/v1/outbreaks	Danh sách vụ dịch
GET	/api/v1/alerts	Danh sách cảnh báo
Cấu hình và biến môi trường
Backend (config.py)

Các biến môi trường chính cho backend:

Biến	Mô tả	Giá trị mặc định
DATABASE_URL	Connection string database production	postgresql+asyncpg://postgres@localhost:5432/poultry_disease_warning
TEST_DATABASE_URL	Connection string cho test	postgresql+asyncpg://postgres@localhost:5432/poultry_disease_test
DEFAULT_ALERT_RADIUS_KM	Bán kính mặc định cảnh báo (km)	5.0
CORS_ORIGINS	Dấu phẩy ngăn cách các origin cho phép CORS	http://localhost:5173
BACKEND_CORS_ORIGINS	CORS origins riêng cho backend	http://localhost:5173
APP_ENV	Môi trường ứng dụng	production (set trong Dockerfile)
Frontend (.env.example)

Các biến môi trường frontend - tham khảo file frontend/.env.example.

Lưu ý kỹ thuật
UUID làm khóa chính; enum Postgres tạo trong migration.
Mọi chuyển đổi tọa độ (định dạng, thứ tự lon/lat) đều đi qua app/utils/geo.py.
Pydantic v2 với pydantic-settings để quản lý biến môi trường.
SQLAlchemy 2.x async mode (asyncpg driver).
Không chạy migration hay seed data trong production (nguyên tắc "không tạo DB mới").

Để xem mã nguồn config đầy đủ: backend/app/core/config.py Để xem cấu trúc database và model: backend/app/models/, backend/app/core/database.py

Di chuyển
bash
# Build image backend
cd backend && docker build -t poultry-warning-backend .

# Build image frontend  
cd ../frontend && docker build -t poultry-warning-frontend .