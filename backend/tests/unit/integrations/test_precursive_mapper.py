"""TDD tests for Precursive field mapper.

These tests use real sample data from the Salesforce schema discovery
to verify the field mapping logic before implementation.
"""

from integrations.precursive.field_mapper import (
    map_salesforce_to_financials,
    map_salesforce_to_project,
)

# Sample data from precursive_schema_discovery.json (actual API response)
SAMPLE_PROJECT_RAW = {
    "attributes": {
        "type": "preempt__PrecursiveProject__c",
        "url": "/services/data/v59.0/sobjects/preempt__PrecursiveProject__c/a2X3X000002chI5UAI",
    },
    "Id": "a2X3X000002chI5UAI",
    "OwnerId": "0053X00000EG6SUQA1",
    "IsDeleted": False,
    "Name": "Admin",
    "CurrencyIsoCode": "USD",
    "RecordTypeId": None,
    "CreatedDate": "2021-09-08T12:47:37.000+0000",
    "CreatedById": "0053X00000EG6SUQA1",
    "LastModifiedDate": "2025-12-19T15:30:06.000+0000",
    "LastModifiedById": "0053X00000EGMm1QAH",
    "SystemModstamp": "2025-12-19T15:30:06.000+0000",
    "LastViewedDate": None,
    "LastReferencedDate": None,
    "preempt__Status__c": None,
    "preempt__account__c": "0013X00003VAfIAQA1",
    "preempt__budgetBy__c": "Fees",
    "preempt__budgetUnit__c": "Hours",
    "preempt__currency__c": None,
    "preempt__projectCategory__c": "Admin",
    "Account_Manager__c": "Unassigned Account",
    "CSM__c": None,
    "Delivery_Manager__c": None,
    "Project_Manager__c": None,
    "Project_TShirt_Size__c": None,
    "Vertical_Industry__c": "Other",
    "Current_User_YN__c": False,
    "Project_Crew__c": None,
    "Pod_Account_Owner__c": None,
    "Pod_CSM__c": None,
    "Proposal_Start_Date__c": None,
    "Proposal_Delivery_Date__c": None,
    "SOW_Start_Date__c": None,
    "SOW_Delivery_Date__c": None,
    "Proposal_Turnaround_Days__c": None,
    "SOW_Turnaround_Days__c": None,
    "Solution_Infrastructure__c": None,
    "Delivery_Responsible__c": None,
    "Partner__c": None,
    "Total_FTEs__c": None,
    "Baseline_Duration_Weeks__c": None,
    "Traveling_Required__c": False,
    "Special_Considerations__c": None,
    "Total_Days_Actuals_Planned__c": 1387.17,
    "Scope_Prerequisites__c": None,
    "FTE_Day_Price__c": None,
    "Project_Risk_Level__c": None,
    "Risk_Description__c": None,
    "Budgeted_Days_in_Delivery_Phase__c": None,
    "Turnaround_SLA_Met__c": False,
    "Customer_Success_Director__c": None,
    "Delivery_Start_Date__c": None,
    "Delivery_End_Date__c": None,
    "Account_Location__c": "Norway",
    "Duration_Weeks__c": None,
    "Vertical__c": None,
    "Current_User_PM_or_Owner__c": False,
    "SOW_Turnaround_SLA_Met__c": False,
    "Deliverables__c": None,
    "Product_Dependencies__c": None,
    "Create_Default_Phases_Activities__c": False,
    "Duration_Difference_Weeks__c": 0.0,
    "Scope_Status__c": "On track",
    "Time_Status__c": "N/A",
    "Which_Products_Engineering_Team_s__c": None,
    "First_Billable_Booking_Date__c": None,
    "Overrun_Investment__c": 18033166.67,
    "Overrun_Investment_Diff__c": None,
    "Cost_Status__c": "N/A",
    "PM_Budget__c": 0.0,
    "SA_Budget__c": 0.0,
    "DE_Budget__c": 0.0,
    "DS_Budget__c": 0.0,
    "PM_Projection_Hours__c": 0.0,
    "DE_Projection_Hours__c": 171.5,
    "SA_Projection_Hours__c": 0.0,
    "DS_Projection_Hours__c": 0.0,
    "PM_Budgeted_FTE__c": None,
    "DE_Budgeted_FTE__c": None,
    "DS_Budgeted_FTE__c": None,
    "SA_Budgeted_FTE__c": None,
    "PM_Actual_FTE__c": None,
    "DE_Actual_FTE__c": None,
    "DS_Actual_FTE__c": None,
    "SA_Actual_FTE__c": None,
    "PM_FTE_Difference__c": None,
    "DE_FTE_Difference__c": None,
    "DS_FTE_Difference__c": None,
    "SA_FTE_Difference__c": None,
    "Resources_Status__c": None,
    "Project_Status__c": "N/A",
    "Cost_Comments2__c": None,
    "Scope_Comments2__c": None,
    "Time_Comments2__c": None,
    "Resources_Comments2__c": None,
    "Product_Teams__c": None,
    "Prognosis_status__c": None,
    "Type_of_service_Secondary__c": None,
    "Last_Project_Status_Update__c": None,
    "Project_Status_Last_Updated_By__c": None,
    "Amber_Subcategories__c": 0.0,
    "Resources_Status2__c": "On track",
    "Budgeted_Hours_in_Delivery_Phase__c": 0.0,
    "PM_FTE_Difference_Status__c": None,
    "SA_FTE_Status__c": None,
    "DE_FTE_Status__c": None,
    "DS_FTE_Status__c": None,
    "Last_Project_Status_Update2__c": None,
    "Mobilizing_Actual_Days__c": 0.0,
    "Mobilizing_Plan_to_Complete_Days__c": 0.0,
    "Mobilizing_Total_FTE_Days__c": 0.0,
    "Mobilizing_Overrun__c": 0.0,
    "GTM_Play__c": None,
    "Time_Status_Pick__c": "N/A",
    "Scope_Status_Pick__c": "On track",
    "Cost_Status_Pick__c": "N/A",
    "Resources_Status_Pick__c": "On track",
    "Project_Status_Pick__c": None,
    "Duration_Difference_Percentual__c": 0.0,
    "Force_Update__c": False,
    "Last_Billable_Booking_Date__c": "2022-03-04",
    "Resources_Status_3__c": None,
    "Type_of_service_Primary__c": None,
    "AKER_ASA_affiliated_customer__c": False,
    "Require_Investment__c": False,
    "Solution_Type__c": None,
    "Success_Criteria__c": None,
    "Partnership__c": None,
    "Solution_Support__c": False,
    "Product_Dependencies_Comments__c": None,
    "LT_Comments__c": None,
    "Standard_Product__c": None,
    "Customer_value__c": None,
    "TargetMAU__c": None,
    "ActualMAU__c": None,
    "PlatinumSuccessTrack__c": False,
    "Atlas_AI__c": False,
    "Opportunity_Close_Date__c": None,
    "Capacity_Scenario__c": None,
    "Account_MAIA_Stage__c": None,
    "Remaining_Budget__c": 0.0,
    "Remaining_Budget_in_Fees_org__c": 0.0,
    "Active_Status__c": None,
}

