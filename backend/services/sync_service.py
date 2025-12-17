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
                "title": "Stakeholder Availability Risk",
                "description": "Key stakeholder unavailability during UAT phase",
                "mitigation": "Schedule backup stakeholders and extend UAT window by 1 week.",
                "category": "Resource"
            },
            {
                "title": "API Rate Limit Risk",
                "description": "Integration API rate limits might bottleneck data sync",
                "mitigation": "Implement exponential backoff and caching layer.",
                "category": "Technical"
            },
            {
                "title": "Scope Creep Risk",
                "description": "Scope creep in reporting requirements",
                "mitigation": "Strict change request process and weekly scope reviews.",
                "category": "Scope"
            },
            {
                "title": "Vendor Delay Risk",
                "description": "Third-party vendor delay in delivering credentials",
                "mitigation": "Escalate to vendor management and prepare mock data for dev.",
                "category": "Vendor"
            },
            {
                "title": "Data Quality Risk",
                "description": "Data quality issues in legacy system export",
                "mitigation": "Run preliminary data profiling scripts and allocate cleanup sprint.",
                "category": "Data"
            },
            {
                "title": "Knowledge Gap Risk",
                "description": "Team knowledge gap on new tech stack",
                "mitigation": "Conduct workshops and pair programming sessions.",
                "category": "People"
            },
            {
                "title": "Budget Overrun Risk",
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
                title=tmpl["title"],
                description=tmpl["description"],
                mitigation_plan=tmpl["mitigation"],
                category=tmpl["category"],
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
        # Attempt sync if key is present OR if URL is present (to try extraction)
        if project.jira_project_key or project.jira_url:
            try:
                result.jira = await self.sync_jira_data(project)
            except Exception as e:
                logger.error("Jira sync failed", error=str(e), exc_info=True)
                result.jira.success = False
                result.jira.error = str(e)
                # Ensure session is in a good state
                try:
                    self.session.rollback()
                except Exception:
                    pass  # Ignore rollback errors
        else:
            result.jira.message = "Jira not configured"
            
        # 2. Precursive Sync
        # Always attempt precursive sync logic, which now includes fake data fallback
        try:
            # Re-fetch project to ensure we have latest state
            project = self.session.get(Project, project_id)
            if not project:
                raise ResourceNotFoundError(f"Project {project_id} not found")
            result.precursive = await self.sync_precursive_data(project)
        except Exception as e:
            logger.error("Precursive sync failed", error=str(e), exc_info=True)
            result.precursive.success = False
            result.precursive.error = str(e)
            # Ensure session is in a good state
            try:
                self.session.rollback()
            except Exception:
                pass  # Ignore rollback errors
            
        # 3. Update Project Last Synced
        # Re-fetch project to ensure we have latest state
        try:
            project = self.session.get(Project, project_id)
            if project:
                project.last_synced_at = datetime.now()
                self.session.add(project)
                self.session.commit()
        except Exception as e:
            logger.error("Failed to update last_synced_at", error=str(e))
            try:
                self.session.rollback()
            except Exception:
                pass
        
        return result
    
    async def sync_jira_data(self, project: Project) -> JiraSyncResult:
        """Sync data from Jira."""
        res = JiraSyncResult(success=True)
        
        # Try to extract project key from URL if missing
        if not project.jira_project_key and project.jira_url:
            # Common patterns: /projects/KEY, /browse/KEY, projects/KEY
            # Key is usually uppercase alphanumeric
            match = re.search(r"/projects/([A-Z][A-Z0-9]+)", project.jira_url)
            if not match:
                match = re.search(r"/browse/([A-Z][A-Z0-9]+)", project.jira_url)
            
            if match:
                project.jira_project_key = match.group(1)
                self.session.add(project)
                self.session.commit()
                logger.info("Extracted Jira project key", key=project.jira_project_key)

        if not project.jira_project_key:
            res.success = False
            res.message = "No Jira project key configured"
            return res

        try:
            # Fetch Actions (Issues)
            issues = await self.jira.get_project_issues(project.jira_project_key)
            res.actions_count = len(issues)
            
            # Update DB
            for issue in issues:
                try:
                    # Check existence
                    existing = self.session.exec(
                        select(ActionItem).where(
                            ActionItem.project_id == project.id,
                            ActionItem.jira_id == issue.key
                        )
                    ).first()
                    
                    if existing:
                        existing.title = issue.summary or existing.title
                        existing.status = self._map_jira_status(issue.status)
                        existing.assignee = issue.assignee
                        existing.priority = self._map_jira_priority(issue.priority)
                        if issue.due_date:
                            try:
                                existing.due_date = datetime.strptime(issue.due_date, "%Y-%m-%d").date()
                            except ValueError:
                                logger.warning("Invalid due_date format", due_date=issue.due_date, issue_key=issue.key)
                        self.session.add(existing)
                    else:
                        new_action = ActionItem(
                            project_id=project.id,
                            jira_id=issue.key,
                            title=issue.summary or "Untitled",
                            status=self._map_jira_status(issue.status),
                            assignee=issue.assignee,
                            priority=self._map_jira_priority(issue.priority),
                            due_date=datetime.strptime(issue.due_date, "%Y-%m-%d").date() if issue.due_date else None
                        )
                        self.session.add(new_action)
                except Exception as e:
                    logger.error("Error processing Jira issue", issue_key=issue.key, error=str(e))
                    # Continue with next issue instead of failing entire sync
                    continue
            
            # Fetch Sprint Goals
            if project.jira_board_id:
                try:
                    sprint_goal = await self.jira.get_active_sprint_goal(project.jira_board_id)
                    if sprint_goal:
                        project.sprint_goals = sprint_goal
                        self.session.add(project)
                except Exception as e:
                    logger.warning("Failed to fetch sprint goal", error=str(e))
            
            # Commit all changes
            self.session.commit()
            res.message = f"Synced {res.actions_count} actions"
            if project.jira_board_id and project.sprint_goals:
                res.message += " and sprint goals"
            
        except Exception as e:
            logger.error("Error syncing Jira", error=str(e), exc_info=True)
            res.success = False
            res.error = str(e)
            # Rollback on error
            try:
                self.session.rollback()
            except Exception:
                pass
            
        return res

    async def sync_precursive_data(self, project: Project) -> PrecursiveSyncResult:
        """Sync data from Precursive."""
        res = PrecursiveSyncResult(success=True)
        errors = []
        
        # Step 1: Try to get or set precursive_id from URL
        precursive_project = None
        if not project.precursive_id and project.precursive_url:
            try:
                precursive_project = await self.precursive.get_project_by_url(project.precursive_url)
                if precursive_project:
                    project.precursive_id = precursive_project.id
                    # Also update project name and client name if available
                    if precursive_project.name and not project.name:
                        project.name = precursive_project.name
                    if precursive_project.client_name:
                        project.client_name = precursive_project.client_name
                    # Sync dates for timeline
                    if precursive_project.start_date:
                        try:
                            project.start_date = datetime.strptime(precursive_project.start_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning("Invalid start_date format", start_date=precursive_project.start_date)
                    if precursive_project.end_date:
                        try:
                            project.end_date = datetime.strptime(precursive_project.end_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning("Invalid end_date format", end_date=precursive_project.end_date)
                    self.session.add(project)
                    logger.info("Extracted Precursive project ID from URL", precursive_id=precursive_project.id)
            except Exception as e:
                logger.warning("Failed to get Precursive project from URL", error=str(e))
        
        # Also try to get project details if we have precursive_id but no dates
        if project.precursive_id and (not project.start_date or not project.end_date):
            try:
                if not precursive_project:
                    # Try to get project by ID - we'll need to fetch from mock data
                    # For now, we'll use the fallback in get_project_by_url which returns first project
                    precursive_project = await self.precursive.get_project_by_url("")
                if precursive_project:
                    if not project.start_date and precursive_project.start_date:
                        try:
                            project.start_date = datetime.strptime(precursive_project.start_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning("Invalid start_date format", start_date=precursive_project.start_date)
                    if not project.end_date and precursive_project.end_date:
                        try:
                            project.end_date = datetime.strptime(precursive_project.end_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning("Invalid end_date format", end_date=precursive_project.end_date)
                    self.session.add(project)
            except Exception as e:
                logger.warning("Failed to fetch Precursive project details", error=str(e))
        
        # Step 2: Sync Financials
        try:
            financials = None
            if project.precursive_id:
                try:
                    financials = await self.precursive.get_project_financials(project.precursive_id)
                except Exception as e:
                    logger.warning("Failed to fetch Precursive financials", error=str(e))
            
            if financials and financials.total_budget:
                project.total_budget = financials.total_budget
                project.spent_budget = financials.spent_budget
                project.remaining_budget = financials.remaining_budget
                project.currency = financials.currency
                self.session.add(project)
                res.financials_updated = True
                res.message = "Synced financials from Precursive"
            else:
                # Generate fake financials if none exist
                if not project.total_budget:
                    logger.info("No Precursive financials found. Generating fake financials.")
                    project.total_budget = random.uniform(200000, 500000)
                    project.spent_budget = project.total_budget * random.uniform(0.2, 0.6)
                    project.remaining_budget = project.total_budget - project.spent_budget
                    project.currency = "USD"
                    self.session.add(project)
                    res.financials_updated = True
                    res.message = "Generated synthetic financials"
                
        except Exception as e:
            errors.append(f"Financials sync failed: {str(e)}")

        # Step 2.5: Generate fake dates if none exist (for timeline)
        if not project.start_date or not project.end_date:
            logger.info("No Precursive dates found. Generating fake dates for timeline.")
            today = date.today()
            if not project.start_date:
                # Start date: 3-6 months ago
                months_ago = random.randint(3, 6)
                project.start_date = today - timedelta(days=months_ago * 30)
            if not project.end_date:
                # End date: 3-9 months from now
                months_ahead = random.randint(3, 9)
                project.end_date = today + timedelta(days=months_ahead * 30)
            self.session.add(project)
            logger.info("Generated synthetic dates", start_date=project.start_date, end_date=project.end_date)

        # Step 3: Sync Risks
        try:
            risks_data = []
            if project.precursive_id:
                try:
                    risks_data = await self.precursive.get_project_risks(project.precursive_id)
                except Exception as e:
                    logger.warning("Failed to fetch Precursive risks", error=str(e))
            
            if risks_data:
                # Real data logic - use mock Precursive data
                for risk_data in risks_data:
                    # Use summary for title, description for description
                    existing_risk = self.session.exec(
                        select(Risk).where(
                            Risk.project_id == project.id,
                            Risk.title == risk_data.summary
                        )
                    ).first()
                    
                    if existing_risk:
                        existing_risk.description = risk_data.description
                        existing_risk.probability = self._map_risk_probability(risk_data.probability)
                        existing_risk.impact = self._map_risk_impact(risk_data.impact)
                        existing_risk.status = self._map_risk_status(risk_data.status)
                        existing_risk.mitigation_plan = risk_data.mitigation_plan
                        existing_risk.category = risk_data.category
                        existing_risk.impact_rationale = risk_data.impact_rationale
                        if risk_data.date_identified:
                            try:
                                existing_risk.date_identified = datetime.strptime(risk_data.date_identified, "%Y-%m-%d")
                            except ValueError:
                                existing_risk.date_identified = datetime.now()
                        self.session.add(existing_risk)
                    else:
                        new_risk = Risk(
                            project_id=project.id,
                            title=risk_data.summary,
                            description=risk_data.description,
                            probability=self._map_risk_probability(risk_data.probability),
                            impact=self._map_risk_impact(risk_data.impact),
                            status=self._map_risk_status(risk_data.status),
                            mitigation_plan=risk_data.mitigation_plan,
                            category=risk_data.category,
                            impact_rationale=risk_data.impact_rationale,
                            date_identified=datetime.strptime(risk_data.date_identified, "%Y-%m-%d") if risk_data.date_identified else datetime.now()
                        )
                        self.session.add(new_risk)
                
                res.risks_count = len(risks_data)
                if not res.message:
                    res.message = "Synced risks from Precursive"
            else:
                # NO DATA or NO ID -> FAKE IT
                # Check if we already have risks
                existing_risks = self.session.exec(
                    select(Risk).where(Risk.project_id == project.id)
                ).all()
                
                if not existing_risks:
                    logger.info("No existing risks and no external data. Generating fake risks.")
                    fake_risks = self._generate_fake_risks(project.id)
                    for r in fake_risks:
                        self.session.add(r)
                    res.risks_count = len(fake_risks)
                    if not res.message:
                        res.message = "Generated synthetic risks"
                else:
                    res.risks_count = len(existing_risks)
                    if not res.message:
                        res.message = f"Found {len(existing_risks)} existing risks"
                    
            self.session.commit()
                        
        except Exception as e:
            errors.append(f"Risk sync failed: {str(e)}")
            logger.error("Risk sync error", error=str(e), exc_info=True)
            
        if errors:
            res.success = False
            res.error = "; ".join(errors)
            
        return res

    # ... helpers ...
    def _map_jira_status(self, status: Optional[str]) -> ActionStatus:
        """Map Jira status to ActionStatus, defaulting to TO_DO if None or unknown."""
        if not status:
            return ActionStatus.TO_DO
        s = status.lower()
        if s in ['done', 'complete', 'closed', 'resolved']:
            return ActionStatus.COMPLETE
        elif s in ['in progress', 'in review', 'qa']:
            return ActionStatus.IN_PROGRESS
        return ActionStatus.TO_DO
    
    def _map_jira_priority(self, priority: Optional[str]) -> Priority:
        """Map Jira priority to Priority, defaulting to MEDIUM if None or unknown."""
        if not priority:
            return Priority.MEDIUM
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

