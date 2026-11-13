# Audit Report: poultry-disease-warning Project

**Project:** Poultry Disease Warning System  
**Auditor:** Senior Software Architect & Independent Code Auditor  
**Date:** 2025  
**Scope:** Static read-only audit against `SPEC.md` requirements  
**Stack:** Python 3.11, FastAPI, SQLAlchemy 2.x async, asyncpg, GeoAlchemy2, Shapely, Pydantic v2, Alembic, PostgreSQL 15+PostGIS

---

## Executive Summary

The codebase demonstrates **significant architectural deviations** from `SPEC.md` requirements. The most critical finding is a **fundamental async/sync mismatch**: the specification mandates SQLAlchemy 2.x async with asyncpg, but the entire implementation uses synchronous `Session` (sqlalchemy.orm.Session) throughout all endpoints, services, and database initialization. Additional critical issues include authentication implementation despite being Phase 2 (stub-only per spec), broken spatial query logic in alerts, enum mismatches, duplicate Location schemas, and inconsistent primary key types.

**Overall Verdict:** **FAIL** — Does not meet Phase 1 acceptance criteria. Requires substantial rework before production readiness.

---

## Severity Classification

| Severity | Definition |
|----------|------------|
| 🔴 **CRITICAL** | Architecture violation, security vulnerability, data integrity risk, or spec non-compliance blocking Phase 1 delivery |
| 🟠 **HIGH** | Major functional defect, incorrect logic, or missing required feature |
| 🟡 **MEDIUM** | Code quality issue, inconsistency, or technical debt that impedes maintainability |
| 🟢 **LOW** | Minor style, documentation, or optimization opportunity |

---

## Critical Findings (🔴 CRITICAL)

### 1. Fundamental Async/Sync Architecture Mismatch
**Files:** All API endpoints, services, database modules  
**Lines:** Pervasive  
**Spec Reference:** SPEC.md §Stack (SQLAlchemy 2.x async, asyncpg), §P10, §P14

**Evidence:**
- `backend/app/core/database.py:1-50` — Defines `async_engine`, `AsyncSessionLocal`, async `get_db` dependency
- `backend/app/db/init_db.py:1-44` — Creates **sync** engine (`create_engine`) and `SessionLocal` (sync sessionmaker)
- `backend/app/api/deps.py:1-45` — `get_current_user` uses `Session = Depends(get_db)` where `get_db` yields sync `Session`
- **All endpoints** (`farms.py`, `outbreaks.py`, `alerts.py`, `auth.py`, `geo_farms.py`) use `db: Session = Depends(get_db)` with sync `Session`
- `backend/app/services/spatial_service.py:1-85` — Uses sync `Session`
- `backend/app/services/alert_service.py:1-120` — Uses sync `Session`
- Tests in `conftest.py:22-27` use `app.db.init_db.SessionLocal` (sync)

**Impact:** The async database layer defined in `core/database.py` is completely bypassed. The application runs synchronously, defeating the purpose of asyncpg and FastAPI's async capabilities. This will cause severe performance bottlenecks under load.

**Recommendation:** 
1. Remove `backend/app/db/init_db.py` entirely or convert to async
2. Update all endpoints to use `AsyncSession` from `core.database`
3. Convert all service methods to `async def` with `await db.execute()`
4. Update `conftest.py` to use async test fixtures
5. Ensure Alembic migrations work with async engine

---

### 2. Authentication Implemented Despite Phase 2 Specification
**Files:** `backend/app/api/v1/endpoints/auth.py`, `backend/app/core/security.py`, `backend/app/schemas/user.py`, `backend/app/models/user.py`  
**Lines:** Full implementations  
**Spec Reference:** SPEC.md §Phase 1/2 split — "P2: stubs only" for auth

**Evidence:**
- `auth.py:1-185` — Full JWT register/login/me/update-me implementation with bcrypt
- `security.py:1-65` — Complete `pwd_context`, JWT encoding/decoding, OAuth2PasswordBearer
- `user.py:1-70` — User model with password_hash, role, full auth fields
- `schemas/user.py:1-65` — UserCreate, UserUpdate, UserResponse, Token schemas

**Impact:** Scope creep — implementation effort spent on Phase 2 feature. Creates maintenance burden and potential security surface before required.

**Recommendation:** 
1. Per spec, reduce `auth.py` to stub endpoints returning 501 Not Implemented
2. Keep `security.py` for future use but document as Phase 2
3. Mark User model and schemas as Phase 2 in code comments

---

### 3. Broken Spatial Distance Logic in Alert Creation
**File:** `backend/app/api/v1/endpoints/alerts.py`  
**Lines:** 82-85  
**Spec Reference:** SPEC.md §Alert model, §P13 (alerts logic)

