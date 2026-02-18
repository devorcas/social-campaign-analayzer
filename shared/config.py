import os


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip()


ANALYSIS_TABLE_NAME = get_env("ANALYSIS_TABLE_NAME", "analysis_jobs")
ARTIFACTS_BUCKET = get_env("ARTIFACTS_BUCKET")
STATE_MACHINE_ARN = get_env("STATE_MACHINE_ARN")
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = get_env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
