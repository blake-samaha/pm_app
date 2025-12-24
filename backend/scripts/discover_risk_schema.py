# type: ignore
"""Comprehensive Salesforce schema discovery script.

This script performs an exhaustive but API-efficient discovery of the Salesforce
schema to find Risk-related objects and understand what's accessible via the API.

Run with: uv run python scripts/discover_risk_schema.py

The results are saved to docs/precursive_schema_discovery.json so this
discovery only needs to be run once.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Add parent directory to path to import from config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Settings

API_VERSION = "v59.0"


async def get_token(settings: Settings) -> dict:
    """Authenticate with Salesforce."""
    client_id = (
        settings.precursive_client_id.strip() if settings.precursive_client_id else ""
    )
    client_secret = (
        settings.precursive_client_secret.strip()
        if settings.precursive_client_secret
        else ""
    )
    instance_url = (
        settings.precursive_instance_url.strip()
        if settings.precursive_instance_url
        else ""
    )

    if not client_id or not client_secret:
        raise ValueError(
            "PRECURSIVE_CLIENT_ID and PRECURSIVE_CLIENT_SECRET must be set"
        )

    # Derive token URL from instance
    if "lightning.force.com" in instance_url:
        parts = instance_url.replace("https://", "").split(".")
        domain = parts[0] if parts else "login"
        token_url = f"https://{domain}.my.salesforce.com/services/oauth2/token"
    elif "my.salesforce.com" in instance_url:
        host = instance_url.replace("https://", "").split("/")[0]
        token_url = f"https://{host}/services/oauth2/token"
    else:
        token_url = "https://login.salesforce.com/services/oauth2/token"

    print(f"🔐 Authenticating with Salesforce at {token_url}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            print(response.text)
            raise ValueError("Authentication failed")
        return response.json()


async def query(client: httpx.AsyncClient, soql: str) -> list:
    """Execute a SOQL query."""
    response = await client.get(
        f"/services/data/{API_VERSION}/query",
        params={"q": soql},
    )
    if response.status_code != 200:
        return []
    return response.json().get("records", [])


async def tooling_query(client: httpx.AsyncClient, soql: str) -> list:
    """Execute a Tooling API query."""
    response = await client.get(
        f"/services/data/{API_VERSION}/tooling/query",
        params={"q": soql},
    )
    if response.status_code != 200:
        print(f"   Tooling query failed: {response.status_code}")
        return []
    return response.json().get("records", [])


async def describe_object(client: httpx.AsyncClient, sobject: str) -> dict | None:
    """Get object metadata/schema. Returns None if not accessible."""
    response = await client.get(
        f"/services/data/{API_VERSION}/sobjects/{sobject}/describe"
    )
    if response.status_code != 200:
        return None
    return response.json()


def extract_field_summary(fields: list) -> list:
    """Extract a summary of fields with important metadata."""
    summary = []
    for f in fields:
        field_info: dict[str, Any] = {
            "name": f["name"],
            "label": f["label"],
            "type": f["type"],
        }
        # Include reference info for lookups
        if f.get("referenceTo"):
            field_info["referenceTo"] = f["referenceTo"]
            field_info["relationshipName"] = f.get("relationshipName")
        # Include picklist values
        if f["type"] == "picklist" and f.get("picklistValues"):
            field_info["picklistValues"] = [
                {"value": pv["value"], "label": pv["label"]}
                for pv in f["picklistValues"]
                if pv.get("active", True)
            ]
        summary.append(field_info)
    return summary


async def comprehensive_discovery():
    """Perform comprehensive, API-efficient schema discovery."""
    settings = Settings()
    token_data = await get_token(settings)
    instance_url = token_data["instance_url"]
    access_token = token_data["access_token"]

    print(f"✅ Connected to {instance_url}")

    async with httpx.AsyncClient(
        base_url=instance_url,
        timeout=60.0,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    ) as client:
        results = {
            "discovery_timestamp": datetime.now().isoformat(),
            "instance_url": instance_url,
            "api_calls_made": 0,
            "discovery_complete": True,
            # Phase 1: High-level discovery
            "all_record_types": [],
            "risk_related_record_types": [],
            "risk_related_fields_found": [],
            # Phase 2: Object inventory
            "accessible_custom_objects": [],
            "precursive_objects": [],
            # Phase 3: Deep schema for key objects
            "project_schema": None,
            "phase_schema": None,
            "participant_schema": None,
            "resource_schema": None,
            # Phase 4: Relationship exploration
            "project_child_relationships": [],
            "sample_project_with_children": None,
            # Risk-specific findings
            "risk_schema": None,
            "risk_objects_found": [],
            "sample_risk": None,
            # Errors encountered
            "errors": [],
        }

        # =====================================================================
        # PHASE 1: High-Value Single Queries
        # =====================================================================

        print("\n" + "=" * 60)
        print("PHASE 1: High-Value Discovery Queries")
        print("=" * 60)

        # 1a. Query ALL Record Types (1 API call)
        print("\n📋 1a. Querying ALL Record Types...")
        try:
            all_record_types = await query(
                client,
                "SELECT Id, Name, DeveloperName, SobjectType, Description FROM RecordType ORDER BY SobjectType",
            )
            results["api_calls_made"] += 1
            results["all_record_types"] = [
                {
                    "sobject": rt.get("SobjectType"),
                    "name": rt.get("Name"),
                    "developerName": rt.get("DeveloperName"),
                    "description": rt.get("Description"),
                }
                for rt in all_record_types
            ]

            # Filter for risk-related
            risk_record_types = [
                rt
                for rt in results["all_record_types"]
                if rt["name"]
                and (
                    "risk" in rt["name"].lower()
                    or "risk" in (rt["developerName"] or "").lower()
                )
            ]
            results["risk_related_record_types"] = risk_record_types

            print(f"   Found {len(all_record_types)} total Record Types")
            print(f"   Risk-related: {len(risk_record_types)}")

            # Group by object for display
            objects_with_record_types = {}
            for rt in results["all_record_types"]:
                obj = rt["sobject"]
                if obj not in objects_with_record_types:
                    objects_with_record_types[obj] = []
                objects_with_record_types[obj].append(rt["name"])

            print("   Objects with Record Types:")
            for obj, types in sorted(objects_with_record_types.items()):
                print(f"      {obj}: {types}")

        except Exception as e:
            results["errors"].append(f"RecordType query failed: {str(e)}")
            print(f"   ❌ Error: {e}")

        # 1b. Use Tooling API to find fields with risk-related names (1 API call)
        print("\n📋 1b. Searching for risk-related fields via Tooling API...")
        try:
            # Search for custom fields with risk-related names
            field_query = """
                SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, Label, DataType
                FROM FieldDefinition 
                WHERE QualifiedApiName LIKE '%Risk%' 
                   OR QualifiedApiName LIKE '%Probability%'
                   OR QualifiedApiName LIKE '%Impact%'
                   OR QualifiedApiName LIKE '%Mitigation%'
                   OR Label LIKE '%Risk%'
                   OR Label LIKE '%Probability%'
                   OR Label LIKE '%Impact%'
                LIMIT 200
            """
            risk_fields = await tooling_query(client, field_query)
            results["api_calls_made"] += 1

            results["risk_related_fields_found"] = [
                {
                    "object": rf.get("EntityDefinition", {}).get("QualifiedApiName"),
                    "field": rf.get("QualifiedApiName"),
                    "label": rf.get("Label"),
                    "type": rf.get("DataType"),
                }
                for rf in risk_fields
            ]

            print(f"   Found {len(risk_fields)} fields with risk-related names:")

            # Group by object
            fields_by_object: dict[str, list] = {}
            for rf in results["risk_related_fields_found"]:
                obj = rf["object"]
                if obj not in fields_by_object:
                    fields_by_object[obj] = []
                fields_by_object[obj].append(f"{rf['field']} ({rf['label']})")

            for obj, fields in sorted(fields_by_object.items()):
                print(f"      🎯 {obj}:")
                for f in fields:
                    print(f"         - {f}")

        except Exception as e:
            results["errors"].append(f"Tooling API query failed: {str(e)}")
            print(f"   ❌ Error: {e}")

        # =====================================================================
        # PHASE 2: Object Inventory
        # =====================================================================

        print("\n" + "=" * 60)
        print("PHASE 2: Object Inventory")
        print("=" * 60)

        # 2a. List all accessible objects (1 API call)
        print("\n📋 2a. Listing all accessible objects...")
        try:
            response = await client.get(f"/services/data/{API_VERSION}/sobjects/")
            response.raise_for_status()
            results["api_calls_made"] += 1
            all_objects = response.json().get("sobjects", [])

            # Filter to custom objects
            custom_objects = [
                {
                    "name": obj["name"],
                    "label": obj["label"],
                    "keyPrefix": obj.get("keyPrefix"),
                    "queryable": obj.get("queryable", False),
                }
                for obj in all_objects
                if obj.get("custom")
                and obj["name"].endswith("__c")
                and "Share" not in obj["name"]
                and "Feed" not in obj["name"]
                and "History" not in obj["name"]
                and "ChangeEvent" not in obj["name"]
            ]

            results["accessible_custom_objects"] = custom_objects

            # Filter to Precursive objects
            precursive_objects = [
                obj for obj in custom_objects if obj["name"].startswith("preempt__")
            ]
            results["precursive_objects"] = precursive_objects

            print(f"   Total custom objects accessible: {len(custom_objects)}")
            print(f"   Precursive (preempt__) objects: {len(precursive_objects)}")

            for obj in precursive_objects:
                print(f"      - {obj['name']} ({obj['label']})")

        except Exception as e:
            results["errors"].append(f"Object listing failed: {str(e)}")
            print(f"   ❌ Error: {e}")

        # =====================================================================
        # PHASE 3: Deep Schema for Key Objects
        # =====================================================================

        print("\n" + "=" * 60)
        print("PHASE 3: Deep Schema for Precursive Objects")
        print("=" * 60)

        key_objects = [
            ("preempt__PrecursiveProject__c", "project_schema"),
            ("preempt__Phase__c", "phase_schema"),
            ("preempt__Participant__c", "participant_schema"),
            ("preempt__Resource__c", "resource_schema"),
        ]

        for obj_name, result_key in key_objects:
            print(f"\n📋 Describing {obj_name}...")
            try:
                schema = await describe_object(client, obj_name)
                results["api_calls_made"] += 1

                if schema:
                    # Get record types
                    record_types = [
                        {
                            "name": rt.get("name"),
                            "developerName": rt.get("developerName"),
                        }
                        for rt in schema.get("recordTypeInfos", [])
                    ]

                    # Get child relationships
                    child_rels = [
                        {
                            "childSObject": rel.get("childSObject"),
                            "relationshipName": rel.get("relationshipName"),
                            "field": rel.get("field"),
                        }
                        for rel in schema.get("childRelationships", [])
                        if rel.get("relationshipName")  # Only named relationships
                    ]

                    # Extract fields
                    fields = extract_field_summary(schema.get("fields", []))

                    results[result_key] = {
                        "object_name": obj_name,
                        "label": schema.get("label"),
                        "field_count": len(fields),
                        "record_types": record_types,
                        "child_relationships": child_rels,
                        "fields": fields,
                    }

                    print(
                        f"   ✅ {len(fields)} fields, {len(record_types)} record types, {len(child_rels)} child relationships"
                    )

                    # Look for risk-related fields in this object
                    risk_fields = [
                        f
                        for f in fields
                        if any(
                            kw in f["name"].lower() or kw in f["label"].lower()
                            for kw in [
                                "risk",
                                "probability",
                                "impact",
                                "mitigation",
                                "severity",
                            ]
                        )
                    ]
                    if risk_fields:
                        print(f"   🎯 Found {len(risk_fields)} risk-related fields:")
                        for f in risk_fields:
                            print(f"      - {f['name']} ({f['label']}) [{f['type']}]")

                    # Store child relationships for Project specifically
                    if result_key == "project_schema":
                        results["project_child_relationships"] = child_rels

                else:
                    print("   ❌ Not accessible")

            except Exception as e:
                results["errors"].append(f"Failed to describe {obj_name}: {str(e)}")
                print(f"   ❌ Error: {e}")

        # =====================================================================
        # PHASE 4: Explore Unknown Objects from Field Discovery
        # =====================================================================

        print("\n" + "=" * 60)
        print("PHASE 4: Explore Objects Found via Field Discovery")
        print("=" * 60)

        # Get unique objects that have risk-related fields
        objects_with_risk_fields = set(
            rf["object"]
            for rf in results.get("risk_related_fields_found", [])
            if rf["object"]
            and rf["object"]
            not in [
                "preempt__PrecursiveProject__c",
                "preempt__Phase__c",
                "preempt__Participant__c",
                "preempt__Resource__c",
            ]
        )

        print(
            f"\n📋 Found {len(objects_with_risk_fields)} additional objects with risk-related fields"
        )

        for obj_name in sorted(objects_with_risk_fields):
            print(f"\n   Attempting to describe {obj_name}...")
            try:
                schema = await describe_object(client, obj_name)
                results["api_calls_made"] += 1

                if schema:
                    print(f"   ✅ Accessible! Label: {schema.get('label')}")

                    # Check if this might be the Risk object
                    label = schema.get("label", "").lower()
                    if "risk" in label or "risk" in obj_name.lower():
                        print("   🎯 POTENTIAL RISK OBJECT FOUND!")

                        # Store full schema
                        fields = extract_field_summary(schema.get("fields", []))
                        record_types = [
                            {
                                "name": rt.get("name"),
                                "developerName": rt.get("developerName"),
                            }
                            for rt in schema.get("recordTypeInfos", [])
                        ]

                        results["risk_schema"] = {
                            "object_name": obj_name,
                            "label": schema.get("label"),
                            "field_count": len(fields),
                            "record_types": record_types,
                            "fields": fields,
                        }

                        results["risk_objects_found"].append(
                            {
                                "name": obj_name,
                                "label": schema.get("label"),
                                "source": "field_discovery",
                            }
                        )

                        # Find project relationship
                        for f in schema.get("fields", []):
                            if "preempt__PrecursiveProject__c" in f.get(
                                "referenceTo", []
                            ):
                                print(f"   ✅ Project relationship field: {f['name']}")

                else:
                    print("   ❌ Not accessible via API")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        # =====================================================================
        # PHASE 5: Try to find risks via SOQL sub-queries
        # =====================================================================

        print("\n" + "=" * 60)
        print("PHASE 5: SOQL Sub-query Exploration")
        print("=" * 60)

        print("\n📋 Querying a sample project with child relationships...")
        try:
            # Get a project with its phases
            sample_query = """
                SELECT Id, Name, 
                       (SELECT Id, Name FROM preempt__Phases__r LIMIT 5)
                FROM preempt__PrecursiveProject__c 
                WHERE Name != 'Admin'
                LIMIT 1
            """
            samples = await query(client, sample_query)
            results["api_calls_made"] += 1

            if samples:
                sample = samples[0]
                phases = sample.get("preempt__Phases__r", {})
                phase_records = phases.get("records", []) if phases else []

                results["sample_project_with_children"] = {
                    "project_id": sample.get("Id"),
                    "project_name": sample.get("Name"),
                    "phase_count": len(phase_records),
                    "phases": [
                        {"id": p.get("Id"), "name": p.get("Name")}
                        for p in phase_records
                    ],
                }

                print(f"   Project: {sample.get('Name')} ({sample.get('Id')})")
                print(f"   Phases found: {len(phase_records)}")

                # If we have phases, let's query one to see its Record Type
                if phase_records:
                    phase_id = phase_records[0].get("Id")
                    phase_detail = await query(
                        client,
                        f"SELECT Id, Name, RecordType.Name, RecordType.DeveloperName FROM preempt__Phase__c WHERE Id = '{phase_id}'",
                    )
                    results["api_calls_made"] += 1

                    if phase_detail:
                        rt = phase_detail[0].get("RecordType", {})
                        print(
                            f"   Sample Phase RecordType: {rt.get('Name')} ({rt.get('DeveloperName')})"
                        )

        except Exception as e:
            results["errors"].append(f"Sub-query exploration failed: {str(e)}")
            print(f"   ❌ Error: {e}")

        # =====================================================================
        # Save Results
        # =====================================================================

        output_path = (
            Path(__file__).parent.parent.parent
            / "docs"
            / "precursive_schema_discovery.json"
        )

        # Pretty print the JSON
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\n" + "=" * 60)
        print("DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"\n💾 Results saved to {output_path}")
        print("\n📊 Summary:")
        print(f"   API calls made: {results['api_calls_made']}")
        print(f"   Total Record Types: {len(results['all_record_types'])}")
        print(
            f"   Risk-related Record Types: {len(results['risk_related_record_types'])}"
        )
        print(
            f"   Risk-related fields found: {len(results['risk_related_fields_found'])}"
        )
        print(
            f"   Accessible custom objects: {len(results['accessible_custom_objects'])}"
        )
        print(f"   Precursive objects: {len(results['precursive_objects'])}")
        print(f"   Risk objects found: {len(results['risk_objects_found'])}")

        if results["errors"]:
            print(f"\n⚠️  Errors encountered: {len(results['errors'])}")
            for err in results["errors"]:
                print(f"   - {err}")

        if results["risk_schema"]:
            print("\n🎉 SUCCESS: Risk schema discovered!")
            print(f"   Object: {results['risk_schema']['object_name']}")
            print(f"   Label: {results['risk_schema']['label']}")
            print(f"   Fields: {results['risk_schema']['field_count']}")
        elif results["risk_related_fields_found"]:
            print("\n⚠️  Risk-related FIELDS found but Risk OBJECT not accessible")
            print("   The API user may not have permissions to the Risk object.")
        else:
            print("\n⚠️  No risk-related data found in accessible schema")
            print("   Consider requesting Salesforce admin access.")

        return results


if __name__ == "__main__":
    asyncio.run(comprehensive_discovery())
