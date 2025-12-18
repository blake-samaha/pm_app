# Phase 1 Completion Plan: Risk Resolution & Demo Infrastructure

**Created:** December 18, 2025  
**Status:** Planning  
**Remaining Tasks:**
- Add `decision_record` field to Risk model
- Create Risk close/resolve UI with decision record input
- Add Cloudflare Tunnel service to `docker-compose.yml`

---

## Executive Summary

Before implementing the Risk Decision Record feature, we've identified **architectural gaps** that should be addressed to ensure clean, maintainable code. The current Risk management code bypasses the layered architecture pattern used elsewhere in the codebase.

### Current Architecture Issues

| Layer | Projects | Users | Risks | Actions |
|-------|----------|-------|-------|---------|
| Router | ✅ `projects.py` | ✅ `users.py` | ⚠️ `risks.py` | ⚠️ `actions.py` |
| Service | ✅ `ProjectService` | ✅ `UserService` | ❌ **Missing** | ❌ **Missing** |
| Repository | ✅ `ProjectRepository` | ✅ `UserRepository` | ❌ **Missing** | ❌ **Missing** |

**Problem:** The `risks.py` and `actions.py` routers directly access the database, bypassing the service layer. This creates:
- ❌ Scattered business logic
- ❌ Difficult-to-test code
- ❌ Inconsistent patterns
- ❌ No encapsulation of status transition rules

### Frontend Type Sync Issue

The frontend `RiskStatus` enum is **missing the `MITIGATED` value** that exists in the backend:

```typescript
// Frontend: frontend/types/actions-risks.ts
export enum RiskStatus {
  OPEN = "Open",
  CLOSED = "Closed"
  // Missing: MITIGATED = "Mitigated"
}

// Backend: backend/models/__init__.py
class RiskStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MITIGATED = "Mitigated"  # ✅ Exists
```

---

## Implementation Plan

### Group A: Risk Management Architecture Refactor (Priority: High)

This group establishes the proper foundation before adding new features.

#### A.1 Create `RiskRepository` (~30 min)

**File:** `backend/repositories/risk_repository.py`

```python
class RiskRepository(BaseRepository[Risk]):
    """Repository for Risk database operations."""
    
    def get_by_project(self, project_id: UUID) -> List[Risk]:
        """Get all risks for a project."""
        
    def get_open_risks(self, project_id: UUID) -> List[Risk]:
        """Get only open/unresolved risks for a project."""
        
    def get_by_status(self, project_id: UUID, status: RiskStatus) -> List[Risk]:
        """Get risks filtered by status."""
```

**Why:** Encapsulates all database queries for risks, following the existing pattern in `project_repository.py`.

---

#### A.2 Create `RiskService` with Resolution Logic (~45 min)

**File:** `backend/services/risk_service.py`

```python
class RiskService:
    """Service for Risk business logic."""
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = RiskRepository(session, Risk)
    
    def get_project_risks(self, project_id: UUID, user: User) -> List[Risk]:
        """Get risks for a project (with access control)."""
        
    def create_risk(self, data: RiskCreate, user: User) -> Risk:
        """Create a new risk."""
        
    def resolve_risk(
        self, 
        risk_id: UUID, 
        status: RiskStatus,  # CLOSED or MITIGATED
        decision_record: str,
        user: User
    ) -> Risk:
        """
        Resolve a risk with a required decision record.
        
        Business Rules:
        - status must be CLOSED or MITIGATED (not OPEN)
        - decision_record is required and non-empty
        - resolved_at is set automatically to now()
        - resolved_by is set to the current user
        """
        
    def reopen_risk(self, risk_id: UUID, user: User) -> Risk:
        """Reopen a previously resolved risk."""
```

**Key Business Logic:**
- Resolution requires a decision record (enforced here, not in model)
- Automatic timestamp and user tracking on resolution
- Access control checks delegated to this layer

---

#### A.3 Add Resolution Fields to Risk Model (~20 min)

**File:** `backend/models/risk.py`

Add these fields to the `Risk` model:

```python
# Resolution tracking
decision_record: Optional[str] = None  # Required when closing
resolved_at: Optional[datetime] = None
resolved_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

# Relationship
resolved_by: Optional["User"] = Relationship()
```

**Migration Note:** SQLModel/SQLAlchemy will handle the migration. New fields are nullable so no data migration needed.

---

#### A.4 Update Risk Schemas (~15 min)

**File:** `backend/schemas/__init__.py`

```python
class RiskResolve(BaseModel):
    """Schema for resolving a risk."""
    status: RiskStatus  # Must be CLOSED or MITIGATED
    decision_record: str  # Required, non-empty

class RiskRead(RiskBase):
    """Schema for reading risk data."""
    id: uuid.UUID
    project_id: uuid.UUID
    decision_record: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = None
    
    class Config:
        from_attributes = True
```

---

#### A.5 Refactor `risks.py` Router (~30 min)

