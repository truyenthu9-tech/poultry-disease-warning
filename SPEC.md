# SPEC: Backend Hệ thống cảnh báo phòng dịch gia cầm

## Mục tiêu

Xây dựng backend Hệ thống cảnh báo phòng dịch gia cầm. Khi có ổ dịch mới được ghi nhận, hệ thống tự tìm các trang trại nằm trong bán kính nguy cơ, tạo cảnh báo (Alert) và gửi thông báo. Khu vực dữ liệu mẫu là Hà Nội và các tỉnh lân cận.

Stack: Python 3.11, FastAPI, SQLAlchemy 2.x (async, asyncpg), GeoAlchemy2, Shapely, Pydantic v2, Alembic, PostgreSQL 15 + PostGIS, Pytest.

## Cấu trúc thư mục

Ghi chú: [P1] là Giai đoạn 1 (làm ngay), [P2] là Giai đoạn 2 (chỉ tạo file rỗng/stub có docstring, chưa cài đặt).

```
poultry-disease-warning/
├── docker-compose.yml                # [P1] db (PostGIS) + backend, có healthcheck
├── .env.example                      # [P1]
├── .gitignore                        # [P1]
├── README.md                         # [P1] hướng dẫn chạy, test, seed
├── backend/
│   ├── Dockerfile                    # [P1]
│   ├── requirements.txt              # [P1] ghim phiên bản
│   ├── pytest.ini                    # [P1] asyncio_mode = auto
│   ├── alembic.ini                   # [P1]
│   ├── alembic/
│   │   ├── env.py                    # [P1] cấu hình async + geoalchemy2
│   │   └── versions/                 # [P1] migration khởi tạo
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # [P1] FastAPI entry, lifespan gọi init_db
│   │   ├── core/
│   │   │   ├── config.py             # [P1] Settings đọc từ .env
│   │   │   ├── database.py           # [P1] async engine, session, get_db
│   │   │   └── security.py           # [P2] JWT, hash mật khẩu
│   │   ├── models/
│   │   │   ├── __init__.py           # [P1] import tất cả model cho Alembic
│   │   │   ├── base.py               # [P1] Base + mixin id/created_at/updated_at
│   │   │   ├── farm.py               # [P1]
│   │   │   ├── outbreak.py           # [P1]
│   │   │   ├── alert.py              # [P1]
│   │   │   └── user.py               # [P2]
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py             # [P1] Location, Page[T], PaginationParams
│   │   │   ├── farm.py               # [P1]
│   │   │   ├── outbreak.py           # [P1]
│   │   │   ├── alert.py              # [P1]
│   │   │   └── user.py               # [P2]
│   │   ├── api/
│   │   │   ├── deps.py               # [P1] get_db; [P2] get_current_user
│   │   │   └── v1/
│   │   │       ├── api.py            # [P1] gộp router, prefix /api/v1
│   │   │       └── endpoints/
│   │   │           ├── farms.py      # [P1]
│   │   │           ├── outbreaks.py  # [P1] gồm nearby-farms
│   │   │           ├── alerts.py     # [P1]
│   │   │           └── auth.py       # [P2]
│   │   ├── services/
│   │   │   ├── spatial_service.py        # [P1] ST_DWithin, khoảng cách
│   │   │   ├── alert_service.py          # [P1] sinh Alert từ ổ dịch
│   │   │   ├── notification_service.py   # [P1] interface + ConsoleNotifier; [P2] Email/SMS
│   │   │   └── crawler_service.py        # [P2]
│   │   ├── utils/
│   │   │   └── geo.py                # [P1] chuyển đổi lat/lon <-> WKB
│   │   └── db/
│   │       ├── init_db.py            # [P1] CREATE EXTENSION postgis
│   │       └── seed_data.py          # [P1] idempotent
│   └── tests/
│       ├── conftest.py               # [P1] DB test riêng, client, fixtures
│       ├── test_geo_utils.py         # [P1]
│       ├── test_farms.py             # [P1]
│       ├── test_outbreaks.py         # [P1]
│       ├── test_spatial.py           # [P1]
│       ├── test_alerts.py            # [P1]
│       └── test_auth.py              # [P2]
└── frontend/                         # [P2] ReactJS + Vite + Leaflet/MapLibre
```

# YÊU CẦU THỰC THI CHI TIẾT (GIAI ĐOẠN 1)

