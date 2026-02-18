from __future__ import annotations

from typing import Any

from shared.job_store import safe_set_failed, set_stage_status


def require_job_id(event: dict[str, Any]) -> str:
    job_id = event.get("job_id")
    if not job_id:
        raise ValueError("job_id is required")
    return str(job_id)


def complete_stage(job_id: str, stage: str) -> None:
    set_stage_status(job_id, stage, "completed")


def fail_stage(job_id: str, stage: str, exc: Exception) -> None:
    safe_set_failed(job_id=job_id, stage=stage, exc=exc)


def ensure_artifacts(event: dict[str, Any]) -> dict[str, Any]:
    artifacts = event.get("artifacts")
    if not isinstance(artifacts, dict):
        artifacts = {}
        event["artifacts"] = artifacts
    return artifacts
