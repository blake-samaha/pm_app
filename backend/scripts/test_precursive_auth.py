"""
Temporary helper script to debug Precursive/Salesforce authentication.

Usage:
    uv run python scripts/test_precursive_auth.py

Notes:
    - Does not print secrets, only whether they are present and response bodies from Salesforce.
    - Attempts client credentials first (if configured), then username/password+token if available.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict

import httpx

from config import get_settings
from integrations.precursive_client import PrecursiveClient


LOGIN_URL = "https://login.salesforce.com/services/oauth2/token"


def _mask(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 4:
        return "****"
    return value[:2] + "***" + value[-2:]


async def try_client_credentials(settings) -> Dict[str, Any]:
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.precursive_client_id,
        "client_secret": settings.precursive_client_secret,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(LOGIN_URL, data=payload)
        return {
            "status": resp.status_code,
            "body": resp.text,
        }


async def try_password_flow(settings) -> Dict[str, Any]:
    payload = {
        "grant_type": "password",
        "client_id": settings.precursive_client_id,
        "client_secret": settings.precursive_client_secret,
        "username": settings.precursive_username,
        "password": f"{settings.precursive_password}{settings.precursive_security_token}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(LOGIN_URL, data=payload)
        return {
            "status": resp.status_code,
            "body": resp.text,
        }


async def main():
    settings = get_settings()

    print("=== Precursive/Salesforce auth debug ===")
    print(f"Instance URL: {settings.precursive_instance_url or '<missing>'}")
    print(f"Client ID: {_mask(settings.precursive_client_id)}")
    print(f"Client Secret: {_mask(settings.precursive_client_secret)}")
    print(f"Username: {_mask(settings.precursive_username)}")
    print(f"Password set: {bool(settings.precursive_password)}")
    print(f"Security token set: {bool(settings.precursive_security_token)}")
    print("")

    client = PrecursiveClient(settings)

    # First, try using the real client helper (will respect configured flow)
    try:
        result = await client.test_connection()
        print("test_connection succeeded:", result)
        await client.close()
        return
    except Exception as e:
        print("test_connection failed:", str(e))

    # Direct probes to the token endpoint for clearer error bodies
    if settings.precursive_client_id and settings.precursive_client_secret:
        print("\n-- Client credentials probe --")
        cc_result = await try_client_credentials(settings)
        print("status:", cc_result["status"])
        print("body:", cc_result["body"])

    if (
        settings.precursive_client_id
        and settings.precursive_client_secret
        and settings.precursive_username
        and settings.precursive_password
        and settings.precursive_security_token
    ):
        print("\n-- Password flow probe --")
        pw_result = await try_password_flow(settings)
        print("status:", pw_result["status"])
        print("body:", pw_result["body"])

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())




