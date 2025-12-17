"""Sync service for orchestrating data synchronization from external APIs."""
import re
import structlog
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID
import random

from sqlmodel import Session, select

from config import Settings
from models import Project, ActionItem, ActionStatus, Priority, HealthStatus, Risk, RiskProbability, RiskImpact, RiskStatus
from integrations import JiraClient, PrecursiveClient
from integrations.jira_client import JiraIssue
from integrations.precursive_client import PrecursiveProject, PrecursiveFinancials
from exceptions import IntegrationError, ResourceNotFoundError
from schemas.sync import SyncResult, JiraSyncResult, PrecursiveSyncResult, SyncStatus

logger = structlog.get_logger()


class SyncService:
    """Service for syncing project data from Jira and Precursive."""
    
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.jira = JiraClient(settings)
        self.precursive = PrecursiveClient(settings)
    
    async def close(self):
        """Close API client connections."""
        await self.jira.close()
        await self.precursive.close()
    
    # =========================================================================
    # Status
    # =========================================================================

    def get_sync_status(self, project_id: UUID) -> SyncStatus:
        """Get the current sync status for a project."""
        project = self.session.get(Project, project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")
            
        return SyncStatus(
            project_id=project.id,
            last_synced_at=project.last_synced_at,
            jira_configured=bool(project.jira_project_key or project.jira_url),
            precursive_configured=bool(project.precursive_id or project.precursive_url),
            jira_project_key=project.jira_project_key,
            jira_project_name=project.jira_project_name
        )

    # =========================================================================
    # Fake Data Generation
    # =========================================================================
    
    def _generate_fake_risks(self, project_id: UUID) -> List[Risk]:
        """Generate realistic fake risks for a project."""
        risk_templates = [
            {
                "description": "Key stakeholder unavailability during UAT phase",
                "mitigation": "Schedule backup stakeholders and extend UAT window by 1 week.",
                "category": "Resource"
            },
            {
                "description": "Integration API rate limits might bottleneck data sync",
                "mitigation": "Implement exponential backoff and caching layer.",
                "category": "Technical"
            },
            {
                "description": "Scope creep in reporting requirements",
                "mitigation": "Strict change request process and weekly scope reviews.",
                "category": "Scope"
            },
            {
                "description": "Third-party vendor delay in delivering credentials",
                "mitigation": "Escalate to vendor management and prepare mock data for dev.",
                "category": "Vendor"
            },
            {
                "description": "Data quality issues in legacy system export",
                "mitigation": "Run preliminary data profiling scripts and allocate cleanup sprint.",
                "category": "Data"
            },
            {
                "description": "Team knowledge gap on new tech stack",
                "mitigation": "Conduct workshops and pair programming sessions.",
                "category": "People"
            },
            {
                "description": "Budget overrun due to extended discovery phase",
                "mitigation": "Re-estimate remaining phases and seek budget approval.",
                "category": "Financial"
            }
        ]
        
        risks = []
        # Generate 5-8 random risks
        num_risks = random.randint(5, 8)
        selected = random.sample(risk_templates, num_risks)
        
        for tmpl in selected:
            risk = Risk(
                project_id=project_id,
                description=tmpl["description"],
                mitigation_plan=tmpl["mitigation"],
                probability=random.choice(list(RiskProbability)),
                impact=random.choice(list(RiskImpact)),
                status=RiskStatus.OPEN,
                date_identified=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            risks.append(risk)
            
        return risks

    # =========================================================================
    # Sync Logic
    # =========================================================================
    
    async def sync_project(self, project_id: UUID) -> SyncResult:
        """
        Full sync for a project.
        1. Fetch Project details
        2. Sync Jira (Actions, Sprint Goals)
        3. Sync Precursive (Financials, Risks)
        4. Update Sync Status
        """
        logger.info("Starting project sync", project_id=str(project_id))
        
        project = self.session.get(Project, project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")
            
        result = SyncResult(
            project_id=project_id,
            timestamp=datetime.now(),
            jira=JiraSyncResult(success=False),
            precursive=PrecursiveSyncResult(success=False)
        )
        
        # 1. Jira Sync
        if project.jira_project_key or project.jira_url:
            try:
                result.jira = await self.sync_jira_data(project)
            except Exception as e:
                logger.error("Jira sync failed", error=str(e))
                result.jira.error = str(e)
        else:
            result.jira.message = "Jira not configured"
            
        # 2. Precursive Sync
        # Always attempt precursive sync logic, which now includes fake data fallback
        try:
            result.precursive = await self.sync_precursive_data(project)
        except Exception as e:
            logger.error("Precursive sync failed", error=str(e))
            result.precursive.error = str(e)
            
        # 3. Update Project Last Synced
        project.last_synced_at = datetime.now()
        self.session.add(project)
        self.session.commit()
        
        return result

    async def sync_jira_data(self, project: Project) -> JiraSyncResult:
        """Sync data from Jira."""
        res = JiraSyncResult(success=True)
        
        if not project.jira_project_key:
            # Try to extract key from URL if not set
            if project.jira_url:
                # varied logic to extract key, placeholder
                pass
            else:
                res.success = False
                res.message = "No Jira configuration"
                return res

        try:
            # Fetch Actions (Issues)
            issues = await self.jira.get_project_issues(project.jira_project_key)
            res.actions_count = len(issues)
            
            # Update DB
            for issue in issues:
                # Check existence
                existing = self.session.exec(
                    select(ActionItem).where(
                        ActionItem.project_id == project.id,
                        ActionItem.jira_id == issue.key
                    )
                ).first()
                
                if existing:
                    existing.title = issue.summary
                    existing.status = self._map_jira_status(issue.status)
                    existing.assignee = issue.assignee
                    existing.priority = self._map_jira_priority(issue.priority)
                    if issue.due_date:
                        existing.due_date = datetime.strptime(issue.due_date, "%Y-%m-%d").date()
                    self.session.add(existing)
                else:
                    new_action = ActionItem(
                        project_id=project.id,
                        jira_id=issue.key,
                        title=issue.summary,
                        status=self._map_jira_status(issue.status),
                        assignee=issue.assignee,
                        priority=self._map_jira_priority(issue.priority),
                        due_date=datetime.strptime(issue.due_date, "%Y-%m-%d").date() if issue.due_date else None
                    )
                    self.session.add(new_action)
            
            # Fetch Sprint Goals
            if project.jira_board_id:
                sprint_goal = await self.jira.get_active_sprint_goal(project.jira_board_id)
                if sprint_goal:
                    project.sprint_goals = sprint_goal
                    self.session.add(project)
                    res.message = "Synced actions and sprint goals"
            
            self.session.commit()
            
        except Exception as e:
            logger.error("Error syncing Jira", error=str(e))
            res.success = False
            res.error = str(e)
            
        return res

    async def sync_precursive_data(self, project: Project) -> PrecursiveSyncResult:
        """Sync data from Precursive."""
        res = PrecursiveSyncResult(success=True)
        errors = []
        
        # Sync Financials
        try:
            if project.precursive_id:
                financials = await self.precursive.get_project_financials(project.precursive_id)
                if financials:
                    project.total_budget = financials.total_budget
                    project.spent_budget = financials.spent_budget
                    project.remaining_budget = financials.remaining_budget
                    project.currency = financials.currency
                    self.session.add(project)
                    res.financials_updated = True
            else:
                # If no precursive ID, we might want to fake financials too?
                # For now focusing on risks as requested
                pass
                
        except Exception as e:
            errors.append(f"Financials sync failed: {str(e)}")

        # Sync Risks
        # Logic: If we get risks from API, use them. If not (or no ID), generate fake ones if none exist.
        try:
            risks_data = []
            if project.precursive_id:
                try:
                    risks_data = await self.precursive.get_project_risks(project.precursive_id)
                except Exception as e:
                    logger.warning("Failed to fetch Precursive risks", error=str(e))
            
            if risks_data:
                # Real data logic
                current_risk_ids = []
                for risk_data in risks_data:
                    existing_risk = self.session.exec(
                        select(Risk).where(
                            Risk.project_id == project.id,
                            Risk.description == risk_data.description # fallback to desc match
                        )
                    ).first()
                    
                    if existing_risk:
                        existing_risk.probability = self._map_risk_probability(risk_data.probability)
                        existing_risk.impact = self._map_risk_impact(risk_data.impact)
                        existing_risk.status = self._map_risk_status(risk_data.status)
                        existing_risk.mitigation_plan = risk_data.mitigation_plan
                        self.session.add(existing_risk)
                        current_risk_ids.append(existing_risk.id)
                    else:
                        new_risk = Risk(
                            project_id=project.id,
                            description=risk_data.description,
                            probability=self._map_risk_probability(risk_data.probability),
                            impact=self._map_risk_impact(risk_data.impact),
                            status=self._map_risk_status(risk_data.status),
                            mitigation_plan=risk_data.mitigation_plan,
                            date_identified=datetime.now()
                        )
                        self.session.add(new_risk)
                        self.session.commit() # Commit to get ID
                        current_risk_ids.append(new_risk.id)
                
                res.risks_count = len(risks_data)
            else:
                # NO DATA or NO ID -> FAKE IT
                # Check if we already have risks
                existing_count = self.session.exec(
                    select(Risk).where(Risk.project_id == project.id)
                ).all()
                
                if not existing_count:
                    logger.info("No existing risks and no external data. Generating fake risks.")
                    fake_risks = self._generate_fake_risks(project.id)
                    for r in fake_risks:
                        self.session.add(r)
                    res.risks_count = len(fake_risks)
                    res.message = "Generated synthetic risks"
                else:
                    res.risks_count = len(existing_count)
                    
            self.session.commit()

        except Exception as e:
            errors.append(f"Risk sync failed: {str(e)}")
            
        if errors:
            res.success = False
            res.error = "; ".join(errors)
            
        return res

    # ... helpers ...
    def _map_jira_status(self, status: str) -> ActionStatus:
        s = status.lower()
        if s in ['done', 'complete', 'closed', 'resolved']:
            return ActionStatus.COMPLETE
        elif s in ['in progress', 'in review', 'qa']:
            return ActionStatus.IN_PROGRESS
        return ActionStatus.TO_DO

    def _map_jira_priority(self, priority: str) -> Priority:
        p = priority.lower()
        if p in ['high', 'critical', 'blocker']:
            return Priority.HIGH
        elif p in ['low', 'trivial']:
            return Priority.LOW
        return Priority.MEDIUM

    def _map_risk_probability(self, prob: str) -> RiskProbability:
        p = prob.lower()
        if 'high' in p: return RiskProbability.HIGH
        if 'low' in p: return RiskProbability.LOW
        return RiskProbability.MEDIUM

    def _map_risk_impact(self, impact: str) -> RiskImpact:
        i = impact.lower()
        if 'high' in i: return RiskImpact.HIGH
        if 'low' in i: return RiskImpact.LOW
        return RiskImpact.MEDIUM

    def _map_risk_status(self, status: str) -> RiskStatus:
        return RiskStatus.OPEN # simplified