**File:** `backend/routers/risks.py`

Refactor to use `RiskService` instead of direct DB access:

```python
from dependencies import RiskServiceDep, CurrentUser

@router.get("/", response_model=List[RiskRead])
async def read_risks(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    risk_service: RiskServiceDep
):
    """Get all risks for a project."""
    return risk_service.get_project_risks(project_id, current_user)

@router.post("/{risk_id}/resolve", response_model=RiskRead)
async def resolve_risk(
    risk_id: uuid.UUID,
    data: RiskResolve,
    current_user: CurrentUser,
    risk_service: RiskServiceDep
):
    """Resolve a risk with a decision record."""
    return risk_service.resolve_risk(
        risk_id=risk_id,
        status=data.status,
        decision_record=data.decision_record,
        user=current_user
    )
```

**New Endpoints:**
- `POST /risks/{id}/resolve` - Resolve with decision record
- `POST /risks/{id}/reopen` - Reopen a resolved risk

---

#### A.6 Sync Frontend Types (~10 min)

**File:** `frontend/types/actions-risks.ts`

```typescript
export enum RiskStatus {
  OPEN = "Open",
  CLOSED = "Closed",
  MITIGATED = "Mitigated"  // Add this
}

export interface Risk {
  id: string;
  project_id: string;
  title?: string;  // New field that exists in backend
  description: string;
  probability: RiskProbability;
  impact: RiskImpact;
  status: RiskStatus;
  mitigation_plan?: string;
  // Resolution fields
  decision_record?: string;
  resolved_at?: string;
  resolved_by_id?: string;
}
```

---

#### A.7 Create Risk Resolution Hook (~20 min)

**File:** `frontend/hooks/useRisks.ts` (update)

```typescript
export const useResolveRisk = () => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ 
            riskId, 
            status, 
            decisionRecord 
        }: { 
            riskId: string; 
            status: RiskStatus; 
            decisionRecord: string 
        }) => {
            const { data } = await api.post(`/risks/${riskId}/resolve`, {
                status,
                decision_record: decisionRecord
            });
            return data;
        },
        onSuccess: (_, variables) => {
            // Invalidate risks cache
            queryClient.invalidateQueries({ queryKey: ["risks"] });
        }
    });
};
```

---

#### A.8 Update RiskList Dialog with Resolution UI (~45 min)

**File:** `frontend/components/project/RiskList.tsx`

Add to the Dialog content:

1. **For OPEN risks:** Add "Resolve Risk" button that expands a form:
   - Status dropdown: CLOSED or MITIGATED
   - Decision Record textarea (required)
   - "Confirm Resolution" button

2. **For CLOSED/MITIGATED risks:** Show:
   - Decision Record (read-only)
   - Resolved timestamp
   - "Reopen Risk" button (Cogniters only)

3. **Visual Indicators:**
   - Resolved risks get a muted/strikethrough style
   - Status badge updates with appropriate colors

**UI Mockup:**
```
┌─────────────────────────────────────────────┐
│ Risk Details                            [X] │
├─────────────────────────────────────────────┤
│ [HIGH Impact] [MEDIUM Probability]          │
│                                             │
│ Description text here...                    │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 📋 Mitigation Strategy                  │ │
│ │ Current mitigation plan text...         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ ✅ Resolve This Risk                    │ │
│ │                                         │ │
│ │ Status: [CLOSED ▼] or [MITIGATED ▼]    │ │
│ │                                         │ │
│ │ Decision Record: *                      │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ Explain how this risk was resolved │ │ │
│ │ │ or why it was accepted...          │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ │                                         │ │
│ │           [Cancel] [Confirm Resolution] │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

### Group B: Demo Infrastructure (Priority: Medium)

This group is independent and can be done in parallel.

#### B.1 Add Cloudflare Tunnel with Docker Compose Profiles (~20 min)

**File:** `docker-compose.yml`

```yaml
services:
  frontend:
    # ... existing config ...
    
  backend:
    # ... existing config ...
    
  db:
    # ... existing config ...

  # Demo tunnel service - only runs with --profile demo
  tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate --url http://frontend:3000
    depends_on:
      - frontend
    profiles:
      - demo
    restart: "no"

volumes:
  postgres_data:
  uploads_data:
```

**Usage:**
```bash
# Normal development
docker-compose up

# With public tunnel for demos
docker-compose --profile demo up
```

**Output:** The tunnel container logs will show a URL like:
```
tunnel: 2025-12-18T10:00:00Z INF +--------------------------------------------+
tunnel: 2025-12-18T10:00:00Z INF |  Your quick tunnel has been created!       |
tunnel: 2025-12-18T10:00:00Z INF |  https://random-name.trycloudflare.com     |
tunnel: 2025-12-18T10:00:00Z INF +--------------------------------------------+
```

---

#### B.2 Add Demo Mode Documentation (~10 min)

**File:** `README.md` (add section)

```markdown
## Demo Mode (Public Access)

