# Product Requirements Document: Project Status & Automation Portal

**Document Version:** 2.0  
**Date:** December 18, 2025  
**Status:** Active Development  
**Stakeholders:** Vince Kapadia, Hana Kabazi, Blake Samaha

---

## 1. Executive Summary

The **Project Status & Automation Portal** is a collaborative interface designed to bridge the gap between internal project management tools (Jira, Precursive) and client-facing status reporting. The primary objective is to automate manual PM reporting efforts while providing clients with a "clean," actionable view of project health, sprint progress, and risk mitigation.

### 1.1 Current State Summary

| Category | Status |
|----------|--------|
| Authentication | ✅ Complete (Google SSO + Email/Password) |
| User Roles & Access Control | ✅ Complete (Cogniter/Client + Financials/Client) |
| Project CRUD | ✅ Complete |
| Team Assignment & Invitations | ✅ Complete |
| Jira Integration | 🟡 Partial (sync works, label filtering needed) |
| Precursive Integration | 🟡 Partial (credentials configured, full sync pending) |
| Risk Management | 🟡 Partial (missing decision record field) |
| Client Collaboration Features | ❌ Not Started |
| Financials Module | ❌ Not Started (Phase 2) |
| Ephemeral Demo Access | ❌ Not Started (Cloudflare Tunnel) |

---

## 2. User Personas & Access Control

Access is governed by three distinct personas. Each level builds upon the visibility of the previous tier.

| Persona | Description | Permissions |
|---------|-------------|-------------|
| **Internal (Cogniter)** | Internal team members / PMs (`@cognite.com` emails) | Full access: Jira dashboards, financial overrides, project creation, all client views, user management |
| **Client + Financials** | Senior client stakeholders | Sprint progress, action registers, financial/budgeting module (burn rates, T&M vs. Fixed Price) |
| **Client** | Standard client stakeholders | Sprint progress, filtered Jira stories, ability to comment and update status on assigned tasks |

### 2.1 ✅ Security Fix (Completed)

> **Issue:** Unassigned new users could previously see all ongoing projects.  
> **Resolution:** Users now only see projects to which they are explicitly assigned.  
> **Priority:** P0 - ~~Fix immediately before next deployment.~~ **COMPLETED**  
> **Status:** ✅ Fixed and verified with comprehensive integration tests.
> 
> **Implementation Details:**
> - Backend logic in `ProjectService.get_user_projects()` correctly filters projects for all client roles
> - `actions.py` and `risks.py` routers now use centralized `project_service.user_has_access_to_project()` check
> - Added `CLIENT_FINANCIALS` role with same project-assignment requirement as `CLIENT`
> - Comprehensive integration tests added in `tests/integration/test_project_endpoints.py` (8 test cases)

---

## 3. High-Value Features ("Ah-Ha!" Requirements)

These features represent the key breakthroughs from the PoC requirements gathering session and should be prioritized in the next sprint.

### 3.1 Client-Facing "Data Shielding" (Jira Label Filtering)

| Attribute | Detail |
|-----------|--------|
| **Insight** | Internal Jira boards are often too noisy for clients |
| **Current State** | Jira sync pulls all issues; no label filtering implemented |
| **Requirement** | Implement filtering mechanism using Jira Labels. Only stories tagged with a configurable "Client-Facing" label will be synced and displayed |
| **Goal** | Eliminate manual filtering and report generation by PMs |
| **Priority** | P1 |

**Implementation Notes:**
- Add `client_facing_label` field to Project model (default: "client-facing")
- Modify `SyncService.sync_jira_issues()` to filter by label
- Add toggle in Edit Project Modal for enabling/disabling client filtering

### 3.2 Visual Sprint Progress Bar

| Attribute | Detail |
|-----------|--------|
| **Insight** | Clients prioritize understanding "where we are in the current cycle" over seeing a raw backlog list |
| **Current State** | `Timeline.tsx` shows project-level dates, not sprint-level progress |
| **Requirement** | Develop a visual two-week timeline graphic showing: current date relative to sprint start/end, status distribution of stories within that sprint |
| **Goal** | Provide "healthy" visibility by focusing on the active sprint |
| **Priority** | P1 |

**Implementation Notes:**
- Create new `SprintProgressBar.tsx` component
- Fetch active sprint data from Jira via existing `jira_board_id`
- Show story status breakdown (To Do / In Progress / Done) as segmented progress bar
- Display sprint name, start date, end date, and "today" marker

### 3.3 Micro-Communication (Per-Story Chat)

| Attribute | Detail |
|-----------|--------|
| **Insight** | Status questions often get lost in email or Slack threads |
| **Current State** | `Comment` model exists and is linked to `ActionItem`, but **no UI exists** |
| **Requirement** | Add a "Chat" column to the action register. Clicking triggers a side-drawer with a dedicated comment thread |
| **Goal** | Centralize communication directly within the context of the work item |
| **Priority** | P1 |

