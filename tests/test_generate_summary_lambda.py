from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIR = REPO_ROOT / "services" / "generate_summary"


def _install_fake_aws_modules() -> None:
    fake_boto3 = types.ModuleType("boto3")

    class _FakeTable:
        def put_item(self, **kwargs):
            return {}

        def get_item(self, **kwargs):
            return {}

        def update_item(self, **kwargs):
            return {}

    class _FakeDynamoResource:
        def Table(self, name):
            return _FakeTable()

    class _FakeS3Client:
        def put_object(self, **kwargs):
            return {}

    def _resource(name):
        if name == "dynamodb":
            return _FakeDynamoResource()
        raise ValueError(name)

    def _client(name):
        if name == "s3":
            return _FakeS3Client()
        raise ValueError(name)

    fake_boto3.resource = _resource
    fake_boto3.client = _client
    sys.modules["boto3"] = fake_boto3

    fake_botocore_exceptions = types.ModuleType("botocore.exceptions")

    class ClientError(Exception):
        pass

    fake_botocore_exceptions.ClientError = ClientError
    sys.modules["botocore.exceptions"] = fake_botocore_exceptions


@pytest.fixture
def summary_handler_module():
    _install_fake_aws_modules()
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(SERVICE_DIR))
    spec = importlib.util.spec_from_file_location("generate_summary_handler", SERVICE_DIR / "handler.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    yield module

    if str(REPO_ROOT) in sys.path:
        sys.path.remove(str(REPO_ROOT))
    if str(SERVICE_DIR) in sys.path:
        sys.path.remove(str(SERVICE_DIR))


def test_generate_summary_persists_final_result_with_mocked_s3(summary_handler_module, monkeypatch):
    event = {
        "job_id": "job_123",
        "campaign_id": "cmp_123",
        "analysis": {
            "visual": {
                "overall_score": 92.4,
                "categories": [
                    {"name": "adult_content", "score": 96.0, "status": "Safe"},
                    {"name": "spoof_fake_content", "score": 84.0, "status": "Warning"},
                ],
            },
            "text": {
                "overall_score": 86.3,
                "categories": [
                    {"name": "misinformation", "score": 80.0, "status": "Warning"},
                    {"name": "hate_speech", "score": 93.0, "status": "Safe"},
                ],
            },
        },
        "transcript_text": "Sponsored skincare review with a safety warning.",
        "artifacts": {},
    }

    fake_s3 = {}
    calls = {"persist": 0, "stage_output": 0}

    def fake_put_json(key, payload):
        fake_s3[key] = payload
        return f"s3://test-bucket/{key}"

    def fake_persist_final_result(*args, **kwargs):
        calls["persist"] += 1

    def fake_set_stage_output(*args, **kwargs):
        calls["stage_output"] += 1

    monkeypatch.setattr(summary_handler_module, "put_json", fake_put_json)
    monkeypatch.setattr(summary_handler_module, "persist_final_result", fake_persist_final_result)
    monkeypatch.setattr(summary_handler_module, "set_stage_output", fake_set_stage_output)
    monkeypatch.setattr(
        summary_handler_module,
        "generate_summary",
        lambda **kwargs: "Content is mostly safe with warning for spoof/fake and misinformation.",
    )

    out = summary_handler_module.lambda_handler(event, None)

    assert "result" in out
    result = out["result"]
    assert result["job_id"] == "job_123"
    assert result["campaign_id"] == "cmp_123"
    assert result["overall_visual_safety_score"] == 92.4
    assert result["overall_text_safety_score"] == 86.3
    assert "human_summary" in result
    assert out["artifacts"]["final_s3_uri"] == "s3://test-bucket/jobs/job_123/final_result.json"

    assert "jobs/job_123/final_result.json" in fake_s3
    assert fake_s3["jobs/job_123/final_result.json"]["human_summary"] == result["human_summary"]
    assert calls["persist"] == 1
    assert calls["stage_output"] == 1


def test_generate_summary_failure_updates_failed_stage(summary_handler_module, monkeypatch):
    event = {"job_id": "job_500", "campaign_id": "cmp_500", "analysis": {}, "artifacts": {}}
    failed = {"count": 0}

    def raising_summary(**kwargs):
        raise RuntimeError("summary exploded")

    def fake_fail_stage(*args, **kwargs):
        failed["count"] += 1

    monkeypatch.setattr(summary_handler_module, "generate_summary", raising_summary)
    monkeypatch.setattr(summary_handler_module, "fail_stage", fake_fail_stage)

    with pytest.raises(RuntimeError):
        summary_handler_module.lambda_handler(event, None)

    assert failed["count"] == 1