For stakeholder demos, you can create a temporary public URL:

```bash
# Start all services including the tunnel
docker-compose --profile demo up
```

Look for the tunnel URL in the logs:
```
tunnel_1  | Your quick tunnel: https://random-name.trycloudflare.com
```

⚠️ **Security Notes:**
- The URL is temporary and changes on restart
- Your local environment is exposed to the internet
- Only run during active demos
- Stop with `Ctrl+C` when done
```

---

## Dependency Graph

```
┌──────────────────────────────────────────────────────────────┐
│                    Group A: Risk Architecture                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  A.1 RiskRepository ─────┐                                   │
│          │               │                                   │
│          ▼               ▼                                   │
│  A.2 RiskService ◄──── A.3 Risk Model                       │
│          │               │                                   │
│          ▼               ▼                                   │
│  A.4 Schemas ◄───────────┘                                   │
│          │                                                   │
│          ▼                                                   │
│  A.5 Router Refactor                                         │
│          │                                                   │
│          ▼                                                   │
│  A.6 Frontend Types ────► A.7 useResolveRisk Hook           │
│                                    │                         │
│                                    ▼                         │
│                          A.8 RiskList UI                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              Group B: Demo Infrastructure                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  B.1 Cloudflare Tunnel ────► B.2 Documentation              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Note: Groups A and B are independent and can be parallelized.
```

---

## Task Breakdown

| ID | Task | Estimated Time | Dependencies |
|----|------|----------------|--------------|
| A.1 | Create `RiskRepository` | 30 min | None |
| A.2 | Create `RiskService` with resolution logic | 45 min | A.1, A.3 |
| A.3 | Add resolution fields to Risk model | 20 min | None |
| A.4 | Update Risk schemas | 15 min | A.3 |
| A.5 | Refactor `risks.py` router | 30 min | A.2, A.4 |
| A.6 | Sync frontend types | 10 min | A.3 |
| A.7 | Create `useResolveRisk` hook | 20 min | A.5, A.6 |
| A.8 | Update RiskList dialog UI | 45 min | A.7 |
| B.1 | Add Cloudflare Tunnel service | 20 min | None |
| B.2 | Add demo mode documentation | 10 min | B.1 |

**Total Estimated Time:** ~4 hours

---

## Test Plan

### Unit Tests (TDD Approach)

**`tests/unit/services/test_risk_service.py`:**

```python
class TestResolveRisk:
    def test_resolve_risk_requires_decision_record(self):
        """Cannot resolve without decision record."""
        
    def test_resolve_risk_rejects_open_status(self):
        """Cannot 'resolve' to OPEN status."""
        
    def test_resolve_sets_timestamp_and_user(self):
        """Resolution auto-populates resolved_at and resolved_by."""
        
    def test_reopen_clears_resolution_fields(self):
        """Reopening removes resolution data."""
```

### Integration Tests

**`tests/integration/test_risk_endpoints.py`:**

```python
class TestRiskResolution:
    def test_resolve_risk_endpoint_success(self):
        """POST /risks/{id}/resolve works with valid data."""
        
    def test_resolve_risk_requires_auth(self):
        """Unauthenticated requests get 401."""
        
    def test_resolve_risk_requires_decision_record(self):
        """Empty decision record returns 422."""
        
    def test_client_can_resolve_assigned_project_risk(self):
        """Clients can resolve risks on their assigned projects."""
        
    def test_client_cannot_resolve_unassigned_project_risk(self):
        """Clients get 403 for unassigned projects."""
```

---

## Acceptance Criteria

### Risk Resolution Feature
- [ ] Risks can be resolved with status CLOSED or MITIGATED
- [ ] Decision record is required (non-empty string)
- [ ] `resolved_at` and `resolved_by` are automatically set
- [ ] Resolved risks display decision record in UI
- [ ] Resolved risks have visual distinction (muted style)
- [ ] Cogniters can reopen resolved risks
- [ ] All access control rules are enforced

### Demo Infrastructure
- [ ] `docker-compose --profile demo up` starts tunnel
- [ ] Tunnel URL appears in container logs
- [ ] External network can access the app via tunnel URL
- [ ] Regular `docker-compose up` does NOT start tunnel

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SQLModel migration issues | Low | Medium | Test migration on fresh DB first |
| Frontend/Backend type drift | Medium | Low | TypeScript catches at compile time |
| Tunnel rate limiting | Low | Low | Only used for short demos |

---

## Open Questions

1. **Should clients be able to resolve risks?** 
   - Current assumption: Yes, on their assigned projects
   - Alternative: Only Cogniters can resolve

2. **Should reopening require a reason?**
   - Current assumption: No, simple reopen
   - Alternative: Require "reopen reason" field

3. **Should we add email notifications on resolution?**
   - Current assumption: Out of scope for Phase 1
   - Can be added in Phase 2 with comment notifications

