# Backend - Poultry Disease Warning API

Backend REST API bằng Python/FastAPI, sử dụng SQLAlchemy 2.x (async) và Postgres/PostGIS.

## Yêu cầu

- Python 3.11+
- PostgreSQL với PostGIS extension
- Pip >= 24.0
- Docker Desktop (tuỳ chọn)

## Cấu trúc code backend

```
backend/
├── app/
│   ├── api/v1/api.py          # Router tổng hợp API v1
│   ├── api/v1/endpoints/      # endpoints: auth, farms, outbreaks, alerts
│   ├── core/
│   │   ├── config.py          # Settings + biến môi trường (Pydantic v2)
│   │   └── database.py        # Async engine, session maker, init_db(), close_db()
│   ├── db/                    # migration và seed data
│   ├── models/                # SQLAlchemy model definitions
│   ├── schemas/               # Pydantic schemas cho requests/responses
│   ├── services/              # Business logic layers
│   ├── utils/                 # Utilities (geo, auth)
│   └── main.py                # FastAPI application entry
├── alembic/                   # Database migrations
├── requirements.txt          # Dependencies Python
├── Dockerfile               # Docker image cho backend
└── .env.example             # Mẫu biến môi trường
```

## Biến môi trường quan trọng

Tham khảo `.env.example`. Các biến cần thiết:

```bash
# --- Database ---
DATABASE_URL=postgresql+asyncpg://POSTGRES_USER:POSTGRES_PASSWORD@localhost:5432/poultry_disease_warning
TEST_DATABASE_URL=postgresql+asyncpg://POSTGRES_USER:POSTGRES_PASSWORD@localhost:5432/poultry_disease_test

# --- Alert settings ---
DEFAULT_ALERT_RADIUS_KM=5.0

# --- CORS ---
CORS_ORIGINS=http://localhost:5173
BACKEND_CORS_ORIGINS=http://localhost:5173
```

Giải thích các biến:

| Biến | Mô tả |
|---|---|
| `DATABASE_URL` | Connection string cho database production. Sử dụng Postgres + asyncpg driver, hỗ trợ transaction async. |
| `TEST_DATABASE_URL` | Connection string cho database test (Pytest). Nên là database riêng hoặc schema khác để cách ly test. |
| `DEFAULT_ALERT_RADIUS_KM` | Bán kính mặc định (km) để tính cảnh báo dịch bệnh gần khu vực trang trại. Mặc định: 5 km. |
| `CORS_ORIGINS` | Dấu phẩy ngăn cách các origin cho phép CORS cho frontend (tuỳ chọn cho cả frontend và backend). |
| `BACKEND_CORS_ORIGINS` | CORS origins riêng cho backend (trùng với CORS_ORIGINS nếu dùng chung một giá trị). |

## Cài đặt và chạy

### Bằng pip + uvicorn:

```bash
# 1. Tạo venv và install dependencies
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy .env.example thành .env và chỉnh sửa
cp .env.example .env
notepad .env  # hoặc editor bạn muốn

# 3. Chạy database migrations (chỉ chạy 1 lần, khi có thay đổi schema)
alembic upgrade head

# 4. Chạy ứng dụng
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ứng dụng sẽ listen tại `http://localhost:8000`. API documentation (Swagger UI) tại `/docs`, ReDoc tại `/redoc`.

### Bằng Docker:

```bash
# Build image
docker build -t poultry-warning-backend .

# Chạy container với biến môi trường từ file
docker run --env-file .env -p 8000:8000 \
  -v "$(pwd)/alembic:/app/alembic" \
  poultry-warning-backend:latest
```

## Architecture tóm tắt

- **Startup**: FastAPI lifespan events gọi `init_db()` để test kết nối, sau shutdown gọi `close_db()` dispose engine.
- **Session management**: Sử dụng SQLAlchemy async session maker (`async_session_maker`) với `expire_on_commit=False`.
- **Database operations**: Inject dependency qua `get_db()` trong route handlers hoặc service functions.

### Các file chính:

| File | Chức năng |
|---|---|
| `app/main.py` | FastAPI app, lifespan events (init_db, close_db), CORS middleware, health/root endpoints |
| `app/core/config.py` | Settings bằng Pydantic v2 + pydantic-settings; đọc biến môi trường uppercase; property/field conversion |
| `app/core/database.py` | Async engine creation, session maker, `init_db()`, `close_db()`, dependency `get_db()` |
| `app/models/*` | SQLAlchemy models (Base, Farm, Outbreak, Alert, Role, User v.v.) - xem thư mục models/ |

## Test và migration

- Không chạy migration hay seed data trong production. Nguyên tắc "không tạo DB mới": chỉ migrate khi cần thiết theo quy trình cụ thể.
- Pytest setup sử dụng `TEST_DATABASE_URL` để cách ly test khỏi database production.

## OpenAPI schema

OpenAPI docs tự động được generate từ Pydantic models, FastAPI routes và config:
- Title: `Poultry Disease Warning System`
- Version: `0.1.0`
- API prefix: `/api/v1`

Xem trong `/docs` khi ứng dụng chạy.
