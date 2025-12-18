export enum ProjectType {
    FIXED_PRICE = "Fixed Price",
    TIME_AND_MATERIALS = "Time & Materials",
    RETAINER = "Retainer",
}

export enum ReportingCycle {
    WEEKLY = "Weekly",
    BIWEEKLY = "Bi-Weekly",
    MONTHLY = "Monthly",
}

export enum HealthStatus {
    GREEN = "Green",
    YELLOW = "Yellow",
    RED = "Red",
}

export enum UserRole {
    COGNITER = "Cogniter",
    CLIENT_FINANCIALS = "Client + Financials",
    CLIENT = "Client",
}

export interface User {
    id: string;
    email: string;
    name: string;
    role: UserRole;
    is_pending?: boolean;
}

export interface InviteUserResponse {
    user: User;
    was_created: boolean;
    message: string;
}

export interface Project {
    id: string;
    name: string;
    precursive_url: string;
    jira_url: string;
    client_logo_url?: string;
    type: ProjectType;
    reporting_cycle?: ReportingCycle;
    health_status: HealthStatus;
    health_status_override?: HealthStatus;
    is_published: boolean;

    // Sync Data
    last_synced_at?: string;
    jira_board_id?: number;

    // Sprint data (from Jira)
    sprint_goals?: string;

    // Financials
    total_budget?: number;
    spent_budget?: number;
    remaining_budget?: number;
    currency?: string;

    // Timeline
    start_date?: string;
    end_date?: string;
    client_name?: string;
}
