export enum ProjectType {
  FIXED_PRICE = "Fixed Price",
  TM = "T&M",
  SAAS_REVENUE = "SaaS Revenue"
}

export enum ReportingCycle {
  WEEKLY = "Weekly",
  BI_WEEKLY = "Bi-weekly"
}

export enum HealthStatus {
  GREEN = "Green",
  YELLOW = "Yellow",
  RED = "Red"
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
