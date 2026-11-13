# Independent Senior Architect Review — `poultry-disease-warning`

**Reviewer:** Independent architect (read-only static inspection)
**Method:** Static source inspection against `SPEC.md` and `AUDIT_REPORT.md`. No DB, migrations, or tests were executed; no source files were modified (SPEC.md L193 constraint).
**Scope:** `backend/app/**`, `backend/alembic/**`, `backend/tests/**`, `SPEC.md`, `AUDIT_REPORT.md`.

> Severity tiers: **CRITICAL** (blocks startup or Phase-1 acceptance), **HIGH** (broken feature/runtime failure), **MEDIUM** (data-integrity/maintenance defect), **LOW** (quality/typo). "Verified" = read line-by-line this session; "Unverified" = evidence not fully re-read this session.

---

## 1. Verdict

**The codebase does not meet Phase 1 acceptance criteria.** This verdict agrees with `AUDIT_REPORT.md`, but the underlying evidence is **worse than the audit reports**: the audit itself contains several incorrect line citations and spec misquotes (see §6). The dominant problems are:

1. **A pervasive async/sync mismatch** — every endpoint/service uses a synchronous `Session` against an `asyncpg` async engine, which will fail at runtime.
2. **An import-time crash cluster** — the application cannot even start because of undefined settings, a missing `primary_key`, a relationship without a foreign key, a missing `@field_validator` import, and broken import paths across the API layer and seed script.
3. **Model/schema/service field mismatches** — endpoints and the alert service write to columns that do not exist on the models.

Estimated rework: **2–3 weeks**, consistent with the audit's estimate, but the fix list differs materially from the audit's recommendations (§5, §6).

---

## 2. Verification Matrix (Audit Findings → Independent Assessment)

| Audit # | Audit Claim (short) | Verified? | Independent assessment |
|---|---|---|---|
| 1 | Async/sync `Session` vs `get_db` mismatch | ✅ Verified | Correct; pervasive across endpoints + services. |
| 2 | Auth implemented despite P2 stub-only | ✅ Verified | Correct; full JWT/bcrypt auth exists; SPEC §Giai đoạn 2 (L185) defers it. |
| 3 | `alerts.py` queries `Outbreak` instead of `Farm` | ✅ Verified (with correction) | Correct bug, but audit's quoted line (`alert_in.farm_id`) does not match code (`payload.outbreak_id`). |
| 4 | Enum mismatches seed ↔ models | ✅ Verified | Correct in spirit; specifics partly wrong (see §6). |
| 5 | Inconsistent PK types (UUID vs String) | ⚠️ Partially wrong | Audit asserts `outbreak.py:18` and `alert.py:18` have `primary_key=True`. **They do NOT** — both `id` columns lack `primary_key=True`, which is a CRITICAL bug the audit missed. |
| 6 | `farm_id` NULL + unique constraint idempotency gap | ⚠️ Partially wrong | `farm_id` is `nullable=True` (verified); unique constraint is `uq_alert_outbreak_farm` (L98–100), **not** `uq_outbreak_farm` (audit L42 wrong). |
| 7 | `risk_level` String instead of enum | ✅ Verified | Correct (`alert.py` L46–48). |
| 8 | `Location` schema duplicated in 4 files | ✅ Verified | Correct, but see correction §6 (a 5th `schemas/location.py` also exists). |
| 9–19 | (pruned middle) | ⚠️ Not fully re-read | Referenced in §4/§6 where re-verified; individual numbering not re-verified end-to-end. |
| 20 | Seed data non-functional | ✅ Verified | Worse than stated — seed imports nonexistent symbols AND field names don't match models. |
| 21 | Tests use sync sessions | ✅ Verified | `conftest.py` uses sync `SessionLocal` from `db/init_db.py`; `test_alerts.py` mixes `AsyncSession`. |
| 22 | `/health` has no DB check | ✅ Verified | `main.py` `/health` returns static `{"status":"ok"}`; compose healthcheck only probes HTTP. |
| 23 | CORS minor note | ✅ Verified | `main.py` + `config.py`; cosmetic. |
| 24 | Outbreak missing `deaths_count` | ❌ Misquote | SPEC §3 Outbreak (L106–115) does **not** require `deaths_count`. Real missing fields: `radius_km` and `farm_id` FK. |
| 25 | Farm model "has all" required fields | ❌ Wrong | Farm model is missing `name`, `owner_name`, `phone`, `email`, `address`, `province`, `district`, `capacity`, `is_active` — nearly everything SPEC requires. |
| 26 | Alert `sent_at` no default | ✅ Verified | Correct (minor). |

