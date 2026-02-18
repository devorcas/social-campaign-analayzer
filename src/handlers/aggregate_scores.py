from __future__ import annotations

from typing import Any

from common.job_store import set_artifact_uri, set_stage_output
from common.s3_store import put_json
from handlers._shared import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "aggregate_scores"
    job_id = require_job_id(event)
    try:
        visual = event.get("visual_moderation") or {"overall_score": 100.0, "categories": []}
        text = event.get("text_moderation") or {"overall_score": 100.0, "categories": []}
        analysis = {
            "visual": visual,
            "text": text,
        }
        event["analysis"] = analysis
        uri = put_json(f"jobs/{job_id}/aggregate_scores.json", analysis)
        artifacts = ensure_artifacts(event)
        artifacts["aggregate_s3_uri"] = uri
        set_artifact_uri(job_id, "aggregate_s3_uri", uri)
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={
                "aggregate_s3_uri": uri,
                "visual_overall_score": visual.get("overall_score"),
                "text_overall_score": text.get("overall_score"),
            },
        )
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
