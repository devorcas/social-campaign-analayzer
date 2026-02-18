from __future__ import annotations

from typing import Any

from common.job_store import set_stage_output
from handlers._shared import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "prepare_media"
    job_id = require_job_id(event)
    try:
        artifacts = ensure_artifacts(event)
        prepared_media = {"audio_extracted": False, "frame_count": 0}
        artifacts.setdefault("prepared_media", prepared_media)
        set_stage_output(job_id=job_id, stage=stage, output=prepared_media)
        complete_stage(job_id, stage)
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