# Minimal sample for focused testing
SAMPLE_PROJECT_MINIMAL = {
    "Id": "a2X3X000002chI5UAI",
    "Name": "Admin",
    "preempt__Status__c": None,
    "preempt__projectCategory__c": "Admin",
    "Delivery_Start_Date__c": None,
    "Delivery_End_Date__c": None,
    "Project_Status_Pick__c": None,
    "Time_Status_Pick__c": "N/A",
    "Cost_Status_Pick__c": "N/A",
    "Resources_Status_Pick__c": "On track",
    "Scope_Comments2__c": None,
    "Project_Risk_Level__c": None,
    "Risk_Description__c": None,
    "CurrencyIsoCode": "USD",
    "Remaining_Budget__c": 0.0,
    "Total_FTEs__c": None,
    "FTE_Day_Price__c": None,
    "Overrun_Investment__c": 18033166.67,
}

# Sample with account relationship data
SAMPLE_PROJECT_WITH_ACCOUNT = {
    **SAMPLE_PROJECT_MINIMAL,
    "preempt__account__r": {"Name": "Cognite Test Client"},
}

# Sample with risk data populated
SAMPLE_PROJECT_WITH_RISK = {
    **SAMPLE_PROJECT_MINIMAL,
    "Project_Risk_Level__c": "High",
    "Risk_Description__c": "Critical dependency on third-party vendor delivery timeline.",
}

