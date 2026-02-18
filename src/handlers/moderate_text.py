from __future__ import annotations

from typing import Any

from common.job_store import set_artifact_uri, set_stage_output
from common.s3_store import put_json
from handlers._shared import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "moderate_text"
    job_id = require_job_id(event)
    try:
        text_result = {
            "overall_score": 100.0,
            "categories": [],
        }
        uri = put_json(f"jobs/{job_id}/text_moderation.json", text_result)
        artifacts = ensure_artifacts(event)
        artifacts["text_s3_uri"] = uri
        event["text_moderation"] = text_result
        set_artifact_uri(job_id, "text_s3_uri", uri)
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={
                "text_s3_uri": uri,
                "overall_score": text_result["overall_score"],
                "category_count": len(text_result["categories"]),
            },
        )
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
