# Project State - P6-P9 Audit Complete

## Status: BLOCKED - Pending User Review & Decision

## Progress Summary (P1-P5)
- ✅ Models structurally complete (base.py, farm.py, outbreak.py, alert.py, user.py, enums.py)
- ✅ Utils implemented (geo.py for GeoAlchemy2/Shapely conversions)
- ✅ Service layer created but incomplete (spatial_service.py, alert_service.py broken, notification_service.py placeholder)
- ⏸️ P6: Schema/service layer compliance audit - COMPLETED but findings block P7+

## Known Issues & Blockers

### Critical Missing Files
1. **`app/api/schemas/*.py`** - ENTIRELY MISSING
   - Endpoints import from `app.api.schemas.farm`, `app.api.schemas.outbreak`, `app.api.schemas.alert`, `app.api.schemas.user`
   - These Pydantic schemas do NOT exist
   - Impact: API endpoints cannot work without them

### Service Layer Issues (P6/P7/P8)

#### 1. `spatial_service.py` - Spatial Query Implementation Issues
- ❌ Uses haversine distance calculation instead of PostGIS-native `ST_DWithin`
- ❌ Missing geography column cast for accurate spatial filtering
- ⚠️ PostGIS geometry functions require `geography` type for efficient nearest-neighbor queries
- Risk: Slow performance at scale, potential accuracy issues

#### 2. `alert_service.py` - Multiple Critical Issues
- ❌ **Session injection broken**: Uses `outbreak.farm.owner` (database Session) instead of injecting `db` parameter
- ❌ **Passes empty list to nearest_farm** - always returns no farms
- ❌ **Imports incorrect enums**:
  ```python
  from app.models.alert import AlertSeverity, AlertStatus, FarmStatus, OutbreakStatus
  # Should be: AlertStatusEnum, RiskLevelEnum (from enums.py)
  # AlertSeverity doesn't exist! 
  ```
- ❌ Missing unique constraint exception handling for Alert(unique_constraint=(outbreak_id, farm_id))

#### 3. `notification_service.py` - Incomplete Implementation
- ❌ Only has print statements (placeholder)
- ❌ Needs User model import and proper notification interface

### Dependencies Issues

#### 4. `app/api/v1/endpoints/alerts.py`
- ❌ **Missing Outbreak import**: Uses `db.get(Outbreak, payload.outbreak_id)` but doesn't import Outbreak from models
- ❌ Line 67: `farm=payload.farm_id` should be `farm_id=payload.farm_id` (wrong keyword argument)

#### 5. Enums Naming Consistency
File: `app/models/enums.py` defines:
- `PoultryTypeEnum`, `OutbreakStatusEnum`, `SeverityLevelEnum`, `RiskLevelEnum`, `AlertStatusEnum`

