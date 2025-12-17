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

- [ ] **Backend Support:**
    - Add `sprint_goals` field (Text/Markdown) to the `Project` model.
    - Update `ProjectUpdate` schema.
- [ ] **Frontend Component:**
    - Create a `SprintGoals` card component.
    - Display this component on the Project Details page (likely near the Action Register).
    - Allow manual editing of this text area in the "Edit Project" flow (since this data might not easily map from Jira/Precursive automatically).

## 3. Client Logo Upload
**Priority:** Low/Medium
**Goal:** Allow branding for client projects.

- [ ] **Backend Storage:**
    - Determine storage strategy (e.g., local static files, S3, or Firebase Storage).
    - Update `ProjectCreate` endpoint to accept file uploads (currently accepts a URL string).
- [ ] **Frontend Upload:**
    - Replace the "Client Logo URL" text input in `CreateProjectModal` with a File Input.
    - Handle the file upload logic before submitting the project creation form.

## 4. User Assignments
**Priority:** High (Blocking for Client Access)
**Goal:** Control which clients see which projects.

- [ ] **User Assignment UI:**
    - Create a "Team" or "Access" tab in the Project Details page.
    - List currently assigned users.
    - Add an "Assign User" interface (search by email/name) to link Clients to the project.
    - Ensure only Cogniters can manage these assignments.

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

