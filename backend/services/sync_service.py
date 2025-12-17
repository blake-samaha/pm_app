"""Sync service for orchestrating data synchronization from external APIs."""
import re
import structlog
from datetime import datetime, date
from typing import Optional
from uuid import UUID

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
    # Main Sync Methods
    # =========================================================================
    
    async def sync_project(self, project_id: UUID) -> SyncResult:
        """
        Sync all data for a project from both Jira and Precursive.
        
        Args:
            project_id: The UUID of the project to sync
            
        Returns:
            SyncResult with details of what was synced
        """
        logger.info("Starting full project sync", project_id=str(project_id))
        
        # Get project
        project = self.session.get(Project, project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")

        # Enforce Precursive is required for full syncs
        if not self.precursive.is_configured:
            raise IntegrationError(
                "Precursive integration is required for full sync. "
                "Set PRECURSIVE_INSTANCE_URL and credentials."
            )
        
        errors: list[str] = []
        jira_synced = False
        jira_items_synced = 0
        jira_items_created = 0
        jira_items_updated = 0
        precursive_synced = False
        financials_updated = False
        
        # Sync Jira
        if self.jira.is_configured:
            try:
                jira_result = await self.sync_jira_issues(project)
                jira_synced = True
                jira_items_synced = jira_result.items_synced
                jira_items_created = jira_result.items_created
                jira_items_updated = jira_result.items_updated
                errors.extend(jira_result.errors)
            except IntegrationError as e:
                logger.error("Jira sync failed", project_id=str(project_id), error=str(e))
                errors.append(f"Jira sync failed: {str(e)}")
        else:
            logger.warning("Jira not configured, skipping sync", project_id=str(project_id))
            errors.append("Jira integration not configured")
        
        # Sync Precursive
        if self.precursive.is_configured:
            try:
                precursive_result = await self.sync_precursive_data(project)
                precursive_synced = precursive_result.synced
                financials_updated = precursive_result.financials_updated
                errors.extend(precursive_result.errors)
            except IntegrationError as e:
                logger.error("Precursive sync failed", project_id=str(project_id), error=str(e))
                errors.append(f"Precursive sync failed: {str(e)}")
        else:
            logger.warning("Precursive not configured, skipping sync", project_id=str(project_id))
            errors.append("Precursive integration not configured")
        
        # Update last synced timestamp
        project.last_synced_at = datetime.utcnow()
        self.session.add(project)
        self.session.commit()
        
        result = SyncResult(
            project_id=project_id,
            jira_synced=jira_synced,
            jira_items_synced=jira_items_synced,
            jira_items_created=jira_items_created,
            jira_items_updated=jira_items_updated,
            precursive_synced=precursive_synced,
            financials_updated=financials_updated,
            errors=errors,
            synced_at=datetime.utcnow(),
        )
        
        logger.info("Project sync complete", 
                   project_id=str(project_id),
                   jira_items=jira_items_synced,
                   precursive_synced=precursive_synced)
        
        await self.close()
        return result
    
    async def sync_jira_issues(self, project: Project) -> JiraSyncResult:
        """
        Sync Jira issues to ActionItems for a project.
        
        Args:
            project: The project to sync issues for
            
        Returns:
            JiraSyncResult with sync details
        """
        logger.info("Starting Jira sync", project_id=str(project.id), jira_url=project.jira_url)
        
        errors: list[str] = []
        items_created = 0
        items_updated = 0
        
        # Extract project key from Jira URL
        try:
            project_key = self._extract_jira_project_key(project.jira_url)
            logger.info("Extracted Jira project key", key=project_key)
            
            # Fetch full project details from Jira to get the name
            try:
                jira_project_details = await self.jira.get_project(project_key)
                project_name = jira_project_details.name
                logger.info("Fetched Jira project details", name=project_name)
            except IntegrationError as e:
                logger.warning("Failed to fetch Jira project details", error=str(e))
                project_name = None

            # Update project with extracted key and fetched name
            if project.jira_project_key != project_key or project.jira_project_name != project_name:
                project.jira_project_key = project_key
                if project_name:
                    project.jira_project_name = project_name
                self.session.add(project)
                self.session.commit()
                
        except IntegrationError as e:
            return JiraSyncResult(
                project_id=project.id,
                items_synced=0,
                items_created=0,
                items_updated=0,
                errors=[str(e)],
                synced_at=datetime.utcnow(),
            )
        
        # Fetch issues from Jira
        try:
            jira_issues = await self.jira.get_project_issues(project_key, max_results=200)
            logger.info("Fetched Jira issues", count=len(jira_issues))
        except IntegrationError as e:
            return JiraSyncResult(
                project_id=project.id,
                items_synced=0,
                items_created=0,
                items_updated=0,
                errors=[str(e)],
                synced_at=datetime.utcnow(),
            )
        
        # Process each issue
        for jira_issue in jira_issues:
            try:
                # Check if ActionItem already exists for this Jira issue
                existing_action = self.session.exec(
                    select(ActionItem).where(
                        ActionItem.project_id == project.id,
                        ActionItem.jira_key == jira_issue.key
                    )
                ).first()
                
                if existing_action:
                    # Update existing
                    self._update_action_from_jira(existing_action, jira_issue)
                    items_updated += 1
                else:
                    # Create new
                    new_action = self._create_action_from_jira(jira_issue, project.id)
                    self.session.add(new_action)
                    items_created += 1
                    
            except Exception as e:
                error_msg = f"Failed to sync issue {jira_issue.key}: {str(e)}"
                logger.error("Issue sync failed", issue_key=jira_issue.key, error=str(e))
                errors.append(error_msg)
        
        self.session.commit()
        
        return JiraSyncResult(
            project_id=project.id,
            items_synced=items_created + items_updated,
            items_created=items_created,
            items_updated=items_updated,
            errors=errors,
            synced_at=datetime.utcnow(),
        )
    
    async def sync_precursive_data(self, project: Project) -> PrecursiveSyncResult:
        """
        Sync project data and financials from Precursive.
        
        Args:
            project: The project to sync data for
            
        Returns:
            PrecursiveSyncResult with sync details
        """
        logger.info("Starting Precursive sync", 
                   project_id=str(project.id), 
                   precursive_url=project.precursive_url)
        
        errors: list[str] = []
        financials_updated = False
        project_name: Optional[str] = None
        client_name: Optional[str] = None
        
        # Fetch project data from Precursive
        try:
            precursive_project = await self.precursive.get_project_by_url(project.precursive_url)
            
            if precursive_project is None:
                return PrecursiveSyncResult(
                    project_id=project.id,
                    synced=False,
                    financials_updated=False,
                    errors=["Project not found in Precursive"],
                    synced_at=datetime.utcnow(),
                )
            
            # Update project fields from Precursive
            project.precursive_id = precursive_project.id
            project.client_name = precursive_project.client_name
            project_name = precursive_project.name
            client_name = precursive_project.client_name
            
            # Map delivery phase to health status
            if precursive_project.delivery_phase:
                project.health_status = self._map_delivery_phase_to_health(
                    precursive_project.delivery_phase
                )
            
            # Parse dates if available
            if precursive_project.start_date:
                try:
                    project.start_date = self._parse_date_string(precursive_project.start_date)
                except ValueError:
                    errors.append(f"Invalid start_date format: {precursive_project.start_date}")
            
            if precursive_project.end_date:
                try:
                    project.end_date = self._parse_date_string(precursive_project.end_date)
                except ValueError:
                    errors.append(f"Invalid end_date format: {precursive_project.end_date}")
            
            logger.info("Updated project from Precursive", 
                       precursive_id=precursive_project.id,
                       client_name=precursive_project.client_name)
            
        except IntegrationError as e:
            return PrecursiveSyncResult(
                project_id=project.id,
                synced=False,
                financials_updated=False,
                errors=[str(e)],
                synced_at=datetime.utcnow(),
            )
        
        # Fetch financials
        try:
            if project.precursive_id:
                financials = await self.precursive.get_project_financials(project.precursive_id)
                
                project.total_budget = financials.total_budget
                project.spent_budget = financials.spent_budget
                project.remaining_budget = financials.remaining_budget
                project.currency = financials.currency
                financials_updated = True
                
                logger.info("Updated financials from Precursive",
                           total_budget=financials.total_budget,
                           currency=financials.currency)
                
        except IntegrationError as e:
            logger.warning("Failed to fetch financials", error=str(e))
            errors.append(f"Financials sync failed: {str(e)}")

        # Sync Risks
        try:
            if project.precursive_id:
                risks = await self.precursive.get_project_risks(project.precursive_id)
                logger.info("Fetched risks from Precursive", count=len(risks))
                
                for risk_data in risks:
                    # Check if risk exists by title
                    existing_risk = self.session.exec(
                        select(Risk).where(
                            Risk.project_id == project.id,
                            Risk.title == risk_data.summary
                        )
                    ).first()
                    
                    if existing_risk:
                        # Update existing
                        existing_risk.description = risk_data.description
                        existing_risk.probability = self._map_risk_probability(risk_data.probability)
                        existing_risk.impact = self._map_risk_impact(risk_data.impact)
                        existing_risk.status = self._map_risk_status(risk_data.status)
                        existing_risk.mitigation_plan = risk_data.mitigation_plan
                        existing_risk.category = risk_data.category
                        existing_risk.impact_rationale = risk_data.impact_rationale
                        if risk_data.date_identified:
                            try:
                                existing_risk.date_identified = self._parse_datetime_string(risk_data.date_identified)
                            except ValueError:
                                pass  # Ignore invalid dates
                        self.session.add(existing_risk)
                    else:
                        # Create new
                        date_identified = None
                        if risk_data.date_identified:
                            try:
                                date_identified = self._parse_datetime_string(risk_data.date_identified)
                            except ValueError:
                                pass

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
                            date_identified=date_identified
                        )
                        self.session.add(new_risk)
                        
        except Exception as e:
            logger.error("Failed to sync risks", error=str(e))
            errors.append(f"Risk sync failed: {str(e)}")
        
        self.session.add(project)
        self.session.commit()
        
        return PrecursiveSyncResult(
            project_id=project.id,
            synced=True,
            financials_updated=financials_updated,
            project_name=project_name,
            client_name=client_name,
            errors=errors,
            synced_at=datetime.utcnow(),
        )
    
    def get_sync_status(self, project_id: UUID) -> SyncStatus:
        """
        Get the current sync status for a project.
        
        Args:
            project_id: The UUID of the project
            
        Returns:
            SyncStatus with current configuration and last sync info
        """
        project = self.session.get(Project, project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")
        
        # Count synced action items
        action_count = self.session.exec(
            select(ActionItem).where(
                ActionItem.project_id == project_id,
                ActionItem.jira_key.isnot(None)
            )
        ).all()
        
        return SyncStatus(
            project_id=project_id,
            last_synced_at=project.last_synced_at,
            jira_configured=self.jira.is_configured,
            precursive_configured=self.precursive.is_configured,
            last_jira_items_count=len(action_count) if action_count else None,
            last_precursive_sync_success=project.precursive_id is not None,
            jira_project_key=project.jira_project_key,
            jira_project_name=project.jira_project_name,
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _extract_jira_project_key(self, jira_url: str) -> str:
        """
        Extract the Jira project key from various URL formats.
        
        Supported formats:
        - https://company.atlassian.net/browse/PROJ
        - https://company.atlassian.net/browse/PROJ-123
        - https://company.atlassian.net/jira/software/projects/PROJ/boards/1
        - https://company.atlassian.net/jira/software/c/projects/PROJ/boards/1
        
        Args:
            jira_url: The Jira URL to parse
            
        Returns:
            The project key (e.g., "PROJ")
            
        Raises:
            IntegrationError: If project key cannot be extracted
        """
        # Try /browse/KEY or /browse/KEY-123
        match = re.search(r'/browse/([A-Z][A-Z0-9_]*)', jira_url, re.IGNORECASE)
        if match:
            # If it's an issue key like PROJ-123, extract just PROJ
            key = match.group(1).upper()
            if '-' in key:
                key = key.split('-')[0]
            return key
        
        # Try /projects/KEY/
        match = re.search(r'/projects/([A-Z][A-Z0-9_]*)(?:/|$)', jira_url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        raise IntegrationError(
            f"Cannot extract Jira project key from URL: {jira_url}. "
            "Expected format like https://company.atlassian.net/browse/PROJ or "
            "https://company.atlassian.net/jira/software/projects/PROJ/boards/1"
        )
    
    def _create_action_from_jira(self, jira_issue: JiraIssue, project_id: UUID) -> ActionItem:
        """Create a new ActionItem from a Jira issue."""
        return ActionItem(
            project_id=project_id,
            title=jira_issue.summary,
            status=self._map_jira_status(jira_issue.status),
            assignee=jira_issue.assignee,
            priority=self._map_jira_priority(jira_issue.priority),
            jira_key=jira_issue.key,
            issue_type=jira_issue.issue_type,
            last_synced_at=datetime.utcnow(),
        )
    
    def _update_action_from_jira(self, action: ActionItem, jira_issue: JiraIssue) -> None:
        """Update an existing ActionItem from a Jira issue."""
        action.title = jira_issue.summary
        action.status = self._map_jira_status(jira_issue.status)
        action.assignee = jira_issue.assignee
        action.priority = self._map_jira_priority(jira_issue.priority)
        action.issue_type = jira_issue.issue_type
        action.last_synced_at = datetime.utcnow()
        self.session.add(action)
    
    def _map_jira_status(self, jira_status: str) -> ActionStatus:
        """
        Map Jira status to ActionStatus enum.
        
        Mapping:
        - To Do, Open, Backlog, New → TO_DO
        - In Progress, In Review, In Development → IN_PROGRESS
        - Done, Closed, Resolved, Complete → COMPLETE
        """
        status_lower = jira_status.lower()
        
        if any(s in status_lower for s in ['done', 'closed', 'resolved', 'complete']):
            return ActionStatus.COMPLETE
        elif any(s in status_lower for s in ['progress', 'review', 'development', 'testing']):
            return ActionStatus.IN_PROGRESS
        else:
            return ActionStatus.TO_DO
    
    def _map_jira_priority(self, jira_priority: Optional[str]) -> Priority:
        """
        Map Jira priority to Priority enum.
        
        Mapping:
        - Highest, High, Critical, Blocker → HIGH
        - Medium, Normal → MEDIUM
        - Low, Lowest, Minor, Trivial → LOW
        """
        if not jira_priority:
            return Priority.MEDIUM
        
        priority_lower = jira_priority.lower()
        
        if any(p in priority_lower for p in ['highest', 'high', 'critical', 'blocker']):
            return Priority.HIGH
        elif any(p in priority_lower for p in ['low', 'lowest', 'minor', 'trivial']):
            return Priority.LOW
        else:
            return Priority.MEDIUM
    
    def _map_delivery_phase_to_health(self, delivery_phase: str) -> HealthStatus:
        """
        Map Precursive delivery phase to HealthStatus.
        
        This is a simplified mapping - adjust based on your Precursive configuration.
        """
        phase_lower = delivery_phase.lower()
        
        if any(s in phase_lower for s in ['complete', 'closed', 'delivered']):
            return HealthStatus.GREEN
        elif any(s in phase_lower for s in ['at risk', 'delayed', 'blocked']):
            return HealthStatus.RED
        elif any(s in phase_lower for s in ['warning', 'concern', 'review']):
            return HealthStatus.YELLOW
        else:
            return HealthStatus.GREEN

    def _map_risk_probability(self, value: str) -> RiskProbability:
        val = value.lower()
        if "high" in val: return RiskProbability.HIGH
        if "medium" in val: return RiskProbability.MEDIUM
        return RiskProbability.LOW

    def _map_risk_impact(self, value: str) -> RiskImpact:
        val = value.lower()
        if "high" in val: return RiskImpact.HIGH
        if "medium" in val: return RiskImpact.MEDIUM
        return RiskImpact.LOW

    def _map_risk_status(self, value: str) -> RiskStatus:
        val = value.lower()
        if "closed" in val: return RiskStatus.CLOSED
        if "mitigated" in val: return RiskStatus.MITIGATED
        return RiskStatus.OPEN

    def _parse_date_string(self, date_str: str) -> date:
        """
        Parse a date string to a date object.
        
        Handles both date-only strings (e.g., "2025-06-11") and 
        datetime strings (e.g., "2025-06-11T00:00:00Z").
        
        Args:
            date_str: ISO format date or datetime string
            
        Returns:
            date object
            
        Raises:
            ValueError: If the string cannot be parsed
        """
        # Remove timezone suffix if present
        clean_str = date_str.replace('Z', '').split('+')[0]
        
        # Check if it's a date-only string (no 'T' separator)
        if 'T' not in clean_str:
            return date.fromisoformat(clean_str)
        
        # It's a datetime string, parse and extract date
        return datetime.fromisoformat(clean_str).date()

    def _parse_datetime_string(self, date_str: str) -> datetime:
        """
        Parse a date or datetime string to a datetime object.
        
        Handles both date-only strings (e.g., "2025-10-09") and 
        datetime strings (e.g., "2025-10-09T14:30:00Z").
        
        Args:
            date_str: ISO format date or datetime string
            
        Returns:
            datetime object (for date-only strings, time is set to 00:00:00)
            
        Raises:
            ValueError: If the string cannot be parsed
        """
        # Remove timezone suffix if present
        clean_str = date_str.replace('Z', '').split('+')[0]
        
        # Check if it's a date-only string (no 'T' separator)
        if 'T' not in clean_str:
            parsed_date = date.fromisoformat(clean_str)
            return datetime.combine(parsed_date, datetime.min.time())
        
        # It's a datetime string
        return datetime.fromisoformat(clean_str)
