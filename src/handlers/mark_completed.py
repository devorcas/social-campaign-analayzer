from __future__ import annotations

from typing import Any

from common.job_store import set_job_status
from handlers._shared import require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    job_id = require_job_id(event)
    # Final status is normally set in generate_summary_and_persist. This is a defensive idempotent update.
    set_job_status(job_id=job_id, status="completed", error=None)
    return event
