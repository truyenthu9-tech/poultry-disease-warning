# poultry-disease-warning

Hệ thống cảnh báo dịch bệnh gia cầm. Người dùng đăng ký trang trại, ghi nhận các ổ dịch, và hệ thống tự tìm những trang trại nằm trong bán kính nguy cơ của ổ dịch để tạo cảnh báo, gửi qua console và email. Dữ liệu mẫu nằm ở Hà Nội và các tỉnh lân cận.

## Công nghệ

- Backend: Python 3.11, FastAPI, SQLAlchemy 2.x async với asyncpg, GeoAlchemy2, Shapely, Pydantic v2, Alembic.
- Cơ sở dữ liệu: PostgreSQL 15 với PostGIS.
- Frontend: React 18, Vite, Leaflet và react-leaflet cho bản đồ.
- Xác thực bằng JWT, gửi email qua SMTP.

## Cấu trúc thư mục

```
poultry-disease-warning/
├── docker-compose.yml        # db PostGIS và backend
├── .env.example              # mẫu biến môi trường
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/              # migration, kiểu ENUM của Postgres tạo ở đây
│   ├── app/
│   │   ├── main.py           # điểm vào FastAPI
│   │   ├── core/             # config, database, security
│   │   ├── models/           # Farm, Outbreak, Alert, User, enums
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── api/v1/endpoints/ # auth, farms, outbreaks, alerts, geo_farms
│   │   ├── services/         # spatial, alert, notification, crawler
│   │   ├── utils/geo.py      # chuyển đổi tọa độ, thứ tự lon, lat
│   │   └── db/               # init_db và seed_data
│   └── tests/                # pytest, conftest.py dùng DB test riêng
└── frontend/
    └── src/
        ├── components/       # Navbar, Login, Register, AlertCard, MapView
        ├── pages/            # Dashboard, Farms, Outbreaks, MapPage, Alerts
        ├── services/         # gọi API theo từng nhóm
        └── apiClient.js      # fetch có gắn token
```

## Cách 1: chạy backend bằng Docker Compose

Docker Compose chạy database và backend. Frontend chạy riêng bằng npm ở bước sau.

```bash
cp .env.example .env
```

Mở `.env` và điền `JWT_SECRET_KEY`, bắt buộc, tối thiểu 32 ký tự. Tạo khóa bằng lệnh:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Nên đổi luôn `POSTGRES_PASSWORD` và đặt `SEED_ADMIN_PASSWORD`. Sau đó chạy:

```bash
docker compose up -d --build
```

Thiếu `JWT_SECRET_KEY` thì Compose dừng ngay và báo lỗi, không khởi động với khóa yếu. Khi khởi động, backend tự chạy `alembic upgrade head` để tạo bảng. Nạp dữ liệu mẫu một lần:

```bash
docker compose exec backend python -m app.db.seed_data
```

Lệnh này in ra email và mật khẩu của hai tài khoản mẫu, chỉ in một lần, nên hãy lưu lại.

Sau đó:

- API: http://localhost:8000
- Tài liệu API: http://localhost:8000/api/v1/docs
- Kiểm tra sống: http://localhost:8000/health, trả 200 khi database dùng được và 503 khi không
- PostgreSQL ra máy thật ở cổng 5433, tránh trùng với PostgreSQL cài sẵn ở cổng 5432.

## Cách 2: chạy thủ công

Cần Python 3.11 trở lên và một PostgreSQL có PostGIS. Có thể dùng luôn container `db` của Compose bằng `docker compose up -d db`.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux, macOS
pip install -r requirements.txt
```

Tạo file `backend/.env` trỏ tới database ở máy thật:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/poultry_disease
```

Có thể thêm `JWT_SECRET_KEY` vào file này. Để trống thì khi chạy dev, backend tự sinh khóa ngẫu nhiên và token cũ mất hiệu lực mỗi lần khởi động lại. Khi triển khai thật phải đặt `APP_ENV=production` cùng một `JWT_SECRET_KEY` cố định, nếu không backend từ chối khởi động.

Rồi chạy migration, nạp dữ liệu mẫu và bật server:

```bash
alembic upgrade head
python -m app.db.seed_data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Trên Windows có thể chạy nhanh bằng `backend\run_backend.bat`, file này kích hoạt `.venv` rồi bật uvicorn.

## Chạy frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Mở http://localhost:5173. Địa chỉ API lấy từ `VITE_API_BASE_URL` trong `frontend/.env`, mặc định là `http://127.0.0.1:8000/api/v1`. Backend cho phép CORS từ `localhost:5173` và `127.0.0.1:5173`.

## Tài khoản và phân quyền

Mọi API nghiệp vụ đều yêu cầu đăng nhập. Có bốn vai trò, trong đó admin và vet_officer được coi là nhân viên:

