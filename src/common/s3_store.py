from __future__ import annotations

import json
from typing import Any

import boto3

from common.config import ARTIFACTS_BUCKET


_s3 = boto3.client("s3")


def put_json(key: str, payload: dict[str, Any]) -> str | None:
    if not ARTIFACTS_BUCKET:
        return None
    _s3.put_object(
        Bucket=ARTIFACTS_BUCKET,
        Key=key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{ARTIFACTS_BUCKET}/{key}"
