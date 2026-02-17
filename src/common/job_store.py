from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.config import ANALYSIS_TABLE_NAME


_dynamodb = boto3.resource("dynamodb")
_table = _dynamodb.Table(ANALYSIS_TABLE_NAME)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_ttl(days: int = 30) -> int:
    return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())


def create_job(job_id: str, campaign_id: str, source: dict[str, Any]) -> dict[str, Any]:
    item = {
        "job_id": job_id,
        "campaign_id": campaign_id,
        "source_type": source.get("type", "amplify"),
        "source_ref": source.get("reference_id"),
        "status": "queued",
        "progress": {
            "validate_input": "pending",
            "ingest_content": "pending",
            "prepare_media": "pending",
            "transcribe_audio": "pending",
            "moderate_text": "pending",
            "moderate_visual": "pending",
            "aggregate_scores": "pending",
            "generate_summary_and_persist": "pending",
        },
        "artifacts": {
            "ingestion_s3_uri": None,
            "transcript_s3_uri": None,
            "visual_s3_uri": None,
            "text_s3_uri": None,
            "final_s3_uri": None,
        },
        "result": None,
        "error": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "expires_at": default_ttl(),
    }
    _table.put_item(Item=item, ConditionExpression="attribute_not_exists(job_id)")
    return item


def get_job(job_id: str) -> dict[str, Any] | None:
    response = _table.get_item(Key={"job_id": job_id})
    return response.get("Item")


def set_job_status(job_id: str, status: str, error: dict[str, Any] | None = None) -> None:
    _table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #status=:status, #error=:error, #updated_at=:updated_at",
        ExpressionAttributeNames={"#status": "status", "#error": "error", "#updated_at": "updated_at"},
        ExpressionAttributeValues={
            ":status": status,
            ":error": error,
            ":updated_at": now_iso(),
        },
    )


def set_stage_status(job_id: str, stage: str, status: str) -> None:
    _table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #updated_at=:updated_at, #progress.#stage=:stage_status",
        ExpressionAttributeNames={"#updated_at": "updated_at", "#progress": "progress", "#stage": stage},
        ExpressionAttributeValues={":updated_at": now_iso(), ":stage_status": status},
    )


def set_artifact_uri(job_id: str, key: str, value: str | None) -> None:
    _table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #updated_at=:updated_at, #artifacts.#key=:value",
        ExpressionAttributeNames={"#updated_at": "updated_at", "#artifacts": "artifacts", "#key": key},
        ExpressionAttributeValues={":updated_at": now_iso(), ":value": value},
    )


def persist_final_result(job_id: str, result: dict[str, Any], final_s3_uri: str | None = None) -> None:
    expr = "SET #status=:status, #result=:result, #updated_at=:updated_at, #progress.#summary=:summary_status"
    names = {
        "#status": "status",
        "#result": "result",
        "#updated_at": "updated_at",
        "#progress": "progress",
        "#summary": "generate_summary_and_persist",
    }
    values: dict[str, Any] = {
        ":status": "completed",
        ":result": result,
        ":updated_at": now_iso(),
        ":summary_status": "completed",
    }
    if final_s3_uri is not None:
        expr += ", #artifacts.#final_key=:final_value"
        names["#artifacts"] = "artifacts"
        names["#final_key"] = "final_s3_uri"
        values[":final_value"] = final_s3_uri

    _table.update_item(
        Key={"job_id": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def safe_set_failed(job_id: str, stage: str, exc: Exception) -> None:
    try:
        set_job_status(
            job_id=job_id,
            status="failed",
            error={"stage": stage, "code": "UNHANDLED_EXCEPTION", "message": str(exc)},
        )
    except ClientError:
        # Best effort error update.
        return
