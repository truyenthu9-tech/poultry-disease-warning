# Tiến độ

## Đã xong
- poultry-disease-warning/docker-compose.yml
- poultry-disease-warning/.env.example
- poultry-disease-warning/.gitignore
- poultry-disease-warning/backend/.gitignore
- poultry-disease-warning/backend/Dockerfile
- poultry-disease-warning/backend/requirements.txt
- poultry-disease-warning/backend/pytest.ini
- poultry-disease-warning/backend/alembic.ini
- poultry-disease-warning/backend/alembic/env.py
- poultry-disease-warning/backend/alembic/versions/ae01c4d0b231_init.py
- poultry-disease-warning/backend/app/core/config.py
- poultry-disease-warning/backend/app/core/database.py
- poultry-disease-warning/backend/app/core/security.py
- poultry-disease-warning/backend/app/utils/geo.py
- poultry-disease-warning/backend/app/models/base.py
- poultry-disease-warning/backend/app/models/user.py
- poultry-disease-warning/backend/app/models/farm.py
- poultry-disease-warning/backend/app/models/outbreak.py
- poultry-disease-warning/backend/app/models/alert.py
- poultry-disease-warning/backend/app/schemas/common.py
- poultry-disease-warning/backend/app/schemas/user.py
- poultry-disease-warning/backend/app/schemas/farm.py
- poultry-disease-warning/backend/app/schemas/outbreak.py
- poultry-disease-warning/backend/app/schemas/alert.py
- poultry-disease-warning/backend/app/api/deps.py
- poultry-disease-warning/backend/app/api/v1/api.py
- poultry-disease-warning/backend/app/api/v1/endpoints/auth.py
- poultry-disease-warning/backend/app/api/v1/endpoints/farms.py
- poultry-disease-warning/backend/app/api/v1/endpoints/outbreaks.py
- poultry-disease-warning/backend/app/api/v1/endpoints/alerts.py
- poultry-disease-warning/backend/app/services/spatial_service.py
- poultry-disease-warning/backend/app/services/alert_service.py
- poultry-disease-warning/backend/app/services/notification_service.py
- poultry-disease-warning/backend/app/services/crawler_service.py
- poultry-disease-warning/backend/app/db/init_db.py
- poultry-disease-warning/backend/app/db/seed_data.py
- poultry-disease-warning/backend/tests/conftest.py
- poultry-disease-warning/backend/tests/test_geo_utils.py
- poultry-disease-warning/backend/tests/test_farms.py
- poultry-disease-warning/backend/tests/test_outbreaks.py
- poultry-disease-warning/backend/app/__init__.py
- poultry-disease-warning/backend/app/main.py
- poultry-disease-warning/backend/app/models/__init__.py
- poultry-disease-warning/backend/app/schemas/__init__.py
- poultry-disease-warning/backend/app/api/v1/endpoints/README.md
- poultry-disease-warning/backend/tests/test_spatial.py
- poultry-disease-warning/backend/tests/test_alerts.py

## Cần viết lại
- (đã hoàn thành) poultry-disease-warning/README.md
- (đã hoàn thành) poultry-disease-warning/backend/tests/test_auth.py

## Đã xong
- poultry-disease-warning/frontend/package.json
- poultry-disease-warning/frontend/vite.config.js
- poultry-disease-warning/frontend/index.html
- poultry-disease-warning/frontend/.env.example
- poultry-disease-warning/frontend/src/main.jsx
- poultry-disease-warning/frontend/src/App.jsx
- poultry-disease-warning/frontend/src/App.css
- poultry-disease-warning/frontend/src/index.css
- poultry-disease-warning/frontend/src/api.js
- poultry-disease-warning/frontend/src/services/authService.js
- poultry-disease-warning/frontend/src/services/farmService.js
- poultry-disease-warning/frontend/src/services/outbreakService.js
- poultry-disease-warning/frontend/src/services/alertService.js
- poultry-disease-warning/frontend/src/components/Navbar.jsx
- poultry-disease-warning/frontend/src/components/Login.jsx
- poultry-disease-warning/frontend/src/components/Register.jsx
- poultry-disease-warning/frontend/src/pages/Dashboard.jsx
- poultry-disease-warning/frontend/src/pages/Farms.jsx
- poultry-disease-warning/frontend/src/pages/Outbreaks.jsx
- poultry-disease-warning/frontend/src/pages/Alerts.jsx

## Quy ước
- UUID làm khóa chính; enum Postgres tạo trong migration; mọi chuyển đổi tọa độ qua utils/geo.py (thứ tự lon, lat)
- Chỉ tạo đúng file có trong cấu trúc đề bài, không tạo thêm README hay file khác
