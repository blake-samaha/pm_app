# Product Requirements Document: Project Status & Automation Portal

**Document Version:** 2.1  
**Date:** December 21, 2025  
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
| Jira Integration | 🟡 Partial (sync works, expanded data capture needed) |
| Precursive Integration | 🟡 Partial (health sync works, financials incomplete) |
| Risk Management | 🟡 Partial (missing decision record field) |
| Client Collaboration Features | ❌ Not Started |
| Financials Module | 🟡 Partial (sync architecture ready, data mapping needed) |
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

---

## 3. Integration Data Expansion (NEW)

These items address gaps in data capture from external integrations. Currently, we're only pulling a subset of available fields from Jira and Precursive.

### 3.1 Precursive Financials Expansion

| Attribute | Detail |
|-----------|--------|
| **Problem** | Precursive sync succeeds but financials show as unavailable. The fields we query (`Total_FTEs__c`, `FTE_Day_Price__c`) are often null in Salesforce. |
| **Root Cause** | We only query 5 financial fields, but Salesforce has 15+ budget-related fields available. |
| **Priority** | P0 - Blocking financials display |

**Current Fields Queried:**
- `CurrencyIsoCode`, `Remaining_Budget__c`, `FTE_Day_Price__c`, `Total_FTEs__c`, `Overrun_Investment__c`

**Additional Fields to Add:**
| Salesforce Field | Label | Sample Value |
|------------------|-------|--------------|
| `PM_Budget__c` | PM Budget | 0.0 |
| `SA_Budget__c` | SA Budget | 0.0 |
| `DE_Budget__c` | DE Budget | 0.0 |
| `DS_Budget__c` | DS Budget | 0.0 |
| `Budgeted_Days_in_Delivery_Phase__c` | Budgeted Days in Delivery | null |
| `Budgeted_Hours_in_Delivery_Phase__c` | Budgeted Hours in Delivery | 0.0 |
| `Total_Days_Actuals_Planned__c` | Total Days (Actuals + Planned) | 1387.17 |
| `Remaining_Budget_in_Fees_org__c` | Remaining Budget (Org Currency) | 0.0 |

**Implementation Tasks:**
- [ ] Add field constants to `salesforce_schema.py`
- [ ] Expand `PrecursiveFinancials` dataclass in `models.py`
- [ ] Update `field_mapper.py` to map new fields
- [ ] Add debug logging to `salesforce_precursive_client.py` to log raw Salesforce responses
- [ ] Update `sync_service.py` to use additional budget fields as fallback
- [ ] Add computed `total_budget` logic (sum of role budgets if FTE fields are null)

**Estimated Effort:** 1-2 hours

---

### 3.2 Jira Data Expansion - Standard Fields

| Attribute | Detail |
|-----------|--------|
| **Problem** | We only capture 8 Jira fields, missing valuable context like descriptions, labels, and time tracking. |
| **Goal** | Pull all available standard Jira data and store in database for richer reporting. |
| **Priority** | P1 |

**Current Fields Captured:**
- `summary`, `status`, `issuetype`, `assignee`, `priority`, `created`, `updated`, `duedate`

**Standard Fields to Add (Phase 1):**
| Jira Field | Description | Value |
|------------|-------------|-------|
| `description` | Full issue description (rich text) | High |
| `reporter` | Who created the issue | Medium |
| `labels` | Array of labels/tags | Medium |
| `components` | Project components | Medium |
| `resolution` | How it was resolved | Medium |
| `resolutiondate` | When resolved | Medium |
| `parent` | Parent issue (for subtasks) | Medium |

**Implementation Tasks:**
- [ ] Expand `JiraIssue` dataclass with new fields
- [ ] Add columns to `ActionItem` model: `description`, `reporter`, `labels`, `components`, `resolution`, `resolved_at`, `parent_key`, `jira_created_at`, `jira_updated_at`
- [ ] Update Jira API request to include new fields
- [ ] Update field mapping in `get_project_issues()`
- [ ] Update sync service to populate new columns
- [ ] Handle database migration (reset or ALTER TABLE)

**Estimated Effort:** 1-2 hours

---

### 3.3 Jira Data Expansion - Time Tracking

| Attribute | Detail |
|-----------|--------|
| **Problem** | No time tracking data captured from Jira. |
| **Goal** | Enable burndown charts and capacity tracking. |
| **Priority** | P2 |

