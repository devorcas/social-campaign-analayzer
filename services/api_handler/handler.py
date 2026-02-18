from __future__ import annotations

"""API Lambda for analysis job lifecycle.

Business logic:
- POST creates a new job record and starts the Step Functions workflow.
- GET returns the current job snapshot from DynamoDB for polling clients.
"""

import json
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError

from shared.config import STATE_MACHINE_ARN
from shared.http import json_response, parse_body
from shared.job_store import create_job, get_job, set_job_status


_sfn = boto3.client("stepfunctions")


def _handle_post(event: dict[str, Any]) -> dict[str, Any]:
    """Create analysis job and trigger orchestration."""
    body = parse_body(event)
    campaign_id = body.get("campaign_id")
    source = body.get("source", {})

    if not campaign_id or not source.get("reference_id"):
        return json_response(400, {"error": "campaign_id and source.reference_id are required"})
    if not STATE_MACHINE_ARN:
        return json_response(500, {"error": "STATE_MACHINE_ARN is not configured"})

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    try:
        create_job(job_id=job_id, campaign_id=campaign_id, source=source)
    except ClientError as exc:
        return json_response(500, {"error": "failed to create job", "details": str(exc)})

    sfn_input: dict[str, Any] = {
        "job_id": job_id,
        "campaign_id": campaign_id,
        "source": source,
        "artifacts": {},
    }
    try:
        _sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=job_id,
            input=json.dumps(sfn_input),
        )
    except ClientError as exc:
        set_job_status(job_id=job_id, status="failed", error={"stage": "start_execution", "message": str(exc)})
        return json_response(500, {"error": "failed to start workflow", "job_id": job_id})

    return json_response(
        202,
        {
            "job_id": job_id,
            "status": "queued",
            "status_url": f"/v1/analysis-jobs/{job_id}",
        },
    )


def _handle_get(event: dict[str, Any]) -> dict[str, Any]:
    """Return a single analysis job by job_id."""
    path = event.get("pathParameters") or {}
    job_id = path.get("job_id")
    if not job_id:
        return json_response(400, {"error": "job_id is required"})

    item = get_job(job_id)
    if not item:
        return json_response(404, {"error": "job not found", "job_id": job_id})
    return json_response(200, item)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Route API Gateway HTTP method to POST/GET handlers."""
    method = event.get("httpMethod")
    if method == "POST":
        return _handle_post(event)
    if method == "GET":
        return _handle_get(event)
    return json_response(405, {"error": "method not allowed"})
