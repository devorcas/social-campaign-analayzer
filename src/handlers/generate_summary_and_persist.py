from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from common.job_store import persist_final_result
from common.s3_store import put_json
from common.summary_client import generate_summary
from handlers._shared import ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    stage = "generate_summary_and_persist"
    job_id = require_job_id(event)
    try:
        analysis = event.get("analysis") or {"visual": {"overall_score": 100.0}, "text": {"overall_score": 100.0}}
        transcript_text = event.get("transcript_text")

        summary = generate_summary(analysis=analysis, transcript_text=transcript_text)
        result = {
            "job_id": job_id,
            "campaign_id": event.get("campaign_id"),
            "visual": analysis.get("visual"),
            "text": analysis.get("text"),
            "human_summary": summary,
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }

        final_uri = put_json(f"jobs/{job_id}/final_result.json", result)
        ensure_artifacts(event)["final_s3_uri"] = final_uri

        persist_final_result(job_id=job_id, result=result, final_s3_uri=final_uri)
        event["result"] = result
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