---

## 3. CRITICAL Findings (block startup / Phase-1 acceptance)

### C1. Import-time crash cluster — application cannot start
At least seven independent `ImportError`/`AttributeError`/`NameError` sources fire at import or startup:

1. **`core/security.py` L22, L23, L43** — `settings.jwt_algorithm`, `settings.jwt_token_expire_minutes`, `settings.jwt_secret_key` are lowercase aliases that **do not exist**. `core/config.py` defines only uppercase (`JWT_ALGORITHM`, `JWT_TOKEN_EXPIRE_MINUTES`, `JWT_SECRET_KEY`). → `AttributeError` at module import.
2. **`models/user.py` L24** — `password = CHAR(settings.PASSWORD_LENGTH)`; `config.py` has **no** `PASSWORD_LENGTH`. → `AttributeError`.
3. **`api/v1/endpoints/auth.py` L132** — `_login` uses `settings.ACCESS_TOKEN_MINUTES` (undefined); config exposes only `JWT_TOKEN_EXPIRE_MINUTES`. → `AttributeError` at login.
4. **`schemas/farm.py` L5 vs L27** — `@field_validator` is used at L27 but never imported (imports only `BaseModel, ConfigDict, Field`). → `NameError` at import.
5. **`api/v1/endpoints/alerts.py` L9, L10, L14** — `from app.api.schemas.alert import ...` (no such package; schemas live in `app/schemas/`), `from app.models.alert import AlertStatusEnum, RiskLevelEnum` (enums live in `models/enums.py`), `from .deps import get_current_user` (no `endpoints/deps.py`). → `ImportError`.
6. **`api/v1/endpoints/farms.py` L9, L11, L12, L14** and **`outbreaks.py` L9, L11, L12, L14** — `from app.api.schemas.farm/outbreak` (broken path), `from app.models.farm import Farm, FarmStatus, FarmType` (`FarmStatus`/`FarmType` nonexistent), `from app.models.outbreak import Disease, Outbreak, OutbreakStatus` (`Disease`/`OutbreakStatus` nonexistent), `from app.services.alert_service import notify_outbreak` (`notify_outbreak` is in `notification_service`), `from .deps import get_current_user` (broken). → `ImportError`.
7. **`db/seed_data.py`** — imports `AlertSeverity, AlertStatus` from `models.alert`, `FarmStatus, FarmType` from `models.farm`, `Disease, OutbreakStatus` from `models.outbreak` — none of these symbols exist. → `ImportError`.

**Impact:** `python -m app.main` / `uvicorn` will fail before serving a request. Severity: **CRITICAL**.

### C2. Missing primary keys on `Outbreak` and `Alert`
- **`models/outbreak.py` L23–25** — `id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid4()))` — **no `primary_key=True`**. Overrides the inherited `Base.id` UUID PK, losing the primary key.
- **`models/alert.py` L28–30** — same pattern: `String(36)` id with **no `primary_key=True`**.

**Impact:** SQLAlchemy `create_all()` will fail ("Table ... has no primary key") or produce a broken table; FK relationships on `Alert.outbreak_id`/`farm_id` cannot resolve to a valid PK. Severity: **CRITICAL**.

### C3. `Outbreak.farm` relationship has no `farm_id` foreign key
- **`models/outbreak.py` L82–86** — `farm: relationship("Farm", back_populates="outbreaks", uselist=False)` declared, but **no `farm_id` mapped column / ForeignKey** exists on `Outbreak`.

**Impact:** The mapper cannot resolve the relationship → `NoForeignKeysError`/`ArgumentError` at mapper configuration (startup). Farm–Outbreak linkage (required by SPEC §6 `/outbreaks/{id}/nearby-farms`) is impossible. Severity: **CRITICAL**.