**Implementation Notes:**
- Create `CommentDrawer.tsx` component (slide-out panel)
- Add comment count badge to ActionTable rows
- Implement `useComments(actionItemId)` hook
- Add `POST /actions/{id}/comments` and `GET /actions/{id}/comments` endpoints
- Real-time updates optional (Phase 2 with WebSockets)

### 3.4 Risk Resolution & Decision Records

| Attribute | Detail |
|-----------|--------|
| **Insight** | Precursive lacks a native "Resolved" or "Closed" status for risks, leading to stale risk logs |
| **Current State** | `RiskStatus` enum has `OPEN`, `CLOSED`, `MITIGATED` but **no Decision Record field** |
| **Requirement** | Add "Closed/Resolved" toggle and a Decision Record text field to capture how a risk was mitigated or why it was accepted |
| **Goal** | Provide superior risk management capabilities that exceed the source enterprise tool |
| **Priority** | P1 |

**Implementation Notes:**
- Add `decision_record: Optional[str]` field to Risk model
- Add `resolved_at: Optional[datetime]` and `resolved_by: Optional[UUID]` fields
- Update RiskList dialog to show/edit decision record when status is CLOSED/MITIGATED
- Add quick-action button to close a risk with required decision record

---

## 4. Functional Requirements

### 4.1 Project Interface

| Feature | Status | Notes |
|---------|--------|-------|
| Project Creation (Name, URLs, Logo) | ✅ Complete | `CreateProjectModal.tsx` |
| Health Status Override | ✅ Complete | Manual override in Edit Modal |
| Publish/Unpublish Actions | ✅ Complete | `POST /projects/{id}/publish` |
| Logo Upload | ✅ Complete | File upload + URL input modes |
| Risk Heat Map | ✅ Complete | `RiskMatrix.tsx` with clickable filtering |
| Edit Project Modal | ✅ Complete | Multi-tab: Details, Sprint, Branding |

### 4.2 Interactive Action Register

| Feature | Status | Notes |
|---------|--------|-------|
| View Actions with Filters | ✅ Complete | Status, Priority, Assignee, Due Date filters |
| Link to Jira Issues | ✅ Complete | External link if jira_url configured |
| Editable Status (by Client) | ❌ Not Started | Clients need ability to mark tasks "Done" |
| Editable Priority (by Client) | ❌ Not Started | Allow priority adjustments |
| Comment Thread (Chat) | ❌ Not Started | See Section 3.3 |

**Client Edit Permissions Implementation:**
- Add `PATCH /actions/{id}` endpoint
- Allow Clients to update `status` and `priority` only for actions assigned to them
- Add inline edit controls to ActionTable for authorized users

### 4.3 Risk Register

| Feature | Status | Notes |
|---------|--------|-------|
| View Risks with Filters | ✅ Complete | Search, pagination, sorting by score |
| Risk Matrix (Heatmap) | ✅ Complete | Clickable filter grid |
| Risk Detail Dialog | ✅ Complete | Shows description, mitigation, score |
| Close/Resolve Risk | 🟡 Partial | Status exists, needs Decision Record UI |
| Decision Record Field | ❌ Not Started | See Section 3.4 |

### 4.4 Team Management

| Feature | Status | Notes |
|---------|--------|-------|
| View Assigned Users | ✅ Complete | `TeamSection.tsx` |
| Assign Users | ✅ Complete | Search and add modal |
| Invite by Email | ✅ Complete | Creates pending placeholder user |
| Remove Users | ✅ Complete | X button on user row |

### 4.5 Financials & Budgeting (Phase 2)

| Feature | Status | Notes |
|---------|--------|-------|
| Budget Fields on Project | ✅ Complete | `total_budget`, `spent_budget`, `remaining_budget` |
| FinancialsCard UI | 🟡 Partial | Exists with mock data |
| Precursive Data Sync | ❌ Not Started | Credentials ready, implementation pending |
| Fixed Price vs T&M Logic | ❌ Not Started | Requires schema definition from Vince/Hana |

**Blocking Action Items:**
- **Hana & Vince:** Define data schema mapping for Fixed Price vs T&M accounting

---

## 5. Technical Requirements & Integrations

### 5.1 Jira Integration

| Capability | Status | Notes |
|------------|--------|-------|
| Connect via API | ✅ Complete | `JiraClient` with OAuth |
| Fetch Projects | ✅ Complete | |
| Fetch Issues/Stories | ✅ Complete | |
| Fetch Active Sprint | ✅ Complete | Via `jira_board_id` |
| Label-based Filtering | ❌ Not Started | Required for Data Shielding |
| Connection Validation | 🟡 Partial | Needs fail-fast on bad credentials |

### 5.2 Precursive/Salesforce Integration

| Capability | Status | Notes |
|------------|--------|-------|
| Connect via Salesforce API | ✅ Complete | Credentials configured in `.env` |
| Fetch Project Details | ❌ Not Started | |
| Fetch Financial Data | ❌ Not Started | |
| Connection Validation | ❌ Not Started | |

### 5.3 Authentication