| Quyền | Người dùng thường | Cán bộ thú y | Quản trị viên |
| --- | --- | --- | --- |
| Xem trang trại, ổ dịch, bản đồ | có | có | có |
| Xem và xác nhận đã biết cảnh báo | chỉ cảnh báo của trang trại gán cho tài khoản mình | tất cả | tất cả |
| Thấy tên chủ trại, điện thoại, email, địa chỉ | chỉ trang trại của mình | có | có |
| Thêm, sửa, xóa trang trại và ổ dịch, gán chủ trại, tạo cảnh báo | không | có | có |
| Xác nhận ổ dịch nhập từ nguồn bên ngoài, bấm nhập dữ liệu | không | có | có |
| Xem danh sách tài khoản và đổi vai trò | không | không | có |

**Trang trại thuộc về tài khoản nào.** Mỗi trang trại có thể gán cho một tài khoản (cột `farms.owner_user_id`). Admin hoặc cán bộ thú y gán bằng cách nhập email tài khoản đã đăng ký vào trường `owner_user_email` khi tạo hoặc sửa trang trại (trên giao diện là ô "Email tài khoản chủ trại"). Người dùng không phải nhân viên chỉ liệt kê, xem chi tiết và xác nhận được cảnh báo của trang trại gán cho mình. Cảnh báo của trang trại khác, hoặc của trang trại chưa gán chủ, trả về 404 như không tồn tại. `GET /farms?mine=true` liệt kê trang trại của chính mình. Bỏ gán bằng cách gửi `owner_user_email: null`. Tài khoản chưa được gán trang trại nào sẽ không thấy cảnh báo nào.

Đăng ký công khai luôn tạo tài khoản người dùng thường, không chọn được vai trò. Tài khoản admin đầu tiên do lệnh seed tạo, mật khẩu lấy từ `SEED_ADMIN_PASSWORD` hoặc được sinh ngẫu nhiên và in ra. Admin cấp quyền cho người khác bằng `PUT /api/v1/auth/users/{id}/role`, và không thể tự đổi vai trò của chính mình. Lấy id tài khoản bằng `GET /api/v1/auth/users`.

## Cách dùng

1. Đăng nhập bằng tài khoản admin hoặc cán bộ thú y, vào Trang trại và thêm trang trại. Bấm lên bản đồ để chọn vị trí, vĩ độ và kinh độ sẽ tự điền. Nhập email của chủ trại nếu muốn nhận cảnh báo qua email, và nhập email tài khoản của chủ trại để họ xem được cảnh báo trên hệ thống.
2. Vào Bùng phát, thêm ổ dịch với bán kính cảnh báo, rồi bấm Tạo cảnh báo ở ổ dịch đang hoạt động. Ổ dịch do cán bộ nhập tay được coi là đã xác nhận. Ổ dịch nhập từ nguồn bên ngoài ở trạng thái Chưa xác nhận, cán bộ phải kiểm tra rồi bấm Xác nhận thì mới tạo được cảnh báo.
3. Hệ thống tạo cảnh báo cho mọi trang trại trong bán kính. Mức nguy cơ lấy theo khoảng cách (trong 1 km là nghiêm trọng, trong 3 km là cao, trong 5 km là trung bình, xa hơn là thấp), rồi nâng lên nếu ổ dịch có mức độ cao: ổ dịch mức Cao thì trang trại trong bán kính không thấp hơn Trung bình, mức Nghiêm trọng thì không thấp hơn Cao. Mức độ ổ dịch chỉ nâng mức, không bao giờ hạ mức. Mỗi cảnh báo lưu cơ sở đánh giá (trường `risk_basis`) và hiển thị trên giao diện. Mỗi cặp ổ dịch và trang trại chỉ có một cảnh báo.
4. Trang Bản đồ hiển thị trang trại bằng chấm xanh, ổ dịch bằng chấm đỏ cùng vòng tròn bán kính. Bấm vào từng chấm để xem chi tiết.
5. Trang Thông báo liệt kê cảnh báo và cho phép xác nhận đã biết.

## Nguồn dữ liệu ổ dịch (crawler)

Hệ thống không gắn sẵn với website nào. Muốn nhập ổ dịch tự động, người vận hành đặt `OUTBREAK_FEED_URLS` trỏ tới nguồn dữ liệu mà mình tin cậy và có quyền dùng (nhiều nguồn thì cách nhau bằng dấu phẩy). Nguồn phải trả JSON là một mảng, hoặc `{"items": [...]}`, mỗi phần tử có `external_id`, `virus_type`, `province`, `latitude`, `longitude`, và tùy chọn `district`, `address`, `cases_count`, `reported_date`, `source_url`, `status`. Mô tả đầy đủ ở đầu file `backend/app/services/crawler_service.py`.

