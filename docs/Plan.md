# Implementation Plan

## Phase 0: Stabilization (COMPLETED)
- [x] **Token Storage Bug**: Fixed Zustand persist config to include accessToken.
- [x] **React Query Setup**: Added QueryClientProvider and DevTools.
- [x] **Toast Notifications**: Replaced all alert() calls with Sonner toasts.
- [x] **Component Migration**: Migrated all data-fetching components to React Query hooks.
- [x] **Removed Refresh Hack**: Dashboard now uses React Query's automatic cache invalidation.

## Phase 1: Foundation & Authentication (COMPLETED)
- [x] **Docker Setup**: Create `docker-compose.yml` with services for Frontend (Next.js), Backend (FastAPI), and Database (PostgreSQL).
- [x] **Backend Setup**: Initialize FastAPI project with SQLAlchemy/SQLModel for DB access.
- [x] **Frontend Setup**: Initialize Next.js project with Shadcn UI.
- [x] **Database Schema**: Define tables for Users, Projects, Actions, Risks in Python models.
- [x] **Authentication (Google SSO)**: Firebase Google provider enabled, working with popup sign-in.
- [x] **Authentication (Email/Password)**: Email/password registration and sign-in working, includes forgot password flow.
- [x] **Role Management**: Auto-assigns Cogniter role to @cognite.com emails, Client role to all others.

## Phase 2: Core UI & Project Management (COMPLETED)
- [x] **Landing Page**: Build the dashboard for Cogniters (Project list) and Clients.
- [x] **Project Creation**: Build the "Create New Project" form.
- [x] **Project API**: Implement CRUD endpoints in FastAPI.

## Phase 3: Integrations (IN PROGRESS)
- [ ] **Jira Client**: Connect to Jira API, fetch projects/issues/sprints with connection validation.
- [ ] **Precursive Client**: Connect to Salesforce API, fetch project details/financials with connection validation.
- [ ] **Sync Endpoints**: Manual trigger endpoints to sync data from external sources.
- [ ] **Connection Validation**: Verify credentials work and fail fast if misconfigured.

## Phase 3.5: Fail-Fast & Debugging
- [ ] **Structured Logging**: Add Python `structlog` with JSON output and request IDs.
- [ ] **Error Boundaries**: React error boundaries with detailed error display in dev mode.
- [ ] **API Error Responses**: Consistent error schema with stack traces in dev mode.
- [ ] **Health Checks**: `/health` endpoint showing DB, Jira, Precursive connection status.
- [ ] **Environment Validation**: Fail on startup if required env vars are missing.

## Phase 4: Visual Showpieces (The "Wow")
- [ ] **Timeline**: Gantt chart with parent-child relationships, progress bars.
- [ ] **Risk Matrix**: Interactive heatmap (Probability vs Impact).
- [ ] **Health Dashboard**: Animated status indicators.

## Phase 5: Data Depth
- [ ] **Action Register**: Full CRUD with commenting.
- [ ] **Financials**: Budget widgets with real data from Precursive.
- [ ] **Sprint Goals**: Display component with data from Jira.

## Phase 6: Refinement & Polish
- [ ] **ProtectedLayout**: Create wrapper component to remove auth boilerplate from pages.
- [ ] **Loading Skeletons**: Replace spinners with skeleton screens.
- [ ] **Responsive Design**: Ensure mobile compatibility.
- [ ] **Testing**: Basic API and UI tests.
