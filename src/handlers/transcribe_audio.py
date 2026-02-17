from __future__ import annotations

from typing import Any

from common.job_store import set_artifact_uri
from common.s3_store import put_json
from handlers._shared import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "transcribe_audio"
    job_id = require_job_id(event)
    try:
        transcript = {"segments": [], "full_text": ""}
        uri = put_json(f"jobs/{job_id}/transcript.json", transcript)
        artifacts = ensure_artifacts(event)
        artifacts["transcript_s3_uri"] = uri
        event["transcript_text"] = transcript["full_text"]
        set_artifact_uri(job_id, "transcript_s3_uri", uri)
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
