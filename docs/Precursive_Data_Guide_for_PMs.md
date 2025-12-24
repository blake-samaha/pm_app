# Precursive Data Guide for Project Managers

**Document Purpose:** This guide explains what project data the PM Portal can retrieve from Precursive (Salesforce) and helps PMs understand which fields need to be populated for the portal to display financial and project health information.

**Last Updated:** December 21, 2025

---

## Quick Summary

The PM Portal syncs the following data from Precursive:

| Category | Status | What You'll See |
|----------|--------|-----------------|
| **Project Health (RAG)** | ✅ Working | Green/Amber/Red indicators for Time, Cost, Resources |
| **Financial Data** | ⚠️ Partial | Only some fields are populated in Precursive |
| **Risk Information** | ✅ Working | Project risk level and description |
| **Dates** | ✅ Working | Delivery start and end dates |

---

## What We Need From You

For the portal to display **complete financial information**, the following fields should be populated in Precursive for each project:

### Required for Budget Display

| Precursive Field | Where to Find It | Why It's Needed |
|------------------|------------------|-----------------|
| **FTE/Day Price** | Project Details → Financial | Used to calculate total budget |
| **Contractual FTE Days** | Project Details → Financial | Multiplied by day price = total budget |

**Example:** If FTE/Day Price = $1,500 and Contractual FTE Days = 100, then Total Budget = $150,000

### Nice to Have (More Detail)

| Precursive Field | What It Shows |
|------------------|---------------|
| PM Budget | Days allocated to Project Management |
| SA Budget | Days allocated to Solution Architects |
| DE Budget | Days allocated to Data Engineers |
| DS Budget | Days allocated to Data Scientists |

---

## Current Sync Results (Real Data)

We query **34 financial fields** from Salesforce. Here's what we're actually receiving for a sample project:

### ✅ Fields With Data

| Field | Sample Value | Usable? |
|-------|--------------|---------|
| Currency | USD | ✅ Yes |
| Remaining Budget | $127,000 | ✅ Yes |
| Total Overrun Investment | $1,495,866 | ✅ Yes |
| Total Days (Actuals + Planned) | 265.07 days | ✅ Yes |
| Cost Status | Requires attention | ✅ Yes |
| Time Status | Requires attention | ✅ Yes |
| Resources Status | On track | ✅ Yes |

### ❌ Fields That Are Empty or Zero

| Field | Current Value | Impact |
|-------|---------------|--------|
| **FTE/Day Price** | `null` | ❌ Cannot calculate total budget |
| **Contractual FTE Days** | `null` | ❌ Cannot calculate total budget |
| PM Budget | 0.0 | No data |
| SA Budget | 0.0 | No data |
| DE Budget | 0.0 | No data |
| DS Budget | 0.0 | No data |
| PM Budgeted FTE | 0.0 | No data |
| SA Budgeted FTE | 0.0 | No data |
| DE Budgeted FTE | 0.0 | No data |
| DS Budgeted FTE | 0.0 | No data |
| PM Actual FTE | 0.0 | No data |
| SA Actual FTE | 0.0 | No data |
| DE Actual FTE | 0.0 | No data |
| DS Actual FTE | 0.0 | No data |
| Budgeted Days in Delivery | `null` | No data |
| Budgeted Hours in Delivery | 0.0 | No data |

### Summary

**Out of 34 financial fields we can access, only 4 have meaningful data:**
1. Remaining Budget
2. Overrun Investment  
3. Total Days (Actuals + Planned)
4. Currency

**The two critical fields needed to calculate Total Budget are both empty:**
- FTE/Day Price = `null`
- Contractual FTE Days = `null`

---

## How Budget Calculation Works

The portal tries to calculate your project's **Total Budget** using this logic:

```
Method 1 (Preferred):
Total Budget = Contractual FTE Days × FTE/Day Price

Method 2 (Fallback):
Total Budget = (PM Budget + SA Budget + DE Budget + DS Budget) × FTE/Day Price

If neither works:
→ Portal shows "Remaining Budget" only (currently $127,000)
→ Cannot show Total Budget or Spent Budget
```

### What You Can Do

1. **Open your project in Precursive**
2. **Navigate to the Financial section**
3. **Ensure these fields are populated:**
   - FTE/Day Price (e.g., $1,500/day)
   - Contractual FTE Days (e.g., 100 days)

Once these are set, the next sync will pull the data and display your full budget breakdown.

---

## All 34 Fields We Query

Here's the complete list of financial fields we retrieve from Precursive:

### Core Financial Fields (6 fields)
| Field Name in Precursive | API Field | Status |
|--------------------------|-----------|--------|
| Contractual FTE Days | `Total_FTEs__c` | ❌ null |
| FTE/Day Price | `FTE_Day_Price__c` | ❌ null |
| Remaining Budget in Fees | `Remaining_Budget__c` | ✅ $127,000 |
| Remaining Budget (Org Currency) | `Remaining_Budget_in_Fees_org__c` | 0.0 |
| Total Overrun Investment | `Overrun_Investment__c` | ✅ $1,495,866 |
| Overrun Investment Diff | `Overrun_Investment_Diff__c` | null |