**Fields to Add:**
| Jira Field | Description |
|------------|-------------|
| `timeoriginalestimate` | Original time estimate (seconds) |
| `timeestimate` | Remaining time estimate (seconds) |
| `timespent` | Actual time logged (seconds) |

**Implementation Tasks:**
- [ ] Add `time_estimate_seconds`, `time_remaining_seconds`, `time_spent_seconds` to `ActionItem` model
- [ ] Add fields to `JiraIssue` dataclass
- [ ] Update API request and field mapping
- [ ] Update sync service

**Estimated Effort:** 1 hour

---

### 3.4 Jira Data Expansion - Custom Fields (Sprint, Story Points)

| Attribute | Detail |
|-----------|--------|
| **Problem** | Sprint and story points are stored as custom fields with instance-specific IDs. |
| **Complexity** | Requires custom field discovery or configuration. |
| **Priority** | P2 |

**Fields to Add:**
| Field | Notes |
|-------|-------|
| `sprint` | Custom field ID varies by Jira instance |
| `story_points` | Custom field ID varies by Jira instance |

**Implementation Tasks:**
- [ ] Add discovery endpoint: `GET /jira/fields` to fetch custom field metadata
- [ ] Add configuration for custom field IDs (env vars or project-level settings)
- [ ] Add `sprint_id`, `sprint_name`, `story_points` to `ActionItem` model
- [ ] Update sync service to map custom fields

**Estimated Effort:** 2-3 hours

---

## 4. High-Value Features ("Ah-Ha!" Requirements)

These features represent the key breakthroughs from the PoC requirements gathering session.

### 4.1 Client-Facing "Data Shielding" (Jira Label Filtering)

| Attribute | Detail |
|-----------|--------|
| **Insight** | Internal Jira boards are often too noisy for clients |
| **Current State** | Jira sync pulls all issues; no label filtering implemented |
| **Requirement** | Implement filtering mechanism using Jira Labels. Only stories tagged with a configurable "Client-Facing" label will be synced and displayed |
| **Priority** | P1 |

**Implementation Notes:**
- Add `client_facing_label` field to Project model (default: "client-facing")
- Modify `SyncService.sync_jira_issues()` to filter by label
- Add toggle in Edit Project Modal for enabling/disabling client filtering

### 4.2 Visual Sprint Progress Bar

| Attribute | Detail |
|-----------|--------|
| **Insight** | Clients prioritize understanding "where we are in the current cycle" |
| **Current State** | `Timeline.tsx` shows project-level dates, not sprint-level progress |
| **Requirement** | Visual two-week timeline showing current date relative to sprint start/end, status distribution of stories |
| **Priority** | P1 |

**Implementation Notes:**
- Create new `SprintProgressBar.tsx` component
- Fetch active sprint data from Jira via existing `jira_board_id`
- Show story status breakdown (To Do / In Progress / Done) as segmented progress bar
- Display sprint name, start date, end date, and "today" marker

### 4.3 Micro-Communication (Per-Story Chat)

| Attribute | Detail |
|-----------|--------|
| **Insight** | Status questions often get lost in email or Slack threads |
| **Current State** | `Comment` model exists but **no UI exists** |
| **Requirement** | Add "Chat" column to action register with side-drawer comment thread |
| **Priority** | P1 |

**Implementation Notes:**
- Create `CommentDrawer.tsx` component (slide-out panel)
- Add comment count badge to ActionTable rows
- Implement `useComments(actionItemId)` hook
- Add `POST /actions/{id}/comments` and `GET /actions/{id}/comments` endpoints

### 4.4 Risk Resolution & Decision Records

| Attribute | Detail |
|-----------|--------|
| **Insight** | Precursive lacks "Resolved" status for risks, leading to stale risk logs |
| **Current State** | `RiskStatus` enum exists but **no Decision Record field** |
| **Requirement** | Add Decision Record text field to capture how a risk was mitigated |
| **Priority** | P1 |

**Implementation Notes:**
- Add `decision_record: Optional[str]` field to Risk model
- Add `resolved_at: Optional[datetime]` and `resolved_by: Optional[UUID]` fields
- Update RiskList dialog to show/edit decision record when status is CLOSED/MITIGATED

---

## 5. Functional Requirements

### 5.1 Project Interface

