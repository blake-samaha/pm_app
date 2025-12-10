# Technical Requirements Document: Automated Project Management Tool

## 1. Overview
The Automated Project Management Tool is a web application designed to streamline project tracking and reporting for Cognite projects. It serves two primary user roles: **Cogniters** (internal employees) and **Clients** (external stakeholders). The app integrates with Precursive (Salesforce) and Jira to provide a unified view of project health, timelines, financials, actions, and risks.

## 2. Architecture & Tech Stack (POC / MVP)
*   **Infrastructure**: Dockerized environment (Local execution).
*   **Frontend**: React (Next.js) with Shadcn UI.
*   **Backend**: Python (FastAPI) using **Astral's uv** for package management.
*   **Database**: PostgreSQL (Docker container).
*   **Authentication**: Google SSO (OAuth2) + Email/Password.
*   **Data Strategy**: Periodic sync from external sources (Precursive, Jira) to local PostgreSQL database. Read-only for Jira initially.
*   **Integrations**:
    *   Salesforce API (Precursive data) - Read-only.
    *   Jira API - Read-only.

## 3. Authentication & Authorization
### 3.1. Sign In
*   **UI**: Clean login page.
    *   "Login with Google" button (Primary for SSO).
    *   Email & Password form.
*   **Role Logic**:
    *   **Cogniter**: Email domain `@cognite.com`. Access to all internal features, project creation, and editing.
    *   **Client**: Non-Cognite email domains. Access limited to assigned project dashboards and specific interactive elements (Action Register comments).

### 3.2. User Data Model
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  role: 'Cogniter' | 'Client';
  authProvider: 'Google' | 'Email';
  assignedProjects: string[]; // Project IDs
}
```

## 4. Core Features & UI Requirements

### 4.1. Landing Page
*   **Cogniter View**:
    *   List of assigned projects (from Precursive or manually created).
    *   Controls: Edit, Create New, Publish, Unpublish projects.
    *   User Group Management: Manage access for specific projects.
*   **Client View**:
    *   List of dashboards/projects associated with their user group.
    *   Task summary (Action Register items assigned to them).

### 4.2. Project Creation / Definition
*   **Trigger**: Automatic creation when Precursive Project moves to "Delivery" phase.
*   **Manual Creation Form**:
    *   **Project Name** (Text, Required): Defaults from Precursive.
    *   **Precursive URL** (URL, Required): Unique identifier/trigger. Enforce one-report-per-URL.
    *   **Jira URL** (URL, Required): Link to main Jira board.
    *   **Client Logo** (File Upload, Required).
    *   **Project Type** (Dropdown, Required): "T&M Billable" or "Fixed Price". (Defaults from Precursive).
    *   **Reporting Cycle** (Dropdown): "Weekly" or "Bi-weekly".
*   **Backend Logic**: Job to populate fields from Precursive URL if manually entered.

### 4.3. Project Health Dashboard
A comprehensive view of the project status.

#### A. Overall Health
*   **Visual**: Status indicator (Green/Yellow/Red).
*   **Logic**: Derived from Precursive "Delivery Phase" status.
    *   On Track = Green
    *   Minor Deviation = Yellow
    *   Requires Attention = Red
*   **Overrides**: Manual override capability. Option for separate Internal vs External status.

#### B. Timeline
*   **Visual**: Gantt chart or Timeline view.
*   **Source**: Jira (Epics, Stories, Tasks, Subtasks).
*   **Features**:
    *   Dynamic adjustments based on parent date changes.
    *   Parent-Child relationships (Epic > Story > Task > Subtask).
    *   Progress bars (percent complete) within timeline bars.
    *   **External View**: Hides subtasks.

#### C. Progress / Sprint Goals
*   **Source**: Jira Sprints.
*   **Content**: Sprint Goals text.
*   **Editability**: Ability to manually add/edit goals.

#### D. Financials
*   **Visibility**: Dependent on Project Type.
    *   **Fixed Price**: Critical for Internal view (Budget vs Actual).
    *   **T&M**: Critical for both Internal & External views.
*   **Data Points**:
    *   Remaining Budget (pulled from Precursive/Salesforce).
    *   Update Frequency: Daily or Live.

#### E. Action Register
*   **Visual**: Table/List view.
*   **Source**: Jira tasks with specific labels OR manual entry.
*   **Columns**: Action ID, Jira ID, Title, Status, Assignee, Due Date, Priority, Comments.
*   **Interactivity**:
    *   Status changes (To Do, In Progress, Complete).
    *   Commenting system (Threaded comments with user & timestamp).
    *   Past due highlighting (Red).
    *   Toggle visibility of columns (Action ID, Jira ID).

#### F. Risk Matrix
*   **Visual**: Heatmap (Probability vs Impact) + List view.
*   **Source**: Precursive (initial import) + App-specific additions.
*   **Fields**: Risk Description, Probability, Impact, Status, Mitigation Plan.
*   **Visibility**: Public to all project viewers.

## 5. Data Models (Draft)

### Project
```typescript
interface Project {
  id: string;
  name: string;
  precursiveUrl: string;
  jiraUrl: string;
  clientLogoUrl: string;
  type: 'Fixed Price' | 'T&M' | 'SaaS Revenue';
  reportingCycle: 'Weekly' | 'Bi-weekly';
  healthStatus: 'Green' | 'Yellow' | 'Red';
  healthStatusOverride?: 'Green' | 'Yellow' | 'Red';
  isPublished: boolean;
}
```

### ActionItem
```typescript
interface ActionItem {
  id: string;
  projectId: string;
  jiraId?: string;
  title: string;
  status: 'To Do' | 'In Progress' | 'Complete';
  assignee: string; // User ID or Name
  dueDate: Date;
  priority: 'High' | 'Medium' | 'Low';
  comments: Comment[];
}
```

### Risk
```typescript
interface Risk {
  id: string;
  projectId: string;
  description: string;
  probability: 'Low' | 'Medium' | 'High';
  impact: 'Low' | 'Medium' | 'High';
  status: 'Open' | 'Closed';
  mitigationPlan: string;
}
```

## 6. Integration Requirements
*   **Precursive**: Read-only access to Project details, Status, Financials. Webhook/Trigger for "Delivery" phase transition.
*   **Jira**: Read/Write access. Read for Timeline/Sprints. Read/Write for Action Register sync (optional bidirectional sync).

## 7. Backend Architecture

> **Note:** Detailed backend architecture, design patterns, and implementation details have been moved to [Backend Architecture](Backend_Architecture.md).


