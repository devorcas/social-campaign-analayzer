from __future__ import annotations

from types import SimpleNamespace

import services.generate_summary.summary_client as summary_client


def test_summary_client_fallback_when_no_api_key(monkeypatch):
    monkeypatch.setattr(summary_client, "ANTHROPIC_API_KEY", None)
    out = summary_client.generate_summary({"visual": {"overall_score": 90}, "text": {"overall_score": 80}}, "hello")
    assert out.startswith("Automated summary fallback:")


def test_summary_client_success_with_sdk_response(monkeypatch):
    monkeypatch.setattr(summary_client, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(summary_client, "ANTHROPIC_MODEL", "claude-sonnet-4-6")

    class FakeMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[
                    SimpleNamespace(type="text", text="Summary line one."),
                    SimpleNamespace(type="text", text="Summary line two."),
                ]
            )

    class FakeAnthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr(summary_client, "Anthropic", FakeAnthropic)

    out = summary_client.generate_summary({"visual": {"overall_score": 95}, "text": {"overall_score": 88}}, "transcript")
    assert "Summary line one." in out
    assert "Summary line two." in out


def test_summary_client_fallback_on_sdk_exception(monkeypatch):
    monkeypatch.setattr(summary_client, "ANTHROPIC_API_KEY", "test-key")

    class BoomAnthropic:
        def __init__(self, api_key):
            class _Messages:
                def create(self, **kwargs):
                    raise RuntimeError("boom")

            self.messages = _Messages()

    monkeypatch.setattr(summary_client, "Anthropic", BoomAnthropic)
    out = summary_client.generate_summary({"visual": {"overall_score": 70}, "text": {"overall_score": 65}}, "x")
    assert out.startswith("Automated summary fallback:")
