from __future__ import annotations

"""Ingestion stage Lambda.

Business logic:
- Builds normalized campaign content payload from source reference.
- Stores ingestion artifact in S3.
- Updates DynamoDB with progress, artifact URI, and stage metadata.
"""

from typing import Any

from shared.job_store import set_artifact_uri, set_job_status, set_stage_output
from shared.s3_store import put_json
from shared.workflow_utils import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run ingestion stage and enrich workflow event with ingestion artifact refs."""
    stage = "ingest_content"
    job_id = require_job_id(event)
    try:
        set_job_status(job_id=job_id, status="running", error=None)
        source = event.get("source", {})
        content = {
            "campaign_id": event.get("campaign_id"),
            "source_type": source.get("type", "amplify"),
            "source_ref": source.get("reference_id"),
            "posts": [],
        }
        uri = put_json(f"jobs/{job_id}/ingestion.json", content)
        artifacts = ensure_artifacts(event)
        artifacts["ingestion_s3_uri"] = uri
        set_artifact_uri(job_id, "ingestion_s3_uri", uri)
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={
                "ingestion_s3_uri": uri,
                "source_type": content["source_type"],
                "post_count": len(content["posts"]),
            },
        )
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