**Evidence:**
```python
# Line 82-85 in alerts.py
farm = db.query(Outbreak).filter(Outbreak.id == alert_in.farm_id).first()  # BUG: queries Outbreak not Farm
if not farm:
    raise HTTPException(status_code=404, detail="Farm not found")
farm_location = func.ST_SetSRID(func.ST_MakePoint(farm.longitude, farm.latitude), 4326)
```

**Impact:** 
- Queries `Outbreak` table using `farm_id` — wrong table entirely
- `Outbreak` model has no `longitude`/`latitude` columns (uses `location` Geometry)
- Will raise AttributeError or return incorrect data
- Alert distance calculation completely broken

**Recommendation:** 
1. Change query to `db.query(Farm).filter(Farm.id == alert_in.farm_id).first()`
2. Use `farm.location` (Geometry) with PostGIS functions for distance calculation
3. Leverage `spatial_service.find_farms_within_radius` for consistency

---

### 4. Enum Mismatches Between Models and Seed Data
**Files:** `backend/app/db/seed_data.py`, `backend/app/models/enums.py`, `backend/app/models/farm.py`, `backend/app/models/outbreak.py`, `backend/app/models/alert.py`  
**Lines:** seed_data.py imports vs model definitions  
**Spec Reference:** SPEC.md §Models, §P15 (seed data)

**Evidence:**
- `seed_data.py:5` imports: `AlertSeverity`, `AlertStatus`, `FarmStatus`, `FarmType`, `Disease`, `OutbreakStatus`
- `models/enums.py:1-50` defines: `PoultryTypeEnum`, `OutbreakStatusEnum`, `SeverityLevelEnum`, `RiskLevelEnum`, `AlertStatusEnum`
- **Mismatches:**
  - `FarmType` vs `PoultryTypeEnum` (values: `broiler`/`layer` vs `BROILER`/`LAYER`)
  - `FarmStatus` vs not defined in models (Farm uses `is_active` Boolean)
  - `Disease` vs not defined (Outbreak uses `virus_type` String)
  - `OutbreakStatus` vs `OutbreakStatusEnum`
  - `AlertSeverity` vs `RiskLevelEnum` / `SeverityLevelEnum` confusion
  - `AlertStatus` vs `AlertStatusEnum`

**Impact:** Seed script will fail with ImportError. Enum value mismatches cause data integrity issues.

**Recommendation:** 
1. Align seed_data.py imports with actual model enums
2. Use `PoultryTypeEnum.BROILER` not `"broiler"` strings
3. Remove references to non-existent enums (`FarmStatus`, `FarmType`, `Disease`, `AlertSeverity`)
4. Map `OutbreakStatusEnum`, `AlertStatusEnum`, `RiskLevelEnum`, `SeverityLevelEnum` correctly

---

### 5. Inconsistent Primary Key Types Across Models
**Files:** `backend/app/models/farm.py`, `backend/app/models/outbreak.py`, `backend/app/models/alert.py`, `backend/app/models/user.py`  
**Lines:** Primary key definitions  
**Spec Reference:** SPEC.md §Models — "UUID làm khóa chính"