| Feature | Status | Notes |
|---------|--------|-------|
| Project Creation (Name, URLs, Logo) | ✅ Complete | `CreateProjectModal.tsx` |
| Health Status Override | ✅ Complete | Manual override in Edit Modal |
| Publish/Unpublish Actions | ✅ Complete | `POST /projects/{id}/publish` |
| Logo Upload | ✅ Complete | File upload + URL input modes |
| Risk Heat Map | ✅ Complete | `RiskMatrix.tsx` with clickable filtering |
| Edit Project Modal | ✅ Complete | Multi-tab: Details, Sprint, Branding |

### 5.2 Interactive Action Register

| Feature | Status | Notes |
|---------|--------|-------|
| View Actions with Filters | ✅ Complete | Status, Priority, Assignee, Due Date filters |
| Link to Jira Issues | ✅ Complete | External link if jira_url configured |
| Editable Status (by Client) | ❌ Not Started | Clients need ability to mark tasks "Done" |
| Editable Priority (by Client) | ❌ Not Started | Allow priority adjustments |
| Comment Thread (Chat) | ❌ Not Started | See Section 4.3 |

### 5.3 Risk Register

| Feature | Status | Notes |
|---------|--------|-------|
| View Risks with Filters | ✅ Complete | Search, pagination, sorting by score |
| Risk Matrix (Heatmap) | ✅ Complete | Clickable filter grid |
| Risk Detail Dialog | ✅ Complete | Shows description, mitigation, score |
| Close/Resolve Risk | 🟡 Partial | Status exists, needs Decision Record UI |
| Decision Record Field | ❌ Not Started | See Section 4.4 |

### 5.4 Team Management

| Feature | Status | Notes |
|---------|--------|-------|
| View Assigned Users | ✅ Complete | `TeamSection.tsx` |
| Assign Users | ✅ Complete | Search and add modal |
| Invite by Email | ✅ Complete | Creates pending placeholder user |
| Remove Users | ✅ Complete | X button on user row |

### 5.5 Financials & Budgeting

| Feature | Status | Notes |
|---------|--------|-------|
| Budget Fields on Project | ✅ Complete | `total_budget`, `spent_budget`, `remaining_budget` |
| FinancialsCard UI | ✅ Complete | Shows budget breakdown |
| Precursive Health Sync | ✅ Complete | Syncs project/time/cost/resources health |
| Precursive Financials Sync | 🟡 Partial | Schema mismatch - see Section 3.1 |
| Fixed Price vs T&M Logic | ❌ Not Started | Requires schema definition from Vince/Hana |

---

## 6. Technical Requirements & Integrations

### 6.1 Jira Integration

| Capability | Status | Notes |
|------------|--------|-------|
| Connect via API | ✅ Complete | `JiraClient` with API Token auth |
| Fetch Projects | ✅ Complete | |
| Fetch Issues/Stories | ✅ Complete | Basic fields only |
| Fetch Active Sprint | ✅ Complete | Via `jira_board_id` |
| Extended Issue Fields | ❌ Not Started | See Section 3.2-3.4 |
| Label-based Filtering | ❌ Not Started | Required for Data Shielding |
| Connection Validation | 🟡 Partial | Needs fail-fast on bad credentials |

### 6.2 Precursive/Salesforce Integration

| Capability | Status | Notes |
|------------|--------|-------|
| Connect via Salesforce API | ✅ Complete | OAuth2 JWT Bearer flow |
| Fetch Project Details | ✅ Complete | Health indicators syncing |
| Fetch Financial Data | 🟡 Partial | Fields null - see Section 3.1 |
| Debug Logging | ❌ Not Started | Need to log raw API responses |
| Extended Budget Fields | ❌ Not Started | See Section 3.1 |
| Connection Validation | ✅ Complete | |

### 6.3 Authentication

| Capability | Status | Notes |
|------------|--------|-------|
| Google SSO | ✅ Complete | Firebase Auth |
| Email/Password | ✅ Complete | Firebase Auth |
| Role Auto-Assignment | ✅ Complete | `@cognite.com` → Cogniter, else → Client |
| Token Storage | ✅ Complete | Zustand persist |

### 6.4 Ephemeral Public Access (PoC Demos)

| Capability | Status | Notes |
|------------|--------|-------|
| Cloudflare Tunnel Integration | ❌ Not Started | Zero-cost public URL for demos |
| Docker Compose Service | ❌ Not Started | New `tunnel` service |