| Capability | Status | Notes |
|------------|--------|-------|
| Google SSO | ✅ Complete | Firebase Auth |
| Email/Password | ✅ Complete | Firebase Auth |
| Role Auto-Assignment | ✅ Complete | `@cognite.com` → Cogniter, else → Client |
| Token Storage | ✅ Complete | Zustand persist fixed |

### 5.4 Ephemeral Public Access (PoC Demos)

| Capability | Status | Notes |
|------------|--------|-------|
| Cloudflare Tunnel Integration | ❌ Not Started | Zero-cost public URL for demos |
| Docker Compose Service | ❌ Not Started | New `tunnel` service |

**Objective:** Enable developers to spin up the full stack locally and generate a temporary public URL for external stakeholder demos without cloud deployment.

**Proposed Solution:** Integrate Cloudflare Quick Tunnel into `docker-compose.yml`

```yaml
# Add to docker-compose.yml
tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --url http://frontend:3000
    depends_on:
        - frontend
    networks:
        - default
```

**Workflow:**
1. Developer runs `docker-compose up`
2. Tunnel service outputs link: `https://random-name.trycloudflare.com`
3. Share link with stakeholder for instant demo access

**Constraints:**
- ⚠️ **Ephemeral:** URL changes on every container restart
- ⚠️ **Security:** Exposes local environment to internet (run only during active demos)
- ✅ **Cost:** Free (Cloudflare anonymous Quick Tunnel)
- ⚠️ **Uptime:** Requires host machine to stay awake

**Acceptance Criteria:**
- [ ] `docker-compose up` spins up stack + tunnel
- [ ] Tunnel logs display valid `https://*.trycloudflare.com` URL
- [ ] External network access (e.g., 4G mobile) successfully loads the app

---

## 6. Implementation Roadmap

### Phase 1: Security & Critical Fixes (Week 1)
- [x] **P0:** Verify and fix user access control bug (unassigned users seeing all projects)
- [x] **P0:** Add integration tests for access control
- [x] **P0:** Implement three-tier user role system (Cogniter/Client + Financials/Client)
- [x] **P0:** Add `PATCH /users/{id}/role` endpoint for role management
- [x] **P0:** Gate FinancialsCard visibility by role (`canViewFinancials` permission)
- [ ] Add `decision_record` field to Risk model (backend migration)
- [ ] Create Risk close/resolve UI with decision record input
- [ ] **Demo Infrastructure:** Add Cloudflare Tunnel service to `docker-compose.yml` for PoC demos

### Phase 2: Client Collaboration Features (Weeks 2-3)
- [ ] **Comment System UI:**
    - [ ] Create `CommentDrawer.tsx` slide-out panel
    - [ ] Add `GET/POST /actions/{id}/comments` endpoints
    - [ ] Add `useComments` hook
    - [ ] Add comment count badge to ActionTable
- [ ] **Client Edit Permissions:**
    - [ ] Add `PATCH /actions/{id}` endpoint with permission checks
    - [ ] Add inline status/priority editing for authorized users

### Phase 3: Sprint Visibility (Week 3)
- [ ] **Sprint Progress Bar:**
    - [ ] Create `SprintProgressBar.tsx` component
    - [ ] Extend Jira sync to cache sprint story counts by status
    - [ ] Display on project detail page above Action Register
- [ ] **Jira Label Filtering:**
    - [ ] Add `client_facing_label` to Project model
    - [ ] Modify sync to filter by label
    - [ ] Add configuration UI in Edit Project Modal

### Phase 4: Precursive & Financials (Weeks 4-5)
- [ ] Complete Precursive API integration (credentials ready ✅)
- [ ] Wire FinancialsCard to real data
- [ ] Implement Fixed Price vs T&M display logic

### Phase 5: Polish & Testing (Week 6)
- [ ] Loading skeletons for all async components
- [ ] Error boundaries at page level
- [ ] Accessibility audit (ARIA labels, keyboard navigation)
- [ ] E2E tests for critical user flows

---

## 7. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | What is the exact Jira label name for "client-facing" stories? | Vince | Pending |
| 2 | ~~Precursive API credentials?~~ | ~~Vince~~ | ✅ Resolved |
| 3 | Fixed Price vs T&M: What fields from Precursive determine project type? | Hana/Vince | Pending |
| 4 | Should comment notifications be email-based or in-app? | Blake | Open |
| 5 | Do we need comment @mentions? | Blake | Open |

---

## 8. Appendix: Existing Architecture Reference

### Backend Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLModel
- **Auth:** Firebase (Google + Email/Password)

### Frontend Stack
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + Shadcn UI
- **State:** TanStack Query + Zustand
- **API Client:** Axios

### Key Files
| Area | File/Directory |
|------|----------------|
| Project Model | `backend/models/project.py` |
| Risk Model | `backend/models/risk.py` |
| Action Model | `backend/models/action_item.py` |
| Jira Sync | `backend/services/sync_service.py` |
| Action Table UI | `frontend/components/project/ActionTable.tsx` |
| Risk List UI | `frontend/components/project/RiskList.tsx` |
| Risk Matrix UI | `frontend/components/project/RiskMatrix.tsx` |
