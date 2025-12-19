export enum ActionStatus {
    TO_DO = "To Do",
    IN_PROGRESS = "In Progress",
    COMPLETE = "Complete",
    NO_STATUS = "No Status",
}

export enum Priority {
    HIGH = "High",
    MEDIUM = "Medium",
    LOW = "Low",
}

export interface ActionItem {
    id: string;
    project_id: string;
    jira_id?: string;
    jira_key?: string;
    title: string;
    status: ActionStatus;
    assignee?: string;
    due_date?: string;
    priority: Priority;
    issue_type?: string;
    last_synced_at?: string;
    // Comment count for badge display
    comment_count?: number;
}

export enum RiskProbability {
    LOW = "Low",
    MEDIUM = "Medium",
    HIGH = "High",
}

export enum RiskImpact {
    LOW = "Low",
    MEDIUM = "Medium",
    HIGH = "High",
}

export enum RiskStatus {
    OPEN = "Open",
    CLOSED = "Closed",
    MITIGATED = "Mitigated",
}

export interface Risk {
    id: string;
    project_id: string;
    title?: string;
    description: string;
    category?: string;
    impact_rationale?: string;
    date_identified?: string;
    probability: RiskProbability;
    impact: RiskImpact;
    status: RiskStatus;
    mitigation_plan?: string;
    // Resolution fields
    decision_record?: string;
    resolved_at?: string;
    resolved_by_id?: string;
    // Reopen fields
    reopen_reason?: string;
    reopened_at?: string;
    reopened_by_id?: string;
}

export interface Comment {
    id: string;
    user_id: string;
    content: string;
    created_at: string;
    action_item_id?: string;
    risk_id?: string;
    // Author identity (name first, fallback to email)
    author_name?: string;
    author_email?: string;
}

// Request types for mutations
export interface RiskResolveRequest {
    status: RiskStatus.CLOSED | RiskStatus.MITIGATED;
    decision_record: string;
}

export interface RiskReopenRequest {
    reason: string;
}

export interface CommentCreateRequest {
    content: string;
}