# Sample with all health indicators populated
SAMPLE_PROJECT_HEALTHY = {
    **SAMPLE_PROJECT_MINIMAL,
    "Project_Status_Pick__c": "On track",
    "Time_Status_Pick__c": "On track",
    "Cost_Status_Pick__c": "Minor deviations",
    "Resources_Status_Pick__c": "On track",
    "Scope_Comments2__c": "Project is progressing well, minor budget variance expected.",
}


class TestMapSalesforceToProject:
    """Tests for map_salesforce_to_project function."""

    def test_maps_core_fields(self):
        """Test that core fields are mapped correctly."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.id == "a2X3X000002chI5UAI"
        assert project.name == "Admin"
        assert project.project_category == "Admin"

    def test_handles_null_status(self):
        """Test that null status is preserved as None."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.status is None

    def test_maps_health_indicators(self):
        """Test that health indicator fields are mapped correctly."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.resources_health == "On track"
        assert project.time_health == "N/A"
        assert project.cost_health == "N/A"
        assert project.project_health is None

    def test_handles_null_risk_fields(self):
        """Test that null risk fields are preserved as None."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.risk_level is None
        assert project.risk_description is None

    def test_maps_risk_fields_when_populated(self):
        """Test that risk fields are mapped when populated."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_WITH_RISK)

        assert project.risk_level == "High"
        assert (
            project.risk_description
            == "Critical dependency on third-party vendor delivery timeline."
        )

    def test_maps_client_name_from_relationship(self):
        """Test that client name is extracted from account relationship."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_WITH_ACCOUNT)

        assert project.client_name == "Cognite Test Client"

    def test_handles_missing_account_relationship(self):
        """Test that missing account relationship results in None client name."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.client_name is None

    def test_maps_all_health_indicators(self):
        """Test that all health indicators are mapped correctly."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_HEALTHY)

        assert project.project_health == "On track"
        assert project.time_health == "On track"
        assert project.cost_health == "Minor deviations"
        assert project.resources_health == "On track"
        assert (
            project.overall_status_summary
            == "Project is progressing well, minor budget variance expected."
        )

    def test_handles_null_dates(self):
        """Test that null dates are preserved as None."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_MINIMAL)

        assert project.delivery_start_date is None
        assert project.delivery_end_date is None

    def test_maps_full_sample_data(self):
        """Test mapping of the full sample project data from schema discovery."""
        project = map_salesforce_to_project(SAMPLE_PROJECT_RAW)

        assert project.id == "a2X3X000002chI5UAI"
        assert project.name == "Admin"
        assert project.project_category == "Admin"
        assert project.status is None
        assert project.resources_health == "On track"
        assert project.time_health == "N/A"


class TestMapSalesforceToFinancials:
    """Tests for map_salesforce_to_financials function."""

    def test_maps_currency(self):
        """Test that currency is mapped correctly."""
        financials = map_salesforce_to_financials("test-id", SAMPLE_PROJECT_MINIMAL)

        assert financials.currency == "USD"

    def test_maps_project_id(self):
        """Test that project_id is set correctly."""
        financials = map_salesforce_to_financials(
            "my-project-id", SAMPLE_PROJECT_MINIMAL
        )

        assert financials.project_id == "my-project-id"

    def test_maps_overrun_investment(self):
        """Test that overrun investment is mapped correctly."""
        financials = map_salesforce_to_financials("test-id", SAMPLE_PROJECT_MINIMAL)

        assert financials.overrun_investment == 18033166.67

    def test_handles_null_budget(self):
        """Test that zero budget is mapped correctly."""
        financials = map_salesforce_to_financials("test-id", SAMPLE_PROJECT_MINIMAL)

        assert financials.remaining_budget == 0.0

    def test_handles_null_fte_fields(self):
        """Test that null FTE fields are preserved as None."""
        financials = map_salesforce_to_financials("test-id", SAMPLE_PROJECT_MINIMAL)

        assert financials.total_fte_days is None
        assert financials.fte_day_price is None

    def test_maps_full_sample_data(self):
        """Test mapping of the full sample data for financials."""
        financials = map_salesforce_to_financials("test-id", SAMPLE_PROJECT_RAW)

        assert financials.currency == "USD"
        assert financials.overrun_investment == 18033166.67
        assert financials.remaining_budget == 0.0

    def test_defaults_currency_to_usd_when_missing(self):
        """Test that currency defaults to USD when not present."""
        data = {"Id": "test"}  # No CurrencyIsoCode field
        financials = map_salesforce_to_financials("test-id", data)

        assert financials.currency == "USD"