## 1. Docker và cấu hình

- `docker-compose.yml` có service `db`: image `postgis/postgis:15-3.3`, volume lưu dữ liệu, healthcheck bằng `pg_isready`, biến môi trường lấy từ `.env`.
- Thêm service `backend`: build từ `backend/Dockerfile`, `depends_on` db ở trạng thái `service_healthy`, chạy `alembic upgrade head` rồi `uvicorn`.
- `.env.example` gồm: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_TEST_DB`, `DATABASE_URL`, `TEST_DATABASE_URL`, `DEFAULT_ALERT_RADIUS_KM=5`.
- `core/config.py` dùng `pydantic-settings`.

## 2. Database (`core/database.py`, `db/init_db.py`)

- Tạo `AsyncEngine`, `async_sessionmaker(expire_on_commit=False)`, dependency `get_db`.
- Hàm `init_db()` chạy `CREATE EXTENSION IF NOT EXISTS postgis;` và được gọi trong lifespan của `main.py`.
- Dùng Alembic quản lý schema (tạo migration khởi tạo, chạy được với async engine). Enum Postgres phải được tạo đúng trong migration.

## 3. Models (SQLAlchemy 2.x + GeoAlchemy2)

Tất cả bảng có `id` (UUID, `default=uuid4`), `created_at`, `updated_at` (`DateTime(timezone=True)`).

### Farm

- `name` (String, bắt buộc), `owner_name`, `phone`, `email`
- `address`, `province`, `district`
- `poultry_type`: Enum (CHICKEN, DUCK, MUSCOVY, QUAIL, OTHER)
- `capacity`: Integer (số lượng gia cầm, >= 0)
- `is_active`: Boolean (mặc định True)
- `location`: `Geometry('POINT', srid=4326)`, có chỉ mục GiST (`spatial_index=True`)

### Outbreak

- `virus_type` (String, ví dụ H5N1, H5N6), `province`, `district`
- `location`: `Geometry('POINT', srid=4326)`, có chỉ mục GiST
- `cases_count`: Integer (số gia cầm mắc bệnh/tiêu hủy, >= 0)
- `status`: Enum (ACTIVE, CONTAINED, CLOSED)
- `severity`: Enum (LOW, MEDIUM, HIGH, CRITICAL)
- `radius_km`: Float (bán kính khoanh vùng, mặc định lấy từ config)
- `reported_date`: `DateTime(timezone=True)`
- Chỉ mục trên `status` và `virus_type`.

### Alert

- `outbreak_id` (FK, `ondelete=CASCADE`), `farm_id` (FK, `ondelete=CASCADE`)
- `distance_km`: Float
- `risk_level`: Enum (LOW, MEDIUM, HIGH, CRITICAL)
- `message`: Text
- `status`: Enum (PENDING, SENT, FAILED, ACKNOWLEDGED)
- `sent_at`: DateTime nullable
- Ràng buộc `UniqueConstraint(outbreak_id, farm_id)` để không tạo trùng cảnh báo.

## 4. Tiện ích địa lý (`utils/geo.py`), QUAN TRỌNG

Chỉ có một nơi duy nhất chuyển đổi tọa độ:

- `location_to_geometry(lat, lon)` dùng `shapely.Point(lon, lat)` rồi `from_shape(..., srid=4326)`. Thứ tự bắt buộc là (longitude, latitude).
- `geometry_to_location(geom)` dùng `to_shape` trả về `{"latitude": y, "longitude": x}`.
- Mọi nơi khác trong code phải gọi hai hàm này, không tự tạo WKT thủ công.

## 5. Pydantic Schemas

- `Location`: `latitude` (-90 đến 90), `longitude` (-180 đến 180).
- Mỗi thực thể có `Create`, `Update` (mọi trường optional), `Response` (`from_attributes=True`).
- Trường `location` trong request/response luôn là JSON `{"latitude": float, "longitude": float}`. Dùng `field_validator`/`model_validator` để convert sang và từ Geometry của GeoAlchemy2, không để lộ WKB/WKT ra API.
- `phone` validate định dạng số điện thoại Việt Nam (`^(0|\+84)\d{9}$`), `email` dùng `EmailStr`.
- `Page[T]`: `items`, `total`, `page`, `page_size`.

## 6. API Endpoints (prefix `/api/v1`)

Tất cả list endpoint hỗ trợ phân trang `page` (>= 1), `page_size` (1 đến 100, mặc định 20).

### /farms

- `POST /` (201), `GET /` (filter: province, district, poultry_type, is_active), `GET /{id}`, `PUT /{id}`, `DELETE /{id}` (204)
- ID không tồn tại trả 404; dữ liệu sai trả 422.

### /outbreaks

- `POST /`, `GET /` (filter: status, virus_type, province), `GET /{id}`, `PUT /{id}`, `DELETE /{id}`
- `GET /{id}/nearby-farms?radius_km=5`: trả danh sách trang trại trong bán kính kèm `distance_km`, sắp xếp gần đến xa.

### /alerts

- `POST /outbreaks/{outbreak_id}/generate`: quét trang trại trong bán kính của ổ dịch, tạo Alert (bỏ qua trang trại đã có Alert), trả danh sách Alert vừa tạo.
- `GET /` (filter: farm_id, outbreak_id, status, risk_level), `GET /{id}`, `PATCH /{id}/acknowledge`.

## 7. Services

- **spatial_service**: tìm trang trại trong bán kính bằng `ST_DWithin` trên kiểu geography (cast `geom::geography`, bán kính tính bằng mét = `radius_km * 1000`). Tính khoảng cách bằng `ST_Distance` cũng trên geography. Cấm dùng bán kính theo độ của SRID 4326.
- **alert_service**: gọi `spatial_service`, tính `risk_level` theo khoảng cách và severity, ví dụ: <= 1 km là CRITICAL, <= 3 km là HIGH, <= 5 km là MEDIUM, còn lại là LOW (ngưỡng đặt trong config). Chỉ tạo Alert khi ổ dịch có `status = ACTIVE`.
- **notification_service**: định nghĩa interface `Notifier` (`async send(alert, farm)`) và cài sẵn `ConsoleNotifier` (log ra console). Alert chuyển sang SENT khi gửi thành công, FAILED nếu lỗi. Email/SMS để Giai đoạn 2.

## 8. Seed data (`db/seed_data.py`)

- Chạy bằng `python -m app.db.seed_data`, idempotent (chạy nhiều lần không sinh trùng, ví dụ khóa theo tên trại/ổ dịch).
- 5 trang trại và 3 ổ dịch với tọa độ chính xác, phân bố như sau:
  - Trang trại: Đông Anh, Sóc Sơn, Gia Lâm (Hà Nội), Văn Giang (Hưng Yên), Yên Phong (Bắc Ninh).
  - Ổ dịch: một ổ gần Đông Anh/Sóc Sơn, một ổ ở Bắc Ninh, một ổ ở Hưng Yên, với các trạng thái ACTIVE/CONTAINED/CLOSED khác nhau.
- Bố trí sao cho ít nhất một trang trại nằm trong bán kính 5 km của một ổ dịch ACTIVE và ít nhất một trang trại nằm ngoài, để test cảnh báo có ý nghĩa.

## 9. Tiêu chí hoàn thành

- `docker compose up` chạy được db và backend, Swagger tại `/docs` hoạt động.
- Migration và seed chạy thành công, chạy seed lần hai không lỗi, không trùng.
- Toàn bộ test Giai đoạn 1 pass.
- `README.md` có hướng dẫn chạy, migrate, seed, test, và ví dụ gọi API cảnh báo.

# GIAI ĐOẠN 2 (CHỈ LÀM SAU KHI GIAI ĐOẠN 1 PASS)

- Auth JWT và phân quyền (ADMIN, VET_OFFICER, FARM_OWNER), ẩn SĐT/email chủ trại với người không có quyền.
- `notification_service`: gửi Email (SMTP), sau đó SMS/Zalo.
- Tự động sinh Alert khi tạo ổ dịch mới, chạy qua BackgroundTasks hoặc hàng đợi.
- `crawler_service`: lấy dữ liệu ổ dịch từ nguồn chính thống, chạy theo lịch (APScheduler).
- Frontend ReactJS + Vite + Leaflet: bản đồ ổ dịch, vòng bán kính nguy cơ, danh sách trang trại bị cảnh báo.

---

Ghi chú cho agent: chỉ tạo file theo cấu trúc, không chạy lệnh nào, không đọc file ngoài workspace.