### Day/Hour Tracking (3 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| Total Days (Actuals + Planned) | `Total_Days_Actuals_Planned__c` | ✅ 265.07 |
| Budgeted Days in Delivery | `Budgeted_Days_in_Delivery_Phase__c` | null |
| Budgeted Hours in Delivery | `Budgeted_Hours_in_Delivery_Phase__c` | 0.0 |

### Role-Based Budgets (4 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| PM Budget | `PM_Budget__c` | 0.0 |
| SA Budget | `SA_Budget__c` | 0.0 |
| DE Budget | `DE_Budget__c` | 0.0 |
| DS Budget | `DS_Budget__c` | 0.0 |

### Role-Based Budgeted FTE (4 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| PM Budgeted FTE | `PM_Budgeted_FTE__c` | 0.0 |
| SA Budgeted FTE | `SA_Budgeted_FTE__c` | 0.0 |
| DE Budgeted FTE | `DE_Budgeted_FTE__c` | 0.0 |
| DS Budgeted FTE | `DS_Budgeted_FTE__c` | 0.0 |

### Role-Based Actual FTE (4 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| PM Actual FTE | `PM_Actual_FTE__c` | 0.0 |
| SA Actual FTE | `SA_Actual_FTE__c` | 0.0 |
| DE Actual FTE | `DE_Actual_FTE__c` | 0.0 |
| DS Actual FTE | `DS_Actual_FTE__c` | 0.0 |

### Role-Based Variance (4 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| PM FTE Difference | `PM_FTE_Difference__c` | null |
| SA FTE Difference | `SA_FTE_Difference__c` | null |
| DE FTE Difference | `DE_FTE_Difference__c` | null |
| DS FTE Difference | `DS_FTE_Difference__c` | null |

### Mobilization Phase (2 fields)
| Field Name | API Field | Status |
|------------|-----------|--------|
| Mobilizing Total FTE Days | `Mobilizing_Total_FTE_Days__c` | null |
| Mobilizing Overrun | `Mobilizing_Overrun__c` | null |

---

## Health Status Fields

These are the RAG (Red/Amber/Green) status indicators (all working ✅):

| Field | API Field | Possible Values |
|-------|-----------|-----------------|
| Project Status | `Project_Status_Pick__c` | On track, Minor deviations, Requires attention |
| Time Status | `Time_Status_Pick__c` | On track, Minor deviations, Requires attention, N/A |
| Cost Status | `Cost_Status_Pick__c` | On track, Minor deviations, Requires attention, N/A |
| Resources Status | `Resources_Status_Pick__c` | On track, Minor deviations, Requires attention, N/A |

---

## Troubleshooting

### "Financial data unavailable" or only showing Remaining Budget

**Cause:** The required budget fields (`FTE/Day Price` and `Contractual FTE Days`) are not populated in Precursive.

**Current State:** We can only show Remaining Budget ($127,000) because the fields needed to calculate Total Budget are empty.

**Fix:**
1. Open the project in Precursive
2. Go to Project Details → Financial
3. Set the **FTE/Day Price** field (e.g., $1,500/day)
4. Set the **Contractual FTE Days** field (e.g., 100 days)
5. Click "Sync Precursive" in the PM Portal

### Health indicators not showing

**Cause:** The project status fields haven't been updated in Precursive.

**Fix:**
1. Open the project in Precursive
2. Update the Project Status, Time Status, Cost Status, and Resources Status fields
3. Click "Sync Precursive" in the PM Portal

### All role budgets showing as 0.0

**Cause:** The PM/SA/DE/DS Budget fields are not being used for this project in Precursive.

**Note:** This may be expected if your project uses a different budgeting model. The key fields are FTE/Day Price and Contractual FTE Days.

---

## Questions?

Contact the PM Portal team:
- Blake Samaha
- Hana Kabazi
- Vince Kapadia

---

## Technical Reference

For developers, the Salesforce API field names are documented in:
- `backend/integrations/precursive/salesforce_schema.py`

Key fields:
```
Total_FTEs__c              → Contractual FTE Days
FTE_Day_Price__c           → FTE/Day Price
Remaining_Budget__c        → Remaining Budget in Fees
Overrun_Investment__c      → Total Overrun Investment
Total_Days_Actuals_Planned__c → Total Days (Actuals + Planned)
```

Role-based fields:
```
PM_Budget__c / SA_Budget__c / DE_Budget__c / DS_Budget__c
PM_Budgeted_FTE__c / SA_Budgeted_FTE__c / DE_Budgeted_FTE__c / DS_Budgeted_FTE__c
PM_Actual_FTE__c / SA_Actual_FTE__c / DE_Actual_FTE__c / DS_Actual_FTE__c
PM_FTE_Difference__c / SA_FTE_Difference__c / DE_FTE_Difference__c / DS_FTE_Difference__c
```

Health status fields:
```
Project_Status_Pick__c / Time_Status_Pick__c / Cost_Status_Pick__c / Resources_Status_Pick__c
```