- Chưa đặt `OUTBREAK_FEED_URLS` thì không nhập gì, nút Nhập từ nguồn dữ liệu báo là chưa cấu hình nguồn.
- Cán bộ bấm Nhập từ nguồn dữ liệu (`POST /api/v1/outbreaks/import`), hoặc đặt `OUTBREAK_CRAWL_INTERVAL_MINUTES` lớn hơn 0 để nhập theo chu kỳ khi backend chạy.
- Bản ghi nhập về luôn ở trạng thái chưa xác nhận, mức độ mặc định là Trung bình. Cán bộ kiểm tra, chỉnh mức độ và bán kính nếu cần, rồi bấm Xác nhận (`POST /api/v1/outbreaks/{id}/verify`). Chỉ khi đó mới tạo được cảnh báo. Hệ thống không bao giờ tự tạo hay tự gửi cảnh báo từ dữ liệu nhập về.
- Bản ghi trùng (cùng nguồn và `external_id`) bị bỏ qua, bản ghi sai định dạng được đếm và báo lại, một nguồn lỗi không chặn các nguồn khác.
- Nếu chạy nhiều tiến trình backend cùng bật chu kỳ nhập thì mỗi tiến trình sẽ tự nhập, dữ liệu vẫn không bị trùng nhờ ràng buộc duy nhất trong database.

## Giới hạn của hệ thống cảnh báo

Đây là công cụ cảnh báo tham khảo, chưa phải hệ thống giám sát dịch tễ. Mức nguy cơ chỉ dựa trên khoảng cách và mức độ ổ dịch do cán bộ nhập. Hệ thống chưa xét hướng gió, đường vận chuyển, loài gia cầm, tình trạng tiêm phòng và các yếu tố dịch tễ khác. Các ngưỡng 1, 3, 5 km và quy tắc nâng mức là giá trị mặc định, cần cơ quan thú y có thẩm quyền rà soát trước khi dùng cho trang trại thật. Email và giao diện đều ghi rõ cảnh báo chỉ mang tính tham khảo.

## Gửi email cảnh báo

Mặc định chỉ in cảnh báo ra console. Để gửi email thật tới những trang trại có điền email, đặt trong `.env`:

```
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tai-khoan@gmail.com
SMTP_PASSWORD=mat-khau-ung-dung
SMTP_FROM=tai-khoan@gmail.com
SMTP_USE_TLS=true
```

Với Gmail cần bật xác minh hai bước và tạo Mật khẩu ứng dụng, không dùng mật khẩu đăng nhập thường. Cổng 465 thì đặt `SMTP_USE_SSL=true` và `SMTP_USE_TLS=false`. Trang trại không có email sẽ được bỏ qua. Nếu gửi email lỗi thì cảnh báo đó có trạng thái Gửi lỗi, các kênh khác vẫn chạy bình thường.

## API chính

Tiền tố `/api/v1`. Trừ đăng ký, đăng nhập và health check, mọi route đều cần header `Authorization: Bearer <token>`. Các thao tác ghi cần vai trò admin hoặc vet_officer.

| Phương thức | Đường dẫn | Mô tả |
| --- | --- | --- |
| POST | /auth/register | Đăng ký |
| POST | /auth/login | Đăng nhập, trả về token và thông tin người dùng |
| GET, PUT | /auth/me | Xem và sửa tài khoản hiện tại |
| GET | /auth/users | Danh sách tài khoản, chỉ admin |
| PUT | /auth/users/{id}/role | Đổi vai trò, chỉ admin |
| GET, POST | /farms | Danh sách (lọc `mine=true` để chỉ lấy trang trại của mình) và tạo trang trại |
| GET, PUT, DELETE | /farms/{id} | Xem, sửa, xóa trang trại |
| GET, POST | /outbreaks | Danh sách (lọc `verified=true` hoặc `false`) và tạo ổ dịch |
| POST | /outbreaks/import | Nhập ổ dịch từ nguồn đã cấu hình, bản ghi mới chưa xác nhận |
| POST | /outbreaks/{id}/verify | Cán bộ xác nhận ổ dịch |
| GET, PUT, DELETE | /outbreaks/{id} | Xem, sửa, xóa ổ dịch |
| GET | /outbreaks/{id}/nearby-farms | Trang trại trong bán kính của ổ dịch |
| POST | /geo/farms/around | Trang trại quanh một tọa độ |
| POST | /alerts/outbreaks/{id}/generate | Tạo cảnh báo cho một ổ dịch |
| GET, POST | /alerts | Danh sách và tạo cảnh báo. Người dùng thường chỉ thấy cảnh báo của trang trại mình |
| GET, PUT, DELETE | /alerts/{id} | Xem, sửa, xóa cảnh báo. Người dùng thường chỉ xem được cảnh báo của trang trại mình |
| PATCH | /alerts/{id}/acknowledge | Xác nhận đã biết. Người dùng thường chỉ xác nhận được cảnh báo của trang trại mình |