---

## 7. Implementation Roadmap

### Phase 1: Integration Data Fixes (THIS WEEK - P0/P1)

**Goal:** Fix blocking integration issues and expand data capture.

#### 1A: Precursive Financials (~2 hours)
- [ ] Add all budget field constants to `salesforce_schema.py`
- [ ] Expand `PrecursiveFinancials` dataclass with 8 new fields
- [ ] Update `field_mapper.py` to map new fields
- [ ] Add debug logging to `salesforce_precursive_client.py`
- [ ] Update `sync_service.py` financials logic with fallback calculation
- [ ] Test with real Precursive project

#### 1B: Jira Standard Fields (~2 hours)
- [ ] Expand `JiraIssue` dataclass with description, reporter, labels, etc.
- [ ] Add new columns to `ActionItem` model
- [ ] Update Jira API request to fetch additional fields
- [ ] Update sync service field mapping
- [ ] Database migration (ALTER TABLE or reset)

### Phase 2: Client Collaboration Features (Week 2)

- [ ] **Comment System UI:**
    - [ ] Create `CommentDrawer.tsx` slide-out panel
    - [ ] Add `GET/POST /actions/{id}/comments` endpoints
    - [ ] Add `useComments` hook
    - [ ] Add comment count badge to ActionTable
- [ ] **Client Edit Permissions:**
    - [ ] Add `PATCH /actions/{id}` endpoint with permission checks
    - [ ] Add inline status/priority editing for authorized users

### Phase 3: Sprint Visibility & Risk Enhancements (Week 3)

- [ ] **Sprint Progress Bar:**
    - [ ] Create `SprintProgressBar.tsx` component
    - [ ] Extend Jira sync to cache sprint story counts by status
    - [ ] Display on project detail page above Action Register
- [ ] **Jira Label Filtering:**
    - [ ] Add `client_facing_label` to Project model
    - [ ] Modify sync to filter by label
    - [ ] Add configuration UI in Edit Project Modal
- [ ] **Risk Decision Records:**
    - [ ] Add `decision_record` field to Risk model
    - [ ] Create Risk close/resolve UI with decision record input

### Phase 4: Extended Jira Data (Week 4)

- [ ] **Time Tracking Fields:**
    - [ ] Add time estimate/spent columns to ActionItem
    - [ ] Update Jira sync to capture time fields
- [ ] **Custom Fields (Sprint/Story Points):**
    - [ ] Add custom field discovery endpoint
    - [ ] Add configuration for field IDs
    - [ ] Update sync to map custom fields

### Phase 5: Polish & Testing (Week 5)

- [ ] Loading skeletons for all async components
- [ ] Error boundaries at page level
- [ ] Accessibility audit (ARIA labels, keyboard navigation)
- [ ] E2E tests for critical user flows
- [ ] **Demo Infrastructure:** Add Cloudflare Tunnel service to `docker-compose.yml`

---

## 8. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | What is the exact Jira label name for "client-facing" stories? | Vince | Pending |
| 2 | ~~Precursive API credentials?~~ | ~~Vince~~ | ✅ Resolved |
| 3 | Fixed Price vs T&M: What fields from Precursive determine project type? | Hana/Vince | Pending |
| 4 | Should comment notifications be email-based or in-app? | Blake | Open |
| 5 | Do we need comment @mentions? | Blake | Open |
| 6 | Which Jira custom field IDs are used for Story Points and Sprint? | Blake | **NEW** - Need to discover |

---

## 9. Appendix: Existing Architecture Reference

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
| Jira Client | `backend/integrations/jira_client.py` |
| Precursive Client | `backend/integrations/salesforce_precursive_client.py` |
| Precursive Schema | `backend/integrations/precursive/salesforce_schema.py` |
| Precursive Models | `backend/integrations/precursive/models.py` |
| Field Mapper | `backend/integrations/precursive/field_mapper.py` |
| Sync Service | `backend/services/sync_service.py` |
| Action Table UI | `frontend/components/project/ActionTable.tsx` |
| Risk List UI | `frontend/components/project/RiskList.tsx` |
| Risk Matrix UI | `frontend/components/project/RiskMatrix.tsx` |
| Financials Card UI | `frontend/components/project/FinancialsCard.tsx` |