**Evidence:**
- `farm.py:18` — `id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- `outbreak.py:18` — `id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))`
- `alert.py:18` — `id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))`
- `user.py:18` — `id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`

**Impact:** 
- Farm/User use native UUID type; Outbreak/Alert use String(36)
- Foreign key relationships may have type coercion issues
- Migration complexity increased
- Inconsistent API responses (some UUID objects, some strings)

**Recommendation:** Standardize all primary keys to `UUID(as_uuid=True)` with `default=uuid.uuid4` (matching Farm/User pattern).

---

### 6. Alert Unique Constraint Allows Multiple NULL farm_id Per Outbreak
**File:** `backend/app/models/alert.py`  
**Lines:** 35-36, 42  
**Spec Reference:** SPEC.md §Alert model — idempotency via unique constraint

**Evidence:**
```python
farm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    UUID(as_uuid=True), ForeignKey("farm.id"), nullable=True  # Line 35
)
# ...
__table_args__ = (
    UniqueConstraint("outbreak_id", "farm_id", name="uq_outbreak_farm"),  # Line 42
)
```

**Impact:** PostgreSQL treats NULL ≠ NULL in unique constraints. Multiple alerts for the same outbreak with `farm_id=NULL` will be allowed, breaking idempotency for outbreak-level alerts.

**Recommendation:** 
1. Make `farm_id` non-nullable if every alert must target a farm
2. Or use partial unique index: `UniqueConstraint("outbreak_id", "farm_id", name="uq_outbreak_farm").where(farm_id.isnot(None))`
3. Or add a separate `outbreak_only_alert` boolean flag with conditional unique constraint

---

### 7. Alert.risk_level Uses String Instead of Enum
**File:** `backend/app/models/alert.py`  
**Lines:** 38-39  
**Spec Reference:** SPEC.md §Alert model — risk_level enum

**Evidence:**
```python
risk_level: Mapped[str] = mapped_column(String(50), nullable=False)  # Line 38
# vs status column:
status: Mapped[AlertStatusEnum] = mapped_column(
    Enum(AlertStatusEnum, name="alert_status_enum", native_enum=False), 
    default=AlertStatusEnum.PENDING
)  # Line 40-42
```

**Impact:** No database-level validation of risk_level values. Application must enforce enum values. Inconsistent with `status` column pattern.

**Recommendation:** Change to `Enum(RiskLevelEnum, name="risk_level_enum", native_enum=False)`.

---

### 8. Location Schema Duplicated in 4 Files
**Files:** `backend/app/schemas/common.py`, `backend/app/schemas/farm.py`, `backend/app/schemas/outbreak.py`, `backend/app/schemas/alert.py`  
**Lines:** Various  
**Spec Reference:** SPEC.md §Schemas — single source of truth

**Evidence:**
- `common.py:8-15` — `Location` class (lat/lon with validation)
- `farm.py:21-30` — Duplicate `Location` class (lines 21-30)
- `outbreak.py:8-12` — Duplicate `Location` class (lines 8-12)
- `alert.py:8-16` — Duplicate `Location` class (lines 8-16)

**Impact:** Maintenance burden, validation inconsistency risk, violates DRY principle.

**Recommendation:** Remove duplicates from farm.py, outbreak.py, alert.py; import from `common.py`.

---

### 9. FarmTypeEnum Defined as BaseModel Instead of StrEnum
**File:** `backend/app/schemas/farm.py`  
**Lines:** 32-37  
**Spec Reference:** SPEC.md §Schemas — enum validation

**Evidence:**
```python
class FarmTypeEnum(BaseModel):  # Line 32
    """Enum loại trang trại."""
    BROILER: str = "broiler"
    LAYER: str = "layer"
```

**Impact:** Pydantic cannot validate against this. Should be `StrEnum` or `Enum` for proper validation.

**Recommendation:** 
```python
from enum import StrEnum
class FarmTypeEnum(StrEnum):
    BROILER = "broiler"
    LAYER = "layer"