Ngoài ra có `GET /health` và `GET /`. Toàn bộ chi tiết xem ở trang `/api/v1/docs`.

## Biến môi trường backend

Đọc từ môi trường hoặc từ file `.env` ở thư mục gốc và `backend/.env`, file sau ghi đè file trước.

| Biến | Ý nghĩa | Mặc định |
| --- | --- | --- |
| DATABASE_URL | Kết nối database chính | postgresql+asyncpg://postgres:postgres@localhost:5432/poultry_disease |
| TEST_DATABASE_URL | Kết nối database cho pytest | postgresql+asyncpg://postgres:postgres@localhost:5432/poultry_disease_test |
| DEFAULT_ALERT_RADIUS_KM | Bán kính cảnh báo mặc định | 5.0 |
| RISK_CRITICAL_KM, RISK_HIGH_KM, RISK_MEDIUM_KM | Ngưỡng khoảng cách của từng mức nguy cơ | 1, 3, 5 |
| APP_ENV | development hoặc production, Dockerfile đặt production | development |
| JWT_SECRET_KEY | Khóa ký JWT, tối thiểu 32 ký tự, bắt buộc khi production | trống, dev tự sinh ngẫu nhiên |
| SEED_ADMIN_PASSWORD, SEED_USER_PASSWORD | Mật khẩu tài khoản mẫu khi seed | trống, seed tự sinh và in ra |
| JWT_TOKEN_EXPIRE_MINUTES | Thời hạn token | 60 |
| BACKEND_CORS_ORIGINS | Các origin được phép, ngăn cách bằng dấu phẩy | http://localhost:5173,http://127.0.0.1:5173 |
| OUTBREAK_FEED_URLS | Danh sách URL nguồn dữ liệu ổ dịch, cách nhau bằng dấu phẩy, chỉ http hoặc https | trống, không nhập gì |
| OUTBREAK_CRAWL_INTERVAL_MINUTES | Chu kỳ tự nhập dữ liệu (phút), 0 là tắt | 0 |
| OUTBREAK_FEED_TIMEOUT, OUTBREAK_FEED_MAX_BYTES | Thời gian chờ (giây) và dung lượng tối đa của một nguồn | 15, 2000000 |
| EMAIL_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_FROM_NAME, SMTP_USE_TLS, SMTP_USE_SSL, SMTP_TIMEOUT | Gửi email, xem mục trên | tắt |

Biến môi trường của frontend nằm ở `frontend/.env.example`.

## Chạy test

Test cần một PostgreSQL có PostGIS và tài khoản có quyền tạo database. Trỏ `TEST_DATABASE_URL` tới đó, ví dụ dùng container `db` của Compose:

```bash
cd backend
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/poultry_disease_test
pytest
```

File `tests/conftest.py` tự tạo database test, chạy `alembic upgrade head` và xóa sạch dữ liệu sau mỗi test, nên không ảnh hưởng database chính. Nếu không kết nối được PostgreSQL thì các test cần database sẽ được bỏ qua. Các file `test_alert_access.py`, `test_risk_and_import.py` và `test_security.py` viết theo code hiện tại. Các file `test_*.py` còn lại (alerts, farms, outbreaks, spatial, migrations...) vẫn viết theo model cũ, dùng fixture không còn trong `conftest.py`, nên cần cập nhật trước khi chạy đủ bộ test. Riêng `test_alerts.py` còn giả định mức nguy cơ chỉ theo khoảng cách, cần sửa theo quy tắc nâng mức ở trên.

## Lưu ý kỹ thuật

- Khóa chính là UUID. Kiểu ENUM của Postgres được tạo trong migration, không phải bởi `create_all`.
- Mọi chuyển đổi tọa độ đi qua `backend/app/utils/geo.py` và dùng thứ tự kinh độ rồi vĩ độ.
- Truy vấn khoảng cách dùng PostGIS, cột vị trí có chỉ mục GiST.
- Không commit file `.env` chứa mật khẩu thật lên git, và xóa `backend/.env` khỏi bản nộp.
- Thông tin liên hệ của trang trại được lọc ở backend theo vai trò, không chỉ ẩn ở giao diện.
- Chưa có giới hạn số lần đăng nhập sai. Nên bổ sung trước khi mở cho người dùng thật.
- Quyền xem cảnh báo dựa trên `farms.owner_user_id`. Trang trại chưa gán tài khoản thì chỉ nhân viên thấy cảnh báo của nó.
