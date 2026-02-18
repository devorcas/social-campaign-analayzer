from __future__ import annotations

"""Audio transcription stage Lambda.

Business logic:
- Produces transcript artifact (blueprint placeholder in current scaffold).
- Stores transcript JSON in S3.
- Updates DynamoDB with transcript artifact URI and transcript metadata.
"""

from typing import Any

from shared.job_store import set_artifact_uri, set_stage_output
from shared.s3_store import put_json
from shared.workflow_utils import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run transcription stage and expose transcript refs/text to downstream steps."""
    stage = "transcribe_audio"
    job_id = require_job_id(event)
    try:
        transcript = {"segments": [], "full_text": ""}
        uri = put_json(f"jobs/{job_id}/transcript.json", transcript)
        artifacts = ensure_artifacts(event)
        artifacts["transcript_s3_uri"] = uri
        event["transcript_text"] = transcript["full_text"]
        set_artifact_uri(job_id, "transcript_s3_uri", uri)
        has_text = bool(transcript["full_text"].strip())
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={"transcript_s3_uri": uri, "segment_count": len(transcript["segments"]), "has_text": has_text},
        )
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