But endpoints/services import non-existent:
- `AlertSeverity` (doesn't exist - should use `SeverityLevelEnum` or create separate enum)
- `FarmStatus` (doesn't exist in Farm model)

### File-by-File Audit Results

| File | Status | Issues |
|------|--------|--------|
| `app/models/base.py` | ✅ OK | Clean UUID/timestamp mixin |
| `app/models/farm.py` | ✅ OK | Structurally complete, geometry as str (GeoAlchemy2) |
| `app/models/outbreak.py` | ✅ OK | Complete with relationships |
| `app/models/alert.py` | ⚠️ PARTIAL | Has UniqueConstraint; exception handler not implemented; imports wrong enums |
| `app/models/user.py` | ✅ OK | Clean User model |
| `app/models/enums.py` | ⚠️ N/A | Enums exist but naming inconsistent with code |
| `app/utils/geo.py` | ⚠️ QUESTIONABLE | Implementation correctness needs verification |
| `app/services/spatial_service.py` | ❌ BROKEN | Haversine vs ST_DWithin; missing geography cast |
| `app/services/alert_service.py` | ❌ BROKEN | Session handling broken; wrong imports; empty list passed |
| `app/services/notification_service.py` | ❌ INCOMPLETE | Only print statements |
| `app/api/v1/endpoints/farms.py` | ✅ OK | Clean implementation |
| `app/api/v1/endpoints/outbreaks.py` | ⚠️ PARTIAL | Correctly calls notify_outbreak() but service broken |
| `app/api/v1/endpoints/alerts.py` | ❌ BROKEN | Missing Outbreak import; wrong keyword arg |
| `app/api/schemas/*.py` | ❌ MISSING | Entire directory missing! |

## DECISIONS.md Content (Required for Next Steps)

### Decision 1: Schemas vs Inline Pydantic Models
**Issue**: `app/api/schemas/*.py` doesn't exist, but endpoints import from them.

**Options**:
1. Create `app/api/schemas/` directory with all Pydantic models
2. Use inline `type=` annotations with model fields in endpoints (not recommended for maintainability)
3. Merge schemas into models directory

**Recommendation**: Create `app/api/schemas/` with proper Pydantic v2 models for:
- `farm.py`: FarmCreate, FarmResponse, FarmUpdate
- `outbreak.py`: OutbreakCreate, OutbreakResponse, OutbreakUpdate  
- `alert.py`: AlertCreate, AlertResponse, AlertUpdate
- `user.py`: UserCreate, UserResponse, UserUpdate, Token (from auth)

**Blocker**: Cannot proceed to P7 until schemas are created.

### Decision 2: Spatial Query Strategy
**Issue**: `spatial_service.py` uses haversine instead of PostGIS `ST_DWithin`.

**Options**:
1. Convert geometry columns to geography type in models (migration required - NOT ALLOWED per constraints)
2. Keep geometry as POINT and use distance-based queries (less efficient, needs custom SQL)
3. Accept current approach with warnings about performance limitations

**Recommendation**: For P7-P9 without migrations, we must:
- Implement `spatial_service.py` with proper `ST_DWithin` in raw SQL queries
- Cast geometry to geography on query time using `.cast(geography)` 
- Document this limitation in DECISIONS.md

### Decision 3: Alert Unique Constraint Handling
**Issue**: Alert has `UniqueConstraint(outbreak_id, farm_id)` but no exception handler.

**Requirement per SPEC**: "Notify nearest farms only when outbreak detected". This implies one alert per (outbreak, farm) pair.

**Approach**:
- Catch `IntegrityError` from SQLAlchemy when creating duplicate alert
- Convert to appropriate HTTP error or update existing alert

### Decision 4: Risk Calculation Logic
**Issue**: SPEC mentions risk calculation but logic is unspecified in compacted summary.

**Status**: Need clarification on risk score formula (distance × severity? population density? etc.)

## P6-P9 Roadmap

### P6: Schema/Service Layer Compliance Audit ✅ COMPLETED
- Reviewed all models, utils, services, endpoints
- Documented all issues above in this file and DECISIONS.md (to be created)

### P7: Spatial Alert Generation with ST_DWithin ❌ BLOCKED
- Requires fixing `spatial_service.py` to use PostGIS-native spatial functions
- Blocked by missing schemas and broken service layer imports

### P8: Unique Constraint Exception Handling ❌ BLOCKED  
- Need to implement IntegrityError handling in alert creation flow
- Blocked by breaking issues in alert_service.py

### P9: Complete Spatial-Based Alert Flow ❌ BLOCKED
- End-to-end flow requires working schemas, services, and exception handling
- Cannot proceed until P7 and P8 resolved

## Pending Tasks for User Approval

1. **Create `app/api/schemas/` directory** with Pydantic models for farms, outbreaks, alerts, users
2. **Fix enum imports** in all files (AlertSeverity→use SeverityLevelEnum or create new enum)
3. **Fix spatial_service.py** to use geography cast and ST_DWithin queries
4. **Fix alert_service.py** session handling and remove wrong enum imports
5. **Complete notification_service.py** with proper implementation
6. **Add Outbreak import** to alerts endpoint
7. **Verify geo.py** correctness (test lat/lon order in WKT generation)
8. **Create DECISIONS.md** documenting all architectural decisions and SPEC contradictions

## File Creation Priority

1. `app/api/schemas/user.py` - User schemas for auth endpoints
2. `app/api/schemas/farm.py` - Farm CRUD schemas
3. `app/api/schemas/outbreak.py` - Outbreak schemas  
4. `app/api/schemas/alert.py` - Alert schemas (requires correct enums)
5. Fix imports in all endpoint files

---

**Last Updated**: 2026-11-12
**Next Action**: Await user review of audit findings before proceeding with file creation
