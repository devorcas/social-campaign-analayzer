from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from shared.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _fallback_summary(analysis: dict[str, Any]) -> str:
    visual_score = analysis.get("visual", {}).get("overall_score")
    text_score = analysis.get("text", {}).get("overall_score")
    return (
        "Automated summary fallback: analysis completed. "
        f"Visual safety score={visual_score}, text safety score={text_score}."
    )


def generate_summary(analysis: dict[str, Any], transcript_text: str | None = None) -> str:
    if not ANTHROPIC_API_KEY:
        return _fallback_summary(analysis)

    prompt = (
        "You are a content safety analyst. Produce a concise human-readable summary "
        "with: (1) content meaning, (2) transcript highlights, (3) key risks/flags.\n\n"
        f"Analysis JSON:\n{json.dumps(analysis, ensure_ascii=True)}\n\n"
        f"Transcript:\n{(transcript_text or '').strip()[:5000]}"
    )
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 400,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }

    req = urllib.request.Request(
        url="https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError:
        return _fallback_summary(analysis)

    parts = body.get("content", [])
    texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
    summary = "\n".join([t.strip() for t in texts if t.strip()])
    return summary or _fallback_summary(analysis)
