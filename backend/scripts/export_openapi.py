#!/usr/bin/env python3
"""
Export OpenAPI schema from FastAPI app.

This script imports the FastAPI application and exports its OpenAPI schema
to a JSON file. It sets safe defaults for required configuration so it can
run without a real database connection.

Usage:
    uv run python scripts/export_openapi.py
    uv run python scripts/export_openapi.py --output ../frontend/openapi.json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def set_dummy_env_vars():
    """
    Set dummy environment variables for required config.

    This allows importing the app without real credentials.
    The values are never used since we only extract the schema.
    """
    defaults = {
        "DATABASE_URL": "postgresql://dummy:dummy@localhost:5432/dummy",
        "SECRET_KEY": "dummy-secret-key-for-openapi-export",
        "FIREBASE_PROJECT_ID": "dummy-project",
    }
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value


def main():
    parser = argparse.ArgumentParser(
        description="Export OpenAPI schema from FastAPI app"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../frontend/openapi.json",
        help="Output file path (default: ../frontend/openapi.json)",
    )
    args = parser.parse_args()

    # Set dummy env vars before importing the app
    set_dummy_env_vars()

    # Add backend to path so imports work
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))

    # Import the app (this will trigger lifespan events but we don't run the server)
    # We need to import FastAPI app module directly
    from fastapi.openapi.utils import get_openapi

    # Import the app - this just creates the app object without running lifespan
    from main import app

    # Generate the OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Resolve output path relative to current working directory
    output_path = Path(args.output).resolve()

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the schema
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI schema exported to: {output_path}")
    print(f"  - {len(openapi_schema.get('paths', {}))} paths")
    print(f"  - {len(openapi_schema.get('components', {}).get('schemas', {}))} schemas")


if __name__ == "__main__":
    main()
