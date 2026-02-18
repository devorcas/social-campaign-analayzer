from __future__ import annotations

"""Media preparation stage Lambda.

Business logic:
- Prepares media-processing metadata (audio extraction/frame sampling placeholders).
- Persists compact stage metadata for observability.
"""

from typing import Any

from shared.job_store import set_stage_output
from shared.workflow_utils import complete_stage, ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Run media preparation and attach preparation metadata to the event."""
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
