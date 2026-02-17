from __future__ import annotations

from typing import Any

from handlers._shared import complete_stage, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "aggregate_scores"
    job_id = require_job_id(event)
    try:
        visual = event.get("visual_moderation") or {"overall_score": 100.0, "categories": []}
        text = event.get("text_moderation") or {"overall_score": 100.0, "categories": []}
        event["analysis"] = {
            "visual": visual,
            "text": text,
        }
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
