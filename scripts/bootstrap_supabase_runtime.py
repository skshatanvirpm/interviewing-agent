from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve Supabase runtime keys from a PAT and optionally apply schema.",
    )
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--access-token", default=os.environ.get("SUPABASE_ACCESS_KEY"))
    parser.add_argument("--schema-file", default="supabase/schema.sql")
    parser.add_argument("--apply-schema", action="store_true")
    return parser.parse_args()


def fetch_api_keys(project_ref: str, access_token: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": access_token,
        "User-Agent": "codex-bootstrap",
    }
    request = Request(
        f"https://api.supabase.com/v1/projects/{project_ref}/api-keys?{urlencode({'reveal': 'true'})}",
        headers=headers,
    )
    with urlopen(request, timeout=30) as response:
        keys = json.load(response)

    publishable = next(
        (
            item["api_key"]
            for item in keys
            if item.get("name") == "default" and str(item.get("api_key", "")).startswith("sb_publishable_")
        ),
        None,
    )
    service_role = next(
        (
            item["api_key"]
            for item in keys
            if item.get("name") == "service_role"
        ),
        None,
    )

    if not publishable or not service_role:
        raise RuntimeError("Could not resolve publishable and service_role keys for the project.")

    return {
        "SUPABASE_URL": f"https://{project_ref}.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": publishable,
        "SUPABASE_SERVICE_ROLE_KEY": service_role,
    }


def apply_schema(project_ref: str, access_token: str, schema_file: Path) -> None:
    query = schema_file.read_text(encoding="utf-8")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": access_token,
        "Content-Type": "application/json",
        "User-Agent": "codex-bootstrap",
    }
    payload = json.dumps({"query": query}).encode("utf-8")
    request = Request(
        f"https://api.supabase.com/v1/projects/{project_ref}/database/query",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=60):
            return
    except HTTPError as exc:  # pragma: no cover - script-only error path
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(detail) from exc


def main() -> None:
    args = parse_args()
    if not args.access_token:
        raise SystemExit("SUPABASE_ACCESS_KEY is required.")

    runtime = fetch_api_keys(args.project_ref, args.access_token)
    print(json.dumps(runtime, ensure_ascii=True))
    if args.apply_schema:
        apply_schema(args.project_ref, args.access_token, Path(args.schema_file))


if __name__ == "__main__":
    main()
