# Project Roadmap & Remaining Tasks

Based on the gap analysis between the current implementation and `docs/Automated Project Management Tools (1).md`.

## 1. Project Management & Editing
**Priority:** High
**Goal:** Allow Cogniters to manage project metadata and lifecycle.

- [x] **Edit Project Modal:**
    - Create a modal accessible from the project page (or dashboard) to edit project details.
    - Fields: Name, Reporting Cycle, Jira URL, Precursive URL.
- [x] **Health Status Override:**
    - Add a dropdown in the Edit Modal (or a dedicated quick-action on the dashboard) to override the calculated health status.
    - Options: Green, Yellow, Red (manual selection supersedes automated status).
- [x] **Publish/Unpublish Actions:**
    - Add buttons/toggles to the Project Page header or Project Card menu.
    - "Publish" makes the project visible to assigned Client users.

## 2. Sprint Goals
**Priority:** Medium
**Goal:** Display the current sprint's focus.

- [x] **Backend Support:**
    - Add `sprint_goals` field (Text/Markdown) to the `Project` model.
    - Update `ProjectUpdate` schema.
    - Add `jira_board_id` field for sprint API access.
    - Integrate sprint goal sync into Jira sync flow.
- [x] **Frontend Component:**
    - Create a `SprintGoalsCard` component.
    - Display this component on the Project Details page (after Timeline, before Action Register).
    - Allow manual editing of sprint goals in the "Edit Project" modal (Sprint tab).

## 3. Client Logo Upload
**Priority:** Low/Medium
**Goal:** Allow branding for client projects.

- [x] **Backend Storage:**
    - Using local filesystem with Docker volume (`uploads_data`) for persistence.
    - Created `POST /uploads/logo` endpoint for file uploads.
    - Static files served via FastAPI's `StaticFiles` mount at `/uploads`.
- [x] **Frontend Upload:**
    - Created `ImageUpload` component with dual mode: file upload or URL input.
    - Added logo upload to `CreateProjectModal`.
    - Added "Branding" tab to `EditProjectModal` for logo editing.
    - Updated `ProjectCard` and project details page to display logos with fallback.

## 4. User Assignments
**Priority:** High (Blocking for Client Access)
**Goal:** Control which clients see which projects.

- [x] **Backend Enhancements:**
    - Added `GET /users` endpoint with search and role filtering.
    - Added `GET /projects/{id}/users` endpoint to list assigned users.
    - Existing `POST/DELETE /projects/{id}/users/{user_id}` for assign/remove.
    - Added `POST /projects/{id}/invite` endpoint for invite-by-email.
- [x] **User Assignment UI:**
    - Created `TeamSection` component on Project Details page.
    - Lists assigned users with avatars, names, emails, and role badges.
    - "Add Member" button opens `AssignUserModal` for searching and assigning users.
    - Remove button (X) on each user to unassign.
    - Only visible to Cogniters.
- [x] **Invite by Email (Placeholder Users):**
    - Added `is_pending` field to User model for placeholder users.
    - Typing a valid email in AssignUserModal shows "Invite new user" option.
    - Creates placeholder user with `is_pending=True` if email doesn't exist.
    - Pending users show amber "Pending" badge in Team section.
    - When user registers with that email, they're automatically activated and retain project access.

## 5. Risk Matrix Visualization
**Priority:** Low (Enhancement)
**Goal:** Visual representation of risks.

- [ ] **Heatmap Component:**
    - Create a `RiskMatrix` component.
    - Grid layout: Probability (Y-axis) vs Impact (X-axis).
    - Map existing risks onto this 3x3 grid (Low/Medium/High).
    - Replace or augment the existing `RiskList` with this view.

## 6. External Permission Validation
**Priority:** Medium (Security/UX)
**Goal:** Verify permissions before creating projects.

- [ ] **Validation Logic:**
    - In `ProjectService.create_project`:
        - Call `JiraClient.get_permissions()` to verify the user is Owner/Admin.
        - Call `PrecursiveClient` to verify the user is PM/Owner.
    - Return specific error messages if permissions are missing, preventing project creation.

