export enum ActionStatus {
  TO_DO = "To Do",
  IN_PROGRESS = "In Progress",
  COMPLETE = "Complete",
  NO_STATUS = "No Status"
}

export enum Priority {
  HIGH = "High",
  MEDIUM = "Medium",
  LOW = "Low"
}

export interface ActionItem {
  id: string;
  project_id: string;
  jira_id?: string;
  title: string;
  status: ActionStatus;
  assignee?: string;
  due_date?: string;
  priority: Priority;
}

export enum RiskProbability {
  LOW = "Low",
  MEDIUM = "Medium",
  HIGH = "High"
}

export enum RiskImpact {
  LOW = "Low",
  MEDIUM = "Medium",
  HIGH = "High"
}

export enum RiskStatus {
  OPEN = "Open",
  CLOSED = "Closed"
}

export interface Risk {
  id: string;
  project_id: string;
  description: string;
  probability: RiskProbability;
  impact: RiskImpact;
  status: RiskStatus;
  mitigation_plan?: string;
}