### C4. Async engine + synchronous `Session` everywhere
- `core/database.py` builds an **async** engine/sessionmaker (`asyncpg`), with async `get_db`.
- `api/v1/endpoints/farms.py`, `outbreaks.py`, `alerts.py`, `geo_farms.py`, `auth.py`, `services/spatial_service.py`, `services/alert_service.py`, `db/init_db.py`, `db/seed_data.py` all declare synchronous `db: Session = Depends(get_db)` and call `db.query(...)`, `db.commit()`, `db.refresh()`.

**Impact:** `asyncpg` cannot be driven by a synchronous `Session`; every data-access call fails at runtime. Severity: **CRITICAL** (matches audit Finding #1).

### C5. `db/init_db.py` is sync and conflicts with `core/database.py`
- `db/init_db.py` creates its own **sync** engine/sessionmaker and calls `drop_all()`/`create_all()`.
- `main.py` lifespan calls async `init_db`/`close_db` from `core/database.py` (which only does `SELECT 1`).

**Impact:** Schema is never actually created by the app lifespan; the sync initializer is incompatible with the async stack. Severity: **CRITICAL**.

---

## 4. HIGH Findings (broken feature / runtime failure)

### H1. Two conflicting `get_current_user` dependencies
- **`api/deps.py`** — `get_current_user` is async but takes `db: Session = Depends(get_db)` (sync), reads a **plain `x_user_id: str | None = None` parameter** (no JWT/OAuth2), calls `db.get(User, x_user_id)`, and raises a bare `RuntimeError` (→ HTTP 500, not 401) when missing.
- **`core/security.py`** — a separate async JWT-based `get_current_user` that selects `User.username` (column **does not exist**) and defaults `role=UserRole.FARMER` (**not** a member of `UserRole`, which only has `ADMIN`/`USER`).

**Impact:** Authentication is inconsistent and non-functional; 401 semantics are wrong (500 instead); `security.py` `UserRole.FARMER` is a `NameError`-at-call and the role does not match SPEC §Giai đoạn 2 (L185), which specifies `FARM_OWNER`. Severity: **HIGH**.

### H2. Enum system collision and misuse
- **`models/enums.py`** — `PoultryTypeEnum`, `OutbreakStatusEnum`, `SeverityLevelEnum`, `RiskLevelEnum`, `AlertStatusEnum` all subclass `sqlalchemy.Enum` (**SA_Enum column type**), not Python `enum.Enum`/`str, Enum`.
- **`models/user.py`** — uses Python `Enum(UserRole)` (ADMIN/USER only) — a different convention.
- **`models/farm.py` L33** — `poultry_type = String(100)` (no enum at all; `PoultryTypeEnum` unused).
- **`models/alert.py` L46–48** — `risk_level = String(50)` (no enum; SPEC §3 requires Enum LOW/MEDIUM/HIGH/CRITICAL).

**Impact:** Because the "enums" are SA_Enum column types, code that treats them as Python enums fails:
- `services/alert_service.py` L58 uses `AlertStatusEnum.CONFIRMED.value` but `AlertStatusEnum` is **not imported** → `NameError`.
- `alert_service.py` calls `SeverityLevelEnum(outbreak.severity)` — SA_Enum is **not callable** → `TypeError`.
- `alert_service.py` references `RiskLevelEnum.MEDIUM` — SA_Enum has **no `.MEDIUM`** → `AttributeError`.
- Enum values also drift from SPEC (§6). Severity: **HIGH**.

### H3. Endpoints write to nonexistent model columns
- **`api/v1/endpoints/farms.py`** references `Farm.owner_name`, `Farm.province`, `Farm.address` (L37–39), `Farm.created_at` (L42), `Farm.farm_type`, `Farm.status` (L33–34), `Farm.latitude`, `Farm.longitude`, `Farm.phone`, `Farm.notes` (L71–75). `Farm` model defines **none** of these (only `id`, `poultry_type`, `location`, timestamps). `FarmResponse.model_validate(f)` is also called on ORM objects (not dicts).
- **`api/v1/endpoints/outbreaks.py`** filters `Outbreak.disease` / `Outbreak.status` (L31–33), orders by `Outbreak.detected_at` (L35), and constructs `Outbreak(disease=..., symptom=..., detected_at=..., description=..., farm=farm)` (L63–69). `Outbreak` has **none** of `disease`/`symptom`/`detected_at`/`description`.
- **`api/v1/endpoints/alerts.py`** sets `Alert(message=payload.message)` (L66–72) and `alert.message` (L117–118) — `Alert` model has **no `message` column** (SPEC §3 requires it, so both model and endpoint are out of spec).

**Impact:** Every one of these routes raises `AttributeError`/`ArgumentError` at runtime. Severity: **HIGH**.

### H4. `alerts.py` distance calculation is broken
- **L82** — `farm = db.query(Outbreak).filter(Outbreak.id == payload.outbreak_id).first()` queries **Outbreak** instead of **Farm**.
- **L83** — `if farm and farm.location` (on the wrong entity).
- **L93** — `distance_expr = func.ST_Distance(outbreak.location, alert_farm.location) / 1000.0` passes ORM **column objects**, not values.
- **L94** — `db.session.execute(...)` — `Session` has no `.session` attribute → `AttributeError`, swallowed by a bare `except` (L96–98).
- **L75 commit** happens **before** `distance_km` is computed (L78–95) and is never re-committed.

**Impact:** Alert generation is non-functional; distance is never persisted. Severity: **HIGH**.

### H5. `geo_farms.py` non-serializable response model
- **`api/v1/endpoints/geo_farms.py` L14** — `response_model=list[tuple[Farm, float]]` — a tuple of an ORM object and float cannot be serialized by FastAPI.
- **L28** — `if not location.longitude or not location.latitude:` is an always-false guard (Pydantic `Location` requires non-null floats).

**Impact:** The endpoint fails serialization. Note: its `from app.schemas.location import Location` import **is valid** (module exists) — this corrects a prior assumption. Severity: **HIGH** (route unusable), guard issue **LOW**.

### H6. `utils/geo.py` convention vs SPEC single-source-of-truth
- SPEC §4 (L127–133) mandates exactly one converter pair: `location_to_geometry(lat, lon)` / `geometry_to_location(geom)` using `shapely.Point(lon, lat)`, and forbids manual WKT.
- `utils/geo.py` instead exposes `lat_lon_to_wkt(lat, lon)`, `wkt_to_lat_lon`, `create_geometry_point(lon, lat)`, `validate_point_wkt`. Function names and signatures differ from SPEC; `geo_farms.py` L36 hand-builds `f"{location.longitude} {location.latitude}"` instead of calling the util.

**Impact:** Coordinate convention is not centralized; risk of lat/lon inversion (SPEC explicitly warns against this). Severity: **HIGH** (spec deviation), though helper itself uses lon/lat internally.

### H7. Farm model missing nearly all SPEC-required fields
- SPEC §3 Farm (L99–104): `name`, `owner_name`, `phone`, `email`, `address`, `province`, `district`, `poultry_type` (enum CHICKEN/DUCK/MUSCOVY/QUAIL/OTHER), `capacity`, `is_active`, `location` (Geometry POINT,4326, GiST index).
- `models/farm.py` defines only `id`, `poultry_type` (String, wrong type), `location` (Geometry, **no `spatial_index=True`**), and one `outbreaks` relationship.

**Impact:** Farm CRUD cannot represent the spec'd entity; audit Finding #25's claim that the model "has all" fields is incorrect. Severity: **HIGH**.

### H8. Outbreak model missing `radius_km` and `farm_id` (spec-critical)
- SPEC §3 Outbreak (L106–115) requires `radius_km` (Float, default from config) and (implicitly, via the relationship + `/nearby-farms`) a `farm_id` FK. Both are absent.
- Audit Finding #24 instead claims `deaths_count` is missing — `deaths_count` is **not** in SPEC (misquote).

**Impact:** `/outbreaks/{id}/nearby-farms` and alert radius logic cannot be implemented. Severity: **HIGH**.

### H9. Seed data non-functional
- `db/seed_data.py` imports nonexistent symbols (`AlertSeverity`, `AlertStatus`, `FarmStatus`, `FarmType`, `Disease`, `OutbreakStatus`), uses field names that don't exist on the models, and declares `seed(db: Session)` (sync) against the async `get_db`.
- SPEC §8 requires 5 farms + 3 outbreaks, idempotent, with one farm inside and one outside a 5 km active-outbreak radius.

**Impact:** `python -m app.db.seed_data` fails; acceptance criterion "seed runs twice without error" cannot pass. Severity: **HIGH**.

---

## 5. MEDIUM / LOW Findings

### MEDIUM
- **M1. PK type inconsistency** (`Farm`/`User` UUID vs `Outbreak`/`Alert` String(36)) — audit Finding #5 direction is right, but the deeper issue is the missing `primary_key=True` (C2). API responses will mix UUID objects and strings.
- **M2. `Alert.farm_id` nullable + `UniqueConstraint(outbreak_id, farm_id)`** — NULL≠NULL in Postgres, so multiple outbreak-level (NULL farm) alerts can be inserted, breaking idempotency (audit Finding #6). Constraint name is `uq_alert_outbreak_farm` (L98–100), not `uq_outbreak_farm`.
- **M3. `Alert.farm` relationship has no `back_populates`** (unidirectional), inconsistent with `outbreak`/`outbreaks` bidirectional pattern.
- **M4. `models/user.py` `is_active` uses `server_default=func.now()`** — a boolean column defaulting to a timestamp is semantically wrong.
- **M5. Alembic init migration** (`ae01c4d0b231_init.py`) uses `Geography` columns while models declare `Geometry(POINT, 4326)` — schema drift between migration and model; must pick one convention.
- **M6. `db/init_db.py` `drop_all()`/`create_all()`** — destructive and bypasses Alembic; SPEC §2 mandates Alembic-managed schema.
- **M7. `alerts.py` L12** imports `find_farms_within_radius` but never uses it; distance is re-implemented inline and incorrectly.
- **M8. Tests** — `conftest.py` uses sync `SessionLocal` (from `init_db.py`) while `test_alerts.py` mixes `AsyncSession`; no async fixture; auth tests would fail because the dependency uses `X-User-Id` rather than JWT (audit Finding #21).

### LOW
- **L1.** `enums.py` L12 typo `BROIILER = "broiler"` (double-I).
- **L2.** `Location` schema duplicated in `common.py`, `farm.py`, `outbreak.py`, `alert.py` (plus a separate `schemas/location.py`) — five definitions (audit Finding #8 undercounts).
- **L3.** `schemas/alert.py` `validate_coords` is a plain `@classmethod`, not a Pydantic validator — inert.
- **L4.** `schemas/farm.py` `FarmTypeEnum` subclasses `BaseModel` (decorative), not `str, Enum`.
- **L5.** `geo_farms.py` L5 imports `get_current_user` but never uses it.
- **L6.** `/health` (main.py) has no DB connectivity check (audit Finding #22).
- **L7.** `schemas/alert.py` `AlertCreate.risk_level` pattern `^(low|medium|high|very_high)$` mismatches SPEC's `LOW/MEDIUM/HIGH/CRITICAL`.
- **L8.** `Alert` model lacks `message` and `sent_at` has no default (audit Finding #26).

---

## 6. Corrections to `AUDIT_REPORT.md` (audit's own errors)

1. **Finding #5 is materially wrong.** Audit asserts `outbreak.py:18` and `alert.py:18` define `primary_key=True`. They **do not** — the `id` columns override the inherited UUID PK with `String(36)` and drop the primary key. This is the single most severe data-model bug and the audit mislabels it as a mere "type inconsistency."
2. **Finding #24 misquotes SPEC.** `deaths_count` is **not** required by SPEC §3 Outbreak. The genuinely missing spec fields are `radius_km` and the `farm_id` FK.
3. **Finding #25 is wrong.** The Farm model does **not** "have all" spec fields; it is missing `name`, `owner_name`, `phone`, `email`, `address`, `province`, `district`, `capacity`, `is_active`.
4. **Finding #3 quote mismatch.** The audit's evidence quotes `alert_in.farm_id`; the actual code uses `payload.outbreak_id`. The bug (querying `Outbreak` not `Farm`) is real, but the audit's evidence is not verbatim.
5. **Finding #6 constraint name.** Audit cites `name="uq_outbreak_farm"` at L42; actual is `uq_alert_outbreak_farm` at L98–100.
6. **Finding #8 undercounts** the `Location` duplication (four files listed; five exist including `schemas/location.py`).
7. **Prior assumption corrected:** `geo_farms.py`'s `from app.schemas.location import Location` is **valid** — `schemas/location.py` exists (19 lines, verified). The genuine geo_farms bugs are the `list[tuple[Farm, float]]` response model and the always-false guard, not the import.

---

## 7. SPEC Cross-Reference (P10–P16, P22)

The audit cites SPEC paragraph markers (`§P10`, `§P13`, `§P15`, etc.). Mapping these to the SPEC sections re-read this session (SPEC.md L74–193):

| Audit ref | Audit topic | SPEC anchor (verified) | Consistency |
|---|---|---|---|
| §P10 (Finding #21) | Tests | SPEC L180 ("Toàn bộ test Giai đoạn 1 pass"); folder L74 `test_auth.py [P2]` | Consistent — tests are Phase 1 except auth. |
| §P13 (Finding #3) | Alert distance logic | SPEC §7 `alert_service` (L165), §6 `/alerts` (L157–160) | Consistent — alert radius/distance is Phase 1. |
| §P15 (Finding #4/#20) | Seed data | SPEC §8 (L168–174) | Consistent — idempotent seed is Phase 1. |
| §P22 (Finding #22) | `/health` | SPEC §1 compose healthcheck (L82–83) | Consistent — but SPEC requires `pg_isready` on **db**; the backend `/health` DB check is a reasonable extra, not a spec violation. |
| P11/P12/P14/P16 | (not re-read end-to-end this session) | — | **Unverified** — not cross-referenced verbatim. |

**Key spec-deviation confirmations:**
- Auth (JWT/bcrypt) belongs to Giai đoạn 2 (SPEC L185), not Phase 1 — confirms audit Finding #2 (scope creep).
- Phase 2 roles are `ADMIN`, `VET_OFFICER`, `FARM_OWNER` (L185); `UserRole` in code has only `ADMIN`/`USER`, and `security.py` references nonexistent `UserRole.FARMER`.
- SPEC §4 (L127–133) mandates a single coordinate-conversion location; `utils/geo.py` deviates (H6).
- SPEC §7 `alert_service` (L165) requires `risk_level` computed from distance + severity, and **only when outbreak `status == ACTIVE`**; the service computes `RiskLevelEnum.MEDIUM.value` (broken) and does not implement the config-threshold logic.
- SPEC §3 Alert (L119–124) requires `message`, `risk_level` (enum), `status` (PENDING/SENT/FAILED/ACKNOWLEDGED); `models/alert.py` lacks `message` and uses `String(50)` for `risk_level`.

---

## 8. Priority Fix Order (Recommended)

1. **Make it import & configure:** fix `config.py` (`PASSWORD_LENGTH`, expose uppercase settings or fix lowercase references in `security.py`/`auth.py`); import `field_validator` in `schemas/farm.py`; fix all `app.api.schemas.*` → `app.schemas.*` imports and `from .deps` → `from app.api.deps`; move `notify_outbreak` reference to `notification_service`; delete nonexistent symbol imports in `farms.py`/`outbreaks.py`/`seed_data.py`.
2. **Fix the data model:** add `primary_key=True` to `Outbreak.id`/`Alert.id`; add `farm_id` FK to `Outbreak`; align Farm/Outbreak/Alert columns to SPEC (§3); switch enums from `SA_Enum` column types to Python `str, Enum`.
3. **Convert to async end-to-end:** replace sync `Session` with `AsyncSession` + `await` in all endpoints and services; unify `get_db`/`get_current_user`.
4. **Fix alert generation:** query `Farm` (not `Outbreak`), compute distance via `spatial_service`, persist `distance_km` before commit, implement `risk_level` thresholds and `status == ACTIVE` gate.
5. **Rebuild seed + tests:** rewrite `seed_data.py` to actual models/enums; convert tests to async fixtures.

---

## 9. Unverified Items (explicit)

- The middle findings 9–19 of `AUDIT_REPORT.md` were not re-read end-to-end this session; they are covered here only where independently re-verified (C/H/M items). Their individual numbering should be re-checked before treating this review as exhaustive.
- `services/notification_service.py` `notify_outbreak` signature and `services/crawler_service.py` stub content were confirmed at a high level but not re-read line-by-line this session.
- Exact line numbers in `db/seed_data.py`, `tests/conftest.py`, and the Alembic init migration are cited from earlier verification in this session; spot-check before final sign-off.

---

*End of Independent Review.*
