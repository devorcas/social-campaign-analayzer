from __future__ import annotations

"""Visual moderation stage Lambda.

Business logic:
- Produces visual safety moderation output (blueprint placeholder in current scaffold).
- Stores moderation artifact in S3.
- Updates DynamoDB with visual moderation metadata for job tracking.
"""

from typing import Any

from shared.job_store import set_artifact_uri, set_stage_output
from shared.s3_store import put_json
from shared.workflow_utils import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run visual moderation stage and pass normalized moderation output forward."""
    stage = "moderate_visual"
    job_id = require_job_id(event)
    try:
        visual_result = {
            "overall_score": 100.0,
            "categories": [],
        }
        uri = put_json(f"jobs/{job_id}/visual_moderation.json", visual_result)
        artifacts = ensure_artifacts(event)
        artifacts["visual_s3_uri"] = uri
        event["visual_moderation"] = visual_result
        set_artifact_uri(job_id, "visual_s3_uri", uri)
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={
                "visual_s3_uri": uri,
                "overall_score": visual_result["overall_score"],
                "category_count": len(visual_result["categories"]),
            },
        )
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
