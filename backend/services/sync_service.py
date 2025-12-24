"""Sync service for orchestrating data synchronization from external APIs."""

import re
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import Session, select

from config import Settings
from exceptions import ResourceNotFoundError
from integrations import JiraClient, SalesforcePrecursiveClient
from models import (
    ActionItem,
    ActionStatus,
    Priority,
    Project,
    Risk,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    SyncJob,
    SyncJobType,
)
from schemas.sync import (
    JiraSyncResult,
    PrecursiveSyncResult,
    SyncJobSummary,
    SyncResult,
    SyncStatus,
)

logger = structlog.get_logger()

# Backfill window to avoid missing updates due to clock skew
INCREMENTAL_SYNC_BACKFILL_MINUTES = 5


class SyncService:
    """Service for syncing project data from Jira and Precursive."""

    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.jira = JiraClient(settings)
        self.precursive = SalesforcePrecursiveClient(settings)
        # Import here to avoid circular dependency (sync_job_service imports models which sync_service also uses)
        from services.sync_job_service import SyncJobService

        self._sync_job_service = SyncJobService(session)

    async def close(self):
        """Close API client connections."""
        await self.jira.close()
        await self.precursive.close()

    def _safe_rollback(self) -> None:
        """Best-effort rollback to return the session to a usable state."""
        try:
            self.session.rollback()
        except Exception as e:
            # Intentionally swallow rollback errors (session may already be closed/broken),
            # but emit a debug log to aid investigations.
            logger.debug("Session rollback failed", error=str(e), exc_info=True)

    # =========================================================================
    # Status
    # =========================================================================

    def _job_to_summary(self, job: Optional[SyncJob]) -> Optional[SyncJobSummary]:
        """Convert a SyncJob model to a SyncJobSummary schema."""
        if not job:
            return None
        return SyncJobSummary(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            items_synced=job.items_synced,
            error=job.error,
        )

    def get_sync_status(self, project_id: UUID) -> SyncStatus:
        """
        Get the current sync status for a project.

        Returns rich status including:
        - Integration configured (credentials set in settings)
        - Project linked (project has URL/key/ID)
        - Active and last completed jobs for each integration
        """
        project = self.session.get(Project, project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found")

        assert project.id is not None, "Project must have an ID"

        # Get active and last completed jobs for each type via service
        jira_active = self._sync_job_service.get_active_job(
            project_id, SyncJobType.JIRA
        )
        jira_last = self._sync_job_service.get_last_completed_job(
            project_id, SyncJobType.JIRA
        )
        precursive_active = self._sync_job_service.get_active_job(
            project_id, SyncJobType.PRECURSIVE
        )
        precursive_last = self._sync_job_service.get_last_completed_job(
            project_id, SyncJobType.PRECURSIVE
        )

        return SyncStatus(
            project_id=project.id,
            last_synced_at=project.last_synced_at,
            # Integration configured (from settings/credentials)
            jira_integration_configured=self.jira.is_configured,
            precursive_integration_configured=self.precursive.is_configured,
            # Project linked (has URL/key/ID)
            jira_project_linked=bool(project.jira_project_key or project.jira_url),
            precursive_project_linked=bool(
                project.precursive_id or project.precursive_url
            ),
            # Project-level info
            jira_project_key=project.jira_project_key,
            jira_project_name=project.jira_project_name,
            # Job summaries
            jira_active_job=self._job_to_summary(jira_active),
            jira_last_job=self._job_to_summary(jira_last),
            precursive_active_job=self._job_to_summary(precursive_active),
            precursive_last_job=self._job_to_summary(precursive_last),
        )

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
            precursive=PrecursiveSyncResult(success=False),
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
                self._safe_rollback()
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
            self._safe_rollback()

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
            self._safe_rollback()

        return result

    def _get_last_successful_jira_sync(self, project_id: UUID) -> Optional[datetime]:
        """Get the completion time of the last successful Jira sync job."""
        last_job = self._sync_job_service.get_last_successful_job(
            project_id, SyncJobType.JIRA
        )

        if last_job and last_job.completed_at:
            return last_job.completed_at
        return None

    async def sync_jira_data(
        self, project: Project, force_full: bool = False
    ) -> JiraSyncResult:
        """
        Sync data from Jira.

        Args:
            project: The project to sync
            force_full: If True, ignore last sync time and do a full sync
        """
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
            # Extract board ID if missing
            if not project.jira_board_id:
                try:
                    boards = await self.jira.get_project_boards(
                        project.jira_project_key
                    )
                    if boards:
                        # Use the first board (typically the main board for the project)
                        project.jira_board_id = boards[0].get("id")
                        self.session.add(project)
                        self.session.commit()
                        logger.info(
                            "Extracted Jira board ID", board_id=project.jira_board_id
                        )
                except Exception as e:
                    logger.warning("Failed to fetch Jira boards", error=str(e))

            # Determine incremental sync window
            updated_since = None
            if not force_full and project.id:
                last_sync_time = self._get_last_successful_jira_sync(project.id)
                if last_sync_time:
                    # Apply backfill window to avoid missing updates
                    sync_cutoff = last_sync_time - timedelta(
                        minutes=INCREMENTAL_SYNC_BACKFILL_MINUTES
                    )
                    updated_since = sync_cutoff.strftime("%Y-%m-%d")
                    logger.info(
                        "Using incremental Jira sync",
                        project_id=str(project.id),
                        updated_since=updated_since,
                    )

            # Fetch Actions (Issues) - incremental if we have a last sync time
            issues = await self.jira.get_project_issues(
                project.jira_project_key,
                max_results=500,
                updated_since=updated_since,
            )
            res.actions_count = len(issues)

            # Pre-fetch all existing actions for this project to avoid N+1 queries
            existing_actions = self.session.exec(
                select(ActionItem).where(ActionItem.project_id == project.id)
            ).all()
            action_by_jira_key: dict[str, ActionItem] = {
                a.jira_key: a for a in existing_actions if a.jira_key
            }

            # Update DB
            for issue in issues:
                try:
                    # O(1) lookup instead of per-issue database query
                    existing = action_by_jira_key.get(issue.key)

                    if existing:
                        # Update existing action item
                        existing.title = issue.summary or existing.title
                        existing.status = self._map_jira_status(issue.status)
                        existing.assignee = issue.assignee
                        existing.priority = self._map_jira_priority(issue.priority)
                        # Ensure jira_id and jira_key are set correctly (for backward compatibility)
                        existing.jira_id = issue.id
                        existing.jira_key = issue.key
                        if issue.due_date:
                            try:
                                # Parse as datetime (at midnight) to match model type
                                existing.due_date = datetime.strptime(
                                    issue.due_date, "%Y-%m-%d"
                                )
                            except ValueError:
                                logger.warning(
                                    "Invalid due_date format",
                                    due_date=issue.due_date,
                                    issue_key=issue.key,
                                )
                        self.session.add(existing)
                    else:
                        # Parse due_date with error handling to match update behavior
                        due_date = None
                        if issue.due_date:
                            try:
                                due_date = datetime.strptime(issue.due_date, "%Y-%m-%d")
                            except ValueError:
                                logger.warning(
                                    "Invalid due_date format for new action",
                                    due_date=issue.due_date,
                                    issue_key=issue.key,
                                )
                                # Continue without due_date instead of skipping the action

                        new_action = ActionItem(
                            project_id=project.id,
                            jira_id=issue.id,  # Internal Jira issue ID
                            jira_key=issue.key,  # Public issue key like "PROJ-123" (indexed)
                            title=issue.summary or "Untitled",
                            status=self._map_jira_status(issue.status),
                            assignee=issue.assignee,
                            priority=self._map_jira_priority(issue.priority),
                            due_date=due_date,
                        )
                        self.session.add(new_action)
                except Exception as e:
                    logger.error(
                        "Error processing Jira issue", issue_key=issue.key, error=str(e)
                    )
                    # Continue with next issue instead of failing entire sync
                    continue

            # Fetch Sprint Goals
            if project.jira_board_id:
                try:
                    sprint_goal = await self.jira.get_active_sprint_goal(
                        project.jira_board_id
                    )
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
            self._safe_rollback()

        return res

    async def sync_precursive_data(self, project: Project) -> PrecursiveSyncResult:
        """Sync data from Precursive."""
        res = PrecursiveSyncResult(success=True)
        errors = []

        # Step 1: Try to get or set precursive_id from URL
        precursive_project = None
        if not project.precursive_id and project.precursive_url:
            try:
                precursive_project = await self.precursive.get_project_by_url(
                    project.precursive_url
                )
                if precursive_project:
                    project.precursive_id = precursive_project.id
                    # Also update project name and client name if available
                    if precursive_project.name and not project.name:
                        project.name = precursive_project.name
                    if precursive_project.client_name:
                        project.client_name = precursive_project.client_name
                    # Sync dates for timeline (use delivery_start_date/delivery_end_date)
                    self._sync_precursive_dates(project, precursive_project)
                    self.session.add(project)
                    logger.info(
                        "Extracted Precursive project ID from URL",
                        precursive_id=precursive_project.id,
                    )
            except Exception as e:
                logger.warning(
                    "Failed to get Precursive project from URL", error=str(e)
                )

        # Also try to get project details if we have precursive_id but haven't fetched it yet
        if project.precursive_id and not precursive_project:
            try:
                precursive_project = await self.precursive.get_project_by_id(
                    project.precursive_id
                )
                if precursive_project:
                    self._sync_precursive_dates(project, precursive_project)
                    if precursive_project.client_name:
                        project.client_name = precursive_project.client_name
                    self.session.add(project)
            except Exception as e:
                logger.warning(
                    "Failed to fetch Precursive project details", error=str(e)
                )

        # Step 1.5: Sync health indicators from Precursive project
        if precursive_project:
            self._sync_precursive_health_indicators(project, precursive_project)
            self.session.add(project)

        # Step 2: Sync Financials
        try:
            financials = None
            if project.precursive_id:
                try:
                    financials = await self.precursive.get_project_financials(
                        project.precursive_id
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch Precursive financials", error=str(e)
                    )

            if financials and financials.has_any_financial_data():
                # Use the dataclass methods for computing budget values
                computed_total = financials.compute_total_budget()
                computed_spent = financials.compute_spent_budget()

                logger.info(
                    "Processing Precursive financials",
                    project_id=str(project.id),
                    computed_total_budget=computed_total,
                    computed_spent_budget=computed_spent,
                    remaining_budget=financials.remaining_budget,
                    currency=financials.currency,
                )

                updated = False

                if computed_total is not None and computed_total > 0:
                    project.total_budget = computed_total
                    if computed_spent is not None:
                        project.spent_budget = computed_spent
                    if financials.remaining_budget is not None:
                        project.remaining_budget = financials.remaining_budget
                    updated = True
                elif financials.remaining_budget is not None:
                    # Only remaining_budget available - still useful
                    project.remaining_budget = financials.remaining_budget
                    updated = True

                # Always update the additional financial details if we have any data
                if financials.overrun_investment is not None:
                    project.overrun_investment = financials.overrun_investment
                    updated = True
                if financials.total_days_actuals_planned is not None:
                    project.total_days_actuals = financials.total_days_actuals_planned
                    updated = True
                if financials.budgeted_days_delivery is not None:
                    project.budgeted_days_delivery = financials.budgeted_days_delivery
                    updated = True
                if financials.budgeted_hours_delivery is not None:
                    project.budgeted_hours_delivery = financials.budgeted_hours_delivery
                    updated = True

                if updated:
                    project.currency = financials.currency
                    self.session.add(project)
                    res.financials_updated = True
                    res.message = "Synced financials from Precursive"
                else:
                    logger.warning(
                        "Precursive returned financial data but could not compute budget",
                        project_id=str(project.id),
                        has_fte_days=financials.total_fte_days is not None,
                        has_fte_price=financials.fte_day_price is not None,
                        has_role_budgets=any(
                            [
                                financials.pm_budget,
                                financials.sa_budget,
                                financials.de_budget,
                                financials.ds_budget,
                            ]
                        ),
                    )
            elif financials:
                logger.info(
                    "Precursive financials query succeeded but no data available",
                    project_id=str(project.id),
                )

        except Exception as e:
            errors.append(f"Financials sync failed: {str(e)}")

        # Step 3: Sync Risks
        try:
            risks_synced = 0

            # First, try to sync embedded project-level risk from Precursive
            if precursive_project and precursive_project.risk_level:
                risks_synced += self._sync_precursive_embedded_risk(
                    project, precursive_project
                )

            # Also try to get any additional risks from Precursive (for mock compatibility)
            risks_data = []
            if project.precursive_id:
                try:
                    risks_data = await self.precursive.get_project_risks(
                        project.precursive_id
                    )
                except Exception as e:
                    logger.warning("Failed to fetch Precursive risks", error=str(e))

            if risks_data:
                # Real data logic - use mock Precursive data
                for risk_data in risks_data:
                    # Use summary for title, description for description
                    existing_risk = self.session.exec(
                        select(Risk).where(
                            Risk.project_id == project.id,
                            Risk.title == risk_data.summary,
                        )
                    ).first()

                    if existing_risk:
                        existing_risk.description = risk_data.description
                        existing_risk.probability = self._map_risk_probability(
                            risk_data.probability
                        )
                        existing_risk.impact = self._map_risk_impact(risk_data.impact)
                        existing_risk.status = self._map_risk_status(risk_data.status)
                        existing_risk.mitigation_plan = risk_data.mitigation_plan
                        existing_risk.category = risk_data.category
                        existing_risk.impact_rationale = risk_data.impact_rationale
                        if risk_data.date_identified:
                            try:
                                existing_risk.date_identified = datetime.strptime(
                                    risk_data.date_identified, "%Y-%m-%d"
                                )
                            except ValueError:
                                existing_risk.date_identified = datetime.now()
                        self.session.add(existing_risk)
                    else:
                        # Parse date_identified with error handling to match update behavior
                        date_identified = datetime.now()
                        if risk_data.date_identified:
                            try:
                                date_identified = datetime.strptime(
                                    risk_data.date_identified, "%Y-%m-%d"
                                )
                            except ValueError:
                                logger.warning(
                                    "Invalid date_identified format for new risk",
                                    date_identified=risk_data.date_identified,
                                    risk_summary=risk_data.summary,
                                )
                                # Use current date as fallback instead of failing

                        new_risk = Risk(
                            project_id=project.id,
                            title=risk_data.summary,
                            description=risk_data.description,
                            probability=self._map_risk_probability(
                                risk_data.probability
                            ),
                            impact=self._map_risk_impact(risk_data.impact),
                            status=self._map_risk_status(risk_data.status),
                            mitigation_plan=risk_data.mitigation_plan,
                            category=risk_data.category,
                            impact_rationale=risk_data.impact_rationale,
                            date_identified=date_identified,
                        )
                        self.session.add(new_risk)

                risks_synced += len(risks_data)

            if risks_synced > 0:
                res.risks_count = risks_synced
                if not res.message:
                    res.message = "Synced risks from Precursive"
            else:
                # No external risk data available - report existing risks count
                existing_risks = self.session.exec(
                    select(Risk).where(Risk.project_id == project.id)
                ).all()
                res.risks_count = len(existing_risks)
                if existing_risks and not res.message:
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
        """Map Jira status to ActionStatus, defaulting to NO_STATUS if None or unknown."""
        if not status:
            return ActionStatus.NO_STATUS
        s = status.lower()
        if s in ["done", "complete", "closed", "resolved"]:
            return ActionStatus.COMPLETE
        elif s in ["in progress", "in review", "qa"]:
            return ActionStatus.IN_PROGRESS
        elif s in ["to do", "backlog", "open", "new", "created"]:
            return ActionStatus.TO_DO
        return ActionStatus.NO_STATUS

    def _map_jira_priority(self, priority: Optional[str]) -> Priority:
        """Map Jira priority to Priority, defaulting to MEDIUM if None or unknown."""
        if not priority:
            return Priority.MEDIUM
        p = priority.lower()
        if p in ["high", "critical", "blocker"]:
            return Priority.HIGH
        elif p in ["low", "trivial"]:
            return Priority.LOW
        return Priority.MEDIUM

    def _map_risk_probability(self, prob: str) -> RiskProbability:
        p = prob.lower()
        if "high" in p:
            return RiskProbability.HIGH
        if "low" in p:
            return RiskProbability.LOW
        return RiskProbability.MEDIUM

    def _map_risk_impact(self, impact: str) -> RiskImpact:
        i = impact.lower()
        if "high" in i:
            return RiskImpact.HIGH
        if "low" in i:
            return RiskImpact.LOW
        return RiskImpact.MEDIUM

    def _map_risk_status(self, status: str) -> RiskStatus:
        """Map Precursive risk status to RiskStatus enum."""
        if not status:
            return RiskStatus.OPEN
        s = status.lower()
        if s in ["closed", "resolved"]:
            return RiskStatus.CLOSED
        elif s in ["mitigated", "mitigation"]:
            return RiskStatus.MITIGATED
        return RiskStatus.OPEN

    def _sync_precursive_dates(self, project: Project, precursive_project) -> None:
        """Sync delivery dates from Precursive project to local project."""
        # Use delivery_start_date/delivery_end_date from new dataclass
        start_date_str = getattr(
            precursive_project, "delivery_start_date", None
        ) or getattr(precursive_project, "start_date", None)
        end_date_str = getattr(
            precursive_project, "delivery_end_date", None
        ) or getattr(precursive_project, "end_date", None)

        if start_date_str and not project.start_date:
            try:
                project.start_date = datetime.strptime(
                    start_date_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                logger.warning(
                    "Invalid start_date format",
                    start_date=start_date_str,
                )

        if end_date_str and not project.end_date:
            try:
                project.end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(
                    "Invalid end_date format",
                    end_date=end_date_str,
                )

    def _sync_precursive_health_indicators(
        self, project: Project, precursive_project
    ) -> None:
        """Sync health indicators from Precursive project to local project."""
        # Map Precursive health indicators to project fields
        project.precursive_project_health = getattr(
            precursive_project, "project_health", None
        )
        project.precursive_time_health = getattr(
            precursive_project, "time_health", None
        )
        project.precursive_cost_health = getattr(
            precursive_project, "cost_health", None
        )
        project.precursive_resources_health = getattr(
            precursive_project, "resources_health", None
        )
        project.precursive_status_summary = getattr(
            precursive_project, "overall_status_summary", None
        )

        logger.info(
            "Synced Precursive health indicators",
            project_id=str(project.id),
            project_health=project.precursive_project_health,
            time_health=project.precursive_time_health,
            cost_health=project.precursive_cost_health,
            resources_health=project.precursive_resources_health,
        )

    def _sync_precursive_embedded_risk(
        self, project: Project, precursive_project
    ) -> int:
        """Sync embedded project-level risk from Precursive.

        Returns the number of risks synced (0 or 1).
        """
        risk_level = getattr(precursive_project, "risk_level", None)
        risk_description = getattr(precursive_project, "risk_description", None)

        if not risk_level:
            return 0

        # Look for existing Precursive-sourced risk
        existing_precursive_risk = self.session.exec(
            select(Risk).where(
                Risk.project_id == project.id,
                Risk.source == "precursive",
            )
        ).first()

        probability = self._map_risk_level_to_probability(risk_level)
        impact = self._map_risk_level_to_impact(risk_level)

        if existing_precursive_risk:
            # Update existing risk
            existing_precursive_risk.description = (
                risk_description or "Project-level risk from Precursive"
            )
            existing_precursive_risk.probability = probability
            existing_precursive_risk.impact = impact
            self.session.add(existing_precursive_risk)
            logger.info(
                "Updated existing Precursive risk",
                risk_id=str(existing_precursive_risk.id),
                risk_level=risk_level,
            )
        else:
            # Create new risk from Precursive
            new_risk = Risk(
                project_id=project.id,
                title="Overall Project Risk",
                description=risk_description or "Project-level risk from Precursive",
                probability=probability,
                impact=impact,
                status=RiskStatus.OPEN,
                source="precursive",
                date_identified=datetime.now(),
            )
            self.session.add(new_risk)
            logger.info(
                "Created new Precursive risk",
                project_id=str(project.id),
                risk_level=risk_level,
            )

        return 1

    def _map_risk_level_to_probability(self, risk_level: str) -> RiskProbability:
        """Map Precursive risk level to probability."""
        if not risk_level:
            return RiskProbability.MEDIUM
        level = risk_level.lower()
        if "high" in level:
            return RiskProbability.HIGH
        if "low" in level:
            return RiskProbability.LOW
        return RiskProbability.MEDIUM

    def _map_risk_level_to_impact(self, risk_level: str) -> RiskImpact:
        """Map Precursive risk level to impact."""
        if not risk_level:
            return RiskImpact.MEDIUM
        level = risk_level.lower()
        if "high" in level:
            return RiskImpact.HIGH
        if "low" in level:
            return RiskImpact.LOW
        return RiskImpact.MEDIUM
