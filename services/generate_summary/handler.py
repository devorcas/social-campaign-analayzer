from __future__ import annotations

"""Summary stage Lambda (implemented end-to-end).

Business logic:
- Generates human-readable summary from aggregated analysis (+ transcript context).
- Calls Claude API when configured, otherwise uses a deterministic fallback summary.
- Stores final result artifact in S3.
- Persists final job result and terminal completed status in DynamoDB.
"""

from datetime import datetime, timezone
from typing import Any

from shared.job_store import persist_final_result, set_stage_output
from shared.s3_store import put_json
from summary_client import generate_summary
from shared.workflow_utils import ensure_artifacts, fail_stage, require_job_id


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Generate summary and persist final analysis result."""
    stage = "generate_summary"
    job_id = require_job_id(event)
    try:
        analysis = event.get("analysis") or {"visual": {"overall_score": 100.0}, "text": {"overall_score": 100.0}}
        transcript_text = event.get("transcript_text")

        summary = generate_summary(analysis=analysis, transcript_text=transcript_text)
        result = {
            "job_id": job_id,
            "campaign_id": event.get("campaign_id"),
            "overall_visual_safety_score": analysis.get("visual", {}).get("overall_score"),
            "overall_text_safety_score": analysis.get("text", {}).get("overall_score"),
            "visual": analysis.get("visual"),
            "text": analysis.get("text"),
            "human_summary": summary,
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }

        final_uri = put_json(f"jobs/{job_id}/final_result.json", result)
        ensure_artifacts(event)["final_s3_uri"] = final_uri

        persist_final_result(job_id=job_id, result=result, final_s3_uri=final_uri)
        set_stage_output(
            job_id=job_id,
            stage=stage,
            output={
                "final_s3_uri": final_uri,
                "summary_chars": len(summary),
                "status": "completed",
            },
        )
        event["result"] = result
        return event
    except Exception as exc:
        fail_stage(job_id, stage, exc)
        raise