```

---

### 10. Missing Schema Exports Required by Spec
**File:** `backend/app/schemas/__init__.py`  
**Lines:** 1-20  
**Spec Reference:** SPEC.md §Schemas — listed exports

**Evidence:** Spec requires exports for:
- `OutbreakNearbyFarmsResponse`
- `UserAlertsResponse`
- `AlertAcknowledge`
- `FarmNearbyQuery`
- `FarmNearbyResponse`

None of these exist in the codebase.

**Recommendation:** Implement missing schemas per spec requirements.

---

### 11. get_current_user Raises RuntimeError Instead of HTTPException
**File:** `backend/app/api/deps.py`  
**Lines:** 35-45  
**Spec Reference:** SPEC.md §Auth — proper error handling

**Evidence:**
```python
def get_current_user(
    user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise RuntimeError("User not found")  # Line 41 - should be HTTPException 404
    if not user.is_active:
        raise RuntimeError("Inactive user")    # Line 43 - should be HTTPException 403
    return user
```

**Impact:** Returns 500 Internal Server Error instead of proper 401/403/404. Breaks API contract.

**Recommendation:** Import and raise `HTTPException` with appropriate status codes.

---

### 12. auth.py Redefines pwd_context Despite Importing from security.py
**File:** `backend/app/api/v1/endpoints/auth.py`  
**Lines:** 11-12, 15  
**Spec Reference:** Code quality — duplication

**Evidence:**
```python
from app.core.security import pwd_context, create_access_token  # Line 11
# ...
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Line 15 - REDEFINES
```

**Impact:** Two different `pwd_context` instances. Passwords hashed in auth.py won't verify with security.py's context (though currently both use bcrypt defaults).

**Recommendation:** Remove redefinition; use imported `pwd_context`.

---

### 13. Migration Uses Geography But Models Use Geometry
**File:** `backend/alembic/versions/ae01c4d0b231_init.py` vs `backend/app/models/farm.py`, `outbreak.py`  
**Lines:** Migration lines 60, 85, 110 vs model definitions  
**Spec Reference:** SPEC.md §Models — PostGIS Geometry(POINT, 4326)

**Evidence:**
- Migration: `sa.Column("location", Geography(geometry_type="POINT", srid=4326))`
- Models: `Mapped[Geometry] = mapped_column(Geometry(geometry_type="POINT", srid=4326))`

**Impact:** Type mismatch between database (Geography) and ORM (Geometry). ST_DWithin behavior differs (meters vs degrees). Query errors likely.

**Recommendation:** Align migration to use `Geometry(geometry_type="POINT", srid=4326)` to match models, OR change models to Geography. Spec says Geometry.

---

### 14. User.password Column Uses Undefined PASSWORD_LENGTH
**File:** `backend/app/models/user.py`  
**Lines:** 24  
**Spec Reference:** SPEC.md §Models

**Evidence:**
```python
password_hash: Mapped[str] = mapped_column(String(settings.PASSWORD_LENGTH), nullable=False)
```

`config.py` has no `PASSWORD_LENGTH` setting.

**Impact:** Runtime AttributeError when model loads.

**Recommendation:** Use fixed length (e.g., `String(255)` for bcrypt hashes) or add setting to config.

---

### 15. UserRole Enum Mismatch: FARMER vs ADMIN/USER
**Files:** `backend/app/models/enums.py`, `backend/app/core/security.py`, `backend/app/schemas/user.py`  
**Lines:** Various  
**Spec Reference:** SPEC.md §Models — UserRole enum

**Evidence:**
- `enums.py:48-50` — `UserRole` enum with `ADMIN = "admin"`, `USER = "user"`
- `security.py:22` — References `UserRole.FARMER` (doesn't exist)
- `schemas/user.py:25` — `role: UserRole = Field(default=UserRole.USER)` but validation expects "farmer"

**Impact:** Security module references non-existent enum value. Schema validation will reject valid roles.

**Recommendation:** Align enum values across all files. Spec mentions "farmer" role — update `UserRole` enum to include `FARMER = "farmer"`.

---

## High Severity Findings (🟠 HIGH)

### 16. geo_farms.py Endpoint Exists But Not In Spec; outbreaks.py Missing nearby-farms
**Files:** `backend/app/api/v1/endpoints/geo_farms.py`, `backend/app/api/v1/endpoints/outbreaks.py`  
**Spec Reference:** SPEC.md §API endpoints table

**Evidence:**
- Spec lists outbreaks endpoints including "nearby-farms" under outbreaks
- `geo_farms.py` implements `POST /geo/farms/around` — not in spec
- `outbreaks.py` has no nearby-farms endpoint

**Impact:** API structure doesn't match spec. Frontend integration will fail.

**Recommendation:** 
1. Move nearby-farms logic to `outbreaks.py` as `GET /api/v1/outbreaks/{id}/nearby-farms`
2. Remove or deprecate `geo_farms.py` router
3. Update `api.py` router registration

---

### 17. spatial_service Uses Sync Session Despite Async Core
**File:** `backend/app/services/spatial_service.py`  
**Lines:** 1-85  
**Spec Reference:** SPEC.md §Services

**Evidence:** All methods use `db: Session` (sync) and `db.execute()` without await.

**Impact:** Blocks event loop during spatial queries. Defeats async architecture.

**Recommendation:** Convert to async with `AsyncSession` and `await db.execute()`.

---

### 18. alert_service Incomplete Risk Logic and Sync Session
**File:** `backend/app/services/alert_service.py`  
**Lines:** 1-120  
**Spec Reference:** SPEC.md §P13 (alerts logic), §Services

**Evidence:**
- `generate_alerts_for_outbreak` has `TODO: implement risk logic` comment (line 67)
- Uses sync `Session`
- Distance calculation uses raw SQL with `ST_Distance` but doesn't convert to km properly
- Risk level assignment is placeholder

**Impact:** Alert generation produces incorrect risk levels. Core business logic incomplete.

**Recommendation:** 
1. Convert to async
2. Implement proper risk calculation based on distance and outbreak severity
3. Use `spatial_service` for distance queries
4. Add unit tests for risk logic

---

### 19. init_db.py Uses Sync Engine — Conflicts with Async Core
**File:** `backend/app/db/init_db.py`  
**Lines:** 1-44  
**Spec Reference:** SPEC.md §P14 (init_db), §P10 (deps)

**Evidence:** Creates sync engine, sync sessionmaker, calls `Base.metadata.drop_all/create_all` synchronously.

**Impact:** Database initialization runs sync; cannot be used in async lifespan. Conflicts with `core/database.py` async pattern.

**Recommendation:** Remove or convert to async. Use `core/database.py` async engine for initialization.

---

### 20. Seed Data Script Will Fail — Multiple Issues
**File:** `backend/app/db/seed_data.py`  
**Lines:** 1-100  
**Spec Reference:** SPEC.md §P15 (seed data)

**Evidence:**
- Enum import mismatches (Finding #4)
- Creates `User` with `role=UserRole.ADMIN` but `UserRole` enum has no `FARMER` (Finding #15)
- Uses `FarmStatus.ACTIVE` but Farm model has `is_active` Boolean
- Uses `FarmType.BROILER` but model uses `PoultryTypeEnum`
- Uses `Disease.NEWTONS` but Outbreak uses `virus_type` String
- Uses `OutbreakStatus.CONFIRMED` but model uses `OutbreakStatusEnum`

**Impact:** Seed script completely non-functional.

**Recommendation:** Rewrite seed_data.py to match actual model definitions and enums.

---

### 21. Tests Use Sync Sessions But Spec Requires Async
**Files:** `backend/tests/conftest.py`, all test files  
**Lines:** Pervasive  
**Spec Reference:** SPEC.md §Tests, §P10

**Evidence:** 
- `conftest.py:22-27` uses `app.db.init_db.SessionLocal` (sync)
- Tests use `sqlalchemy.orm.Session` type hints
- `test_alerts.py` uses `AsyncSession` and `pytest.mark.asyncio` — **inconsistent** with other tests

**Impact:** Test suite doesn't validate async implementation. Mixed patterns indicate confusion.

**Recommendation:** Standardize all tests on async with `AsyncSession` and `pytest-asyncio`.

---

### 22. Docker Healthcheck Uses /health But No Explicit Health Endpoint Test
**Files:** `docker-compose.yml`, `backend/app/main.py`  
**Lines:** compose.yml:15, main.py:45  
**Spec Reference:** SPEC.md §Docker compose healthcheck

**Evidence:** 
- `docker-compose.yml:15` — `test: ["CMD", "curl", "-f", "http://localhost:8000/health"]`
- `main.py:45` — `@app.get("/health")` returns `{"status": "ok"}`
- No database connectivity check in health endpoint

**Impact:** Healthcheck only verifies HTTP server responds, not database connectivity. Container may be "healthy" but unable to serve requests.

**Recommendation:** Enhance `/health` endpoint to check database connectivity (execute `SELECT 1`).

---

### 23. CORS Configuration Uses Settings But Missing in Some Endpoints
**Files:** `backend/app/main.py`, `backend/app/core/config.py`  
**Lines:** main.py:30-35, config.py:45-50  
**Spec Reference:** SPEC.md §CORS

**Evidence:** CORS middleware configured in main.py using `settings.CORS_ORIGINS`. However, if auth endpoints are accessed before CORS middleware (unlikely in FastAPI), issues could arise. Minor.

---

### 24. Outbreak Model Missing Required Fields Per Spec
**File:** `backend/app/models/outbreak.py`  
**Lines:** 1-80  
**Spec Reference:** SPEC.md §Models — Outbreak

**Evidence:** Spec requires: `virus_type`, `province`, `district`, `location` (POINT), `cases_count`, `deaths_count`, `status`, `severity`, `reported_date`, `farm_id` (nullable), relationships.

Current model has: `virus_type`, `province`, `district`, `location`, `cases_count`, `status`, `severity`, `reported_date`, `farm_id` — **missing `deaths_count`**.

**Recommendation:** Add `deaths_count: Mapped[int] = mapped_column(Integer, default=0)`.

---

### 25. Farm Model Missing Required Fields Per Spec
**File:** `backend/app/models/farm.py`  
**Lines:** 1-70  
**Spec Reference:** SPEC.md §Models — Farm

**Evidence:** Spec requires: `owner_name`, `phone`, `poultry_type`, `capacity`, `is_active`, `address`, `location` (POINT).

Current model has all but uses `poultry_type` (String) vs spec `poultry_type` (Enum). Model uses `PoultryTypeEnum` — correct. However, spec mentions `province`, `district` fields not in model (only `address`).

**Recommendation:** Verify spec alignment. Add `province`, `district` if required.

---

### 26. Alert Model Missing sent_at Default Logic
**File:** `backend/app/models/alert.py`  
**Lines:** 33-34  
**Spec Reference:** SPEC.md §Models — Alert

**Evidence:**
```python
sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

No default. Should be auto-set on creation.

**Recommendation:** Add `default=lambda: datetime.now(timezone.utc)` or handle in service layer.

---

## Medium Severity Findings (🟡 MEDIUM)

### 27. Inconsistent Coordinate Order (lon/lat vs lat/lon)
**Files:** `backend/app/utils/geo.py`, `backend/app/services/spatial_service.py`, schemas  
**Lines:** Various  
**Spec Reference:** SPEC.md §Geo utilities

**Evidence:** 
- `geo.py:25` — `Point(lon, lat)` (correct for Shapely/PostGIS)
- `geo.py:11` — `lat_lon_to_wkt(lat, lon)` parameter order
- `spatial_service.py:55` — `ST_MakePoint(lon, lat)` 
- Schemas use `latitude`, `longitude` field names

**Impact:** Cognitive load, potential bugs when converting between formats.

**Recommendation:** Document convention clearly (PostGIS uses lon/lat). Use consistent parameter naming.

---

### 28. Outbreak Schema Has Duplicate Location Class
**File:** `backend/app/schemas/outbreak.py`  
**Lines:** 8-12  
**Spec Reference:** Finding #8

**Evidence:** Duplicate `Location` class defined inline.

---

### 29. Alert Schema Has Duplicate Location Class  
**File:** `backend/app/schemas/alert.py`  
**Lines:** 8-16  
**Spec Reference:** Finding #8

---

### 30. Farm Schema Has Duplicate Location Class AND FarmTypeEnum Issue
**File:** `backend/app/schemas/farm.py`  
**Lines:** 21-37  
**Spec Reference:** Findings #8, #9

---

### 31. Missing now_aware() Usage in Models
**Files:** Models using `datetime.utcnow()` vs `now_aware()`  
**Lines:** Various  
**Spec Reference:** SPEC.md §Database — timezone-aware datetimes

**Evidence:** `core/database.py:48` defines `now_aware()` returning timezone-aware UTC. Models should use this for `created_at`/`updated_at` defaults.

**Recommendation:** Use `default=now_aware` in mapped_column for timestamp fields.

---

### 32. Password Hash Length in User Model
**File:** `backend/app/models/user.py`  
**Lines:** 24  
**Spec Reference:** Finding #14

---

### 33. Settings Missing PASSWORD_LENGTH and Other Fields
**File:** `backend/app/core/config.py`  
**Lines:** 1-80  
**Spec Reference:** SPEC.md §Config

**Evidence:** Missing `PASSWORD_LENGTH`, `ACCESS_TOKEN_EXPIRE_MINUTES` (used in security.py but not in settings), `DEFAULT_ALERT_RADIUS_KM` (in .env.example but not Settings).

---

### 34. alembic.ini version_path May Be Incorrect
**File:** `backend/alembic.ini`  
**Lines:** 5  
**Spec Reference:** SPEC.md §P12 (Alembic)

**Evidence:** `version_path=alembic/versions` but migration file is at `alembic/versions/ae01c4d0b231_init.py` — correct. However, `script_location=alembic` assumes alembic dir is at backend root — verify.

---

### 35. Dockerfile Uses python:3.11-slim But No Build Optimization
**File:** `backend/Dockerfile`  
**Lines:** 1-20  
**Spec Reference:** SPEC.md §P17 (Dockerfile)

**Evidence:** Basic Dockerfile. No multi-stage build, no dependency caching optimization, runs as root.

**Recommendation:** Use multi-stage build, create non-root user, cache pip dependencies.

---

### 36. Frontend Directory Structure Exists But No Implementation
**Path:** `poultry-disease-warning/frontend/`  
**Spec Reference:** SPEC.md §Phase 2 — frontend is Phase 2

**Evidence:** Frontend directory mentioned in README but not audited (Phase 2). Placeholder only.

---

## Low Severity Findings (🟢 LOW)

### 37. Vietnamese Comments Mixed with English Code
**Files:** Throughout codebase  
**Spec Reference:** Code style consistency

**Evidence:** Docstrings and comments in Vietnamese (e.g., `"""Khởi tạo client test."""`). Code identifiers in English.

**Recommendation:** Standardize on English for all comments/docstrings for international team compatibility.

---

### 38. Type Hint Inconsistencies
**Files:** Various  
**Spec Reference:** Code quality

**Evidence:** Some functions use `-> User`, others `-> Optional[User]`, some missing return types.

---

### 39. Unused Imports in Some Files
**Files:** Various  
**Example:** `auth.py` imports `oauth2_scheme` but redefines it; `security.py` imports not all used.

---

### 40. Test Coverage Gaps
**Files:** `backend/tests/`  
**Spec Reference:** SPEC.md §Tests

**Evidence:** No tests for spatial_service, alert_service, geo utilities integration, auth edge cases (expired tokens, invalid signatures).

---

## Completion Matrix: SPEC.md Requirements vs Implementation

| Spec Item | Requirement | Status | Evidence |
|-----------|-------------|--------|----------|
| **P1** | Folder structure | ✅ PASS | Matches spec structure |
| **P2** | requirements.txt pinned | ✅ PASS | All versions pinned |
| **P3** | main.py FastAPI entry | ⚠️ PARTIAL | Sync lifespan, missing DB health check |
| **P4** | config.py with env_file | ✅ PASS | Pydantic Settings v2 |
| **P5** | database.py async engine | ⚠️ PARTIAL | Defined but not used |
| **P6** | security.py JWT/bcrypt | ✅ PASS | Implemented (but Phase 2) |
| **P7** | models/__init__.py exports | ✅ PASS | All models + enums exported |
| **P8** | base.py UUID, timestamps | ✅ PASS | Base and BaseModel |
| **P9** | farm.py model | ⚠️ PARTIAL | Missing deaths_count, province/district |
| **P10** | outbreak.py model | ⚠️ PARTIAL | Missing deaths_count |
| **P11** | alert.py model | ⚠️ PARTIAL | String risk_level, nullable FK issue |
| **P12** | user.py model | ⚠️ PARTIAL | password_hash length, UserRole mismatch |
| **P13** | enums.py | ⚠️ PARTIAL | UserRole missing FARMER |
| **P14** | schemas/__init__.py exports | ❌ FAIL | Missing 5 required schemas |
| **P15** | common.py Location | ✅ PASS | But duplicated elsewhere |
| **P16** | farm.py schemas | ⚠️ PARTIAL | Duplicate Location, FarmTypeEnum wrong |
| **P17** | outbreak.py schemas | ⚠️ PARTIAL | Duplicate Location |
| **P18** | alert.py schemas | ⚠️ PARTIAL | Duplicate Location, missing AlertAcknowledge |
| **P19** | user.py schemas | ⚠️ PARTIAL | UserRole validation mismatch |
| **P20** | deps.py get_current_user | ❌ FAIL | Uses X-User-Id header, RuntimeError, sync |
| **P21** | api.py router registration | ✅ PASS | All routers included |
| **P22** | farms.py CRUD | ⚠️ PARTIAL | Sync session, uses model enums not schema |
| **P23** | outbreaks.py CRUD | ⚠️ PARTIAL | Sync session, missing nearby-farms |
| **P24** | alerts.py CRUD | ❌ FAIL | Broken spatial query, sync session |
| **P25** | auth.py endpoints | ❌ FAIL | Implemented (Phase 2), sync, redefines pwd_context |
| **P26** | geo_farms.py endpoint | ⚠️ PARTIAL | Not in spec, sync session |
| **P27** | spatial_service.py | ⚠️ PARTIAL | Sync session, incomplete |
| **P28** | alert_service.py | ❌ FAIL | Incomplete risk logic, sync session |
| **P29** | init_db.py | ❌ FAIL | Sync engine, conflicts with async core |
| **P30** | seed_data.py | ❌ FAIL | Enum mismatches, will not run |
| **P31** | Dockerfile | ⚠️ PARTIAL | Basic, no optimization |
| **P32** | docker-compose.yml | ✅ PASS | Healthchecks, depends_on |
| **P33** | .env.example | ✅ PASS | All required vars |
| **P34** | alembic.ini | ✅ PASS | Configured |
| **P35** | migration init | ⚠️ PARTIAL | Geography vs Geometry mismatch |
| **P36** | README.md | ✅ PASS | Comprehensive |
| **P37** | Tests | ⚠️ PARTIAL | Sync sessions, gaps |

**Phase 1 Overall:** ❌ **FAIL** — Critical async/sync mismatch, broken alerts, missing schemas, non-functional seed

---

## Specific Focus Area Analysis

### auth.py Implementation vs Spec
| Aspect | Spec (Phase 2) | Implementation | Verdict |
|--------|----------------|----------------|---------|
| Endpoints | Stub only (501) | Full JWT/bcrypt | 🔴 Scope creep |
| Password hashing | N/A | bcrypt via passlib | ✅ Correct lib |
| JWT tokens | N/A | python-jose, HS256 | ✅ Correct lib |
| User lookup | N/A | X-User-Id header | 🔴 Wrong — should be JWT |
| Error handling | N/A | RuntimeError | 🔴 Should be HTTPException |
| Password context | N/A | Redefined in auth.py | 🟠 Duplication |

### alerts.py Model, Relationships, Logic
| Aspect | Spec | Implementation | Verdict |
|--------|------|----------------|---------|
| Fields | outbreak_id, farm_id(nullable), distance_km, risk_level(enum), message, status(enum), sent_at, acknowledged_at | Mostly correct | ⚠️ risk_level=String |
| Unique constraint | (outbreak_id, farm_id) for idempotency | Exists but allows NULL duplicates | 🔴 Broken idempotency |
| Relationships | outbreak, farm | Defined | ✅ |
| create_alert logic | Spatial distance calc | Queries Outbreak not Farm | 🔴 Completely broken |
| acknowledge endpoint | Required | Not implemented | 🟠 Missing |
| generate_alerts_for_outbreak | Idempotent, risk logic | Placeholder risk logic | 🟠 Incomplete |

### geo_farms.py Endpoint
| Aspect | Spec | Implementation | Verdict |
|--------|------|----------------|---------|
| Existence | Not listed; nearby-farms under outbreaks | Implemented as /geo/farms/around | 🔴 Wrong location |
| Request schema | FarmNearbyQuery | Uses Location from schemas | ⚠️ OK |
| Response schema | FarmNearbyResponse | Returns raw dict | 🟠 Missing schema |
| lon/lat ordering | PostGIS (lon, lat) | Uses ST_MakePoint(lon, lat) | ✅ Correct |
| Radius units | km | km parameter | ✅ |
| PostGIS usage | ST_DWithin/ST_Distance | Uses spatial_service | ✅ |
| Session type | Async | Sync | 🔴 Critical mismatch |

### Location Schema
| Aspect | Spec | Implementation | Verdict |
|--------|------|----------------|---------|
| Validation | lat: -90-90, lon: -180-180 | Implemented in common.py | ✅ |
| Single source | common.py only | Duplicated in 3 other files | 🔴 DRY violation |
| Export | schemas/__init__.py | Exported | ✅ |
| Coordinate consistency | lon/lat for PostGIS | Schemas use lat/lon field names | ⚠️ Cognitive load |

### P10–P16 & P22 Checklist
| Item | Spec Ref | Status | Notes |
|------|----------|--------|-------|
| P10 deps | requirements.txt | ✅ | Pinned versions |
| P11 router arch | api.py | ✅ | Modular routers |
| P12 FastAPI init | main.py | ⚠️ | Sync lifespan |
| P13 Farm API | farms.py | ⚠️ | Sync session |
| P14 Outbreak API | outbreaks.py | ⚠️ | Missing nearby-farms |
| P15 Alert API | alerts.py | ❌ | Broken logic |
| P16 Alembic | alembic/ | ⚠️ | Geometry mismatch |
| P22 init_db | init_db.py | ❌ | Sync engine |
| P23 seed | seed_data.py | ❌ | Enum mismatches |

---

## Integration Issues Summary

1. **Async/Sync Split Brain:** Two database initialization paths (`core/database.py` async vs `db/init_db.py` sync) — only sync is used.
2. **Circular Import Risk:** `deps.py` imports `get_db` from `core.database` but endpoints import `get_db` from `deps.py` — currently works but fragile.
3. **Enum Drift:** Models, schemas, seed data, and tests use different enum definitions/values.
4. **Schema/Model Drift:** Pydantic schemas don't consistently match SQLAlchemy models (e.g., FarmTypeEnum vs PoultryTypeEnum).
5. **Test/Implementation Drift:** `test_alerts.py` uses async/AsyncSession; all other tests use sync/Session.
6. **Migration/Model Drift:** Migration creates Geography columns; models expect Geometry.

---

## Concrete Recommendations (Prioritized)

### Immediate (Block Phase 1 Delivery)
1. **Convert entire stack to async:** Remove `db/init_db.py`, update all endpoints/services to use `AsyncSession` from `core.database`, add `await` to all DB operations.
2. **Fix alerts.py spatial query:** Change `db.query(Outbreak)` to `db.query(Farm)`, use Geometry column with PostGIS functions.
3. **Implement missing schemas:** Add `OutbreakNearbyFarmsResponse`, `UserAlertsResponse`, `AlertAcknowledge`, `FarmNearbyQuery`, `FarmNearbyResponse`.
4. **Fix seed_data.py:** Align all enum references with actual model enums.
5. **Fix Alert unique constraint:** Make `farm_id` non-nullable or add partial index.
6. **Change Alert.risk_level to Enum:** Use `RiskLevelEnum`.
7. **Remove duplicate Location classes:** Import from `common.py` in farm.py, outbreak.py, alert.py.
8. **Fix FarmTypeEnum:** Change to `StrEnum`.
9. **Fix get_current_user:** Use JWT from `security.py`, raise `HTTPException`.
10. **Fix User.password_hash length:** Use `String(255)` or add `PASSWORD_LENGTH` to settings.

### Short-term (Before Production)
11. **Move nearby-farms to outbreaks.py:** Implement `GET /api/v1/outbreaks/{id}/nearby-farms`.
12. **Complete alert_service risk logic:** Implement distance-based risk calculation.
13. **Align migration with models:** Use Geometry not Geography.
14. **Add deaths_count to Outbreak model.**
15. **Fix UserRole enum:** Add `FARMER = "farmer"` value.
16. **Enhance /health endpoint:** Add database connectivity check.
17. **Standardize tests on async:** Convert all tests to use `AsyncSession`.
18. **Dockerfile optimization:** Multi-stage build, non-root user.
19. **Add now_aware() defaults to model timestamps.**

### Technical Debt (Post-Launch)
20. **Remove auth.py implementation** (or mark clearly as Phase 2 stub).
21. **Consolidate geo utilities:** Ensure single coordinate convention.
22. **Add comprehensive test coverage:** Spatial service, alert service, auth edge cases.
23. **Documentation:** API docs, architecture decision records.

---

## Final Verdict

**The project does not meet Phase 1 acceptance criteria.** The fundamental async/sync architecture violation alone blocks production readiness. Combined with broken alert logic, non-functional seed data, missing schemas, and enum mismatches, the codebase requires **2-3 weeks of focused rework** before it can pass a Phase 1 acceptance review.

**Recommended Path Forward:**
1. Week 1: Async conversion + alert logic fix + schema implementation
2. Week 2: Seed data fix + migration alignment + test conversion
3. Week 3: Integration testing + Docker optimization + documentation

---

*End of Audit Report*