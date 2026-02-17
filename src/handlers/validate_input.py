from __future__ import annotations

from typing import Any

from handlers._shared import complete_stage, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "validate_input"
    job_id = require_job_id(event)
    try:
        if not event.get("campaign_id"):
            raise ValueError("campaign_id is required")
        source = event.get("source") or {}
        if not source.get("reference_id"):
            raise ValueError("source.reference_id is required")
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
