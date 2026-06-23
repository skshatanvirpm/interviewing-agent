from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from interviewing_agent.config import Settings
from interviewing_agent.services.persistence import SupabasePersistenceService


class FakeSupabasePersistence(SupabasePersistenceService):
    def __init__(self) -> None:
        super().__init__(
            Settings(
                supabase_url="https://example.supabase.co",
                supabase_publishable_key="publishable",
                supabase_service_role_key="service-role",
                _env_file=None,
            )
        )
        self.tables: dict[str, list[dict[str, Any]]] = {
            "interviews": [
                {
                    "id": "session-1",
                    "candidate_id": "candidate-1",
                    "resume_id": "resume-1",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "resumes": [
                {
                    "id": "resume-1",
                    "candidate_id": "candidate-1",
                    "storage_path": "candidate-1/resume-1.pdf",
                }
            ],
        }
        self.deletes: list[tuple[str, dict[str, str]]] = []
        self.deleted_objects: list[str] = []

    def _select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        rows = list(self.tables.get(table, []))
        if "id" in params and params["id"].startswith("eq."):
            expected = params["id"].removeprefix("eq.")
            rows = [row for row in rows if row.get("id") == expected]
        if "candidate_id" in params and params["candidate_id"].startswith("eq."):
            expected = params["candidate_id"].removeprefix("eq.")
            rows = [row for row in rows if row.get("candidate_id") == expected]
        if "created_at" in params and params["created_at"].startswith("lt."):
            cutoff = datetime.fromisoformat(params["created_at"].removeprefix("lt."))
            rows = [
                row
                for row in rows
                if datetime.fromisoformat(row["created_at"]) < cutoff
            ]
        return rows

    def _delete(self, table: str, params: dict[str, str]) -> None:
        self.deletes.append((table, params))
        if "id" in params and params["id"].startswith("eq."):
            expected = params["id"].removeprefix("eq.")
            self.tables[table] = [
                row for row in self.tables.get(table, []) if row.get("id") != expected
            ]

    def _delete_resume_object(self, storage_path: str) -> None:
        self.deleted_objects.append(storage_path)


def test_delete_session_data_removes_candidate_data_and_private_resume_object() -> None:
    persistence = FakeSupabasePersistence()

    deleted = persistence.delete_session_data("session-1")

    assert deleted is True
    assert persistence.deleted_objects == ["candidate-1/resume-1.pdf"]
    assert ("candidates", {"id": "eq.candidate-1"}) in persistence.deletes


def test_delete_expired_interview_data_removes_only_expired_sessions() -> None:
    persistence = FakeSupabasePersistence()
    persistence.tables["interviews"].extend(
        [
            {
                "id": "old-session",
                "candidate_id": "candidate-old",
                "resume_id": "resume-old",
                "created_at": (
                    datetime.now(timezone.utc) - timedelta(days=45)
                ).isoformat(),
            },
            {
                "id": "fresh-session",
                "candidate_id": "candidate-fresh",
                "resume_id": "resume-fresh",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
    )

    deleted_count = persistence.delete_expired_interview_data(retention_days=30)

    assert deleted_count == 1
    assert ("candidates", {"id": "eq.candidate-old"}) in persistence.deletes
    assert ("candidates", {"id": "eq.candidate-fresh"}) not in persistence.deletes


def test_retention_keeps_candidate_data_when_a_fresh_session_remains() -> None:
    persistence = FakeSupabasePersistence()
    persistence.tables["interviews"] = [
        {
            "id": "old-session",
            "candidate_id": "candidate-shared",
            "resume_id": "resume-shared",
            "created_at": (
                datetime.now(timezone.utc) - timedelta(days=45)
            ).isoformat(),
        },
        {
            "id": "fresh-session",
            "candidate_id": "candidate-shared",
            "resume_id": "resume-shared",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    deleted_count = persistence.delete_expired_interview_data(retention_days=30)

    assert deleted_count == 1
    assert ("interviews", {"id": "eq.old-session"}) in persistence.deletes
    assert ("candidates", {"id": "eq.candidate-shared"}) not in persistence.deletes
