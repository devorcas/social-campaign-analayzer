# LocalStack End-to-End Runbook

This document describes how to run the full stack locally with LocalStack and execute API calls end-to-end.

## Prerequisites

1. Docker Desktop running.
2. LocalStack CLI installed.
3. `awslocal` installed.
4. Python 3.12 with project dependencies.

## Start LocalStack

```bash
localstack start -d
```

Check readiness:

```bash
awslocal sts get-caller-identity
```

## Deploy SAM stack to LocalStack

From repo root:

```bash
cd cicd/sam
sam build --template-file template.yaml
```

Deploy with SAM wrapper for LocalStack:

```bash
samlocal deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name social-campaign-analyzer-local \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --resolve-s3 \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    EnvironmentName=local \
    AnthropicApiKey=YOUR_ANTHROPIC_KEY \
    AnthropicModel=claude-sonnet-4-6
```

## Get API base URL from stack outputs

```bash
awslocal cloudformation describe-stacks \
  --stack-name social-campaign-analyzer-local \
  --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue" \
  --output text
```

Example output:

```text
http://localhost:4566/restapis/abc123/local/_user_request_
```

## End-to-end API calls

Trigger analysis:

```bash
API_BASE_URL="http://localhost:4566/restapis/abc123/local/_user_request_"

curl -s -X POST "${API_BASE_URL}/v1/analysis-jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "cmp_local_001",
    "source": {
      "type": "amplify",
      "reference_id": "amplify_campaign_local_001"
    }
  }' | jq
```

Expected shape:

```json
{
  "job_id": "job_xxxxx",
  "status": "queued",
  "status_url": "/v1/analysis-jobs/job_xxxxx"
}
```

Poll result:

```bash
JOB_ID="job_xxxxx"
curl -s "${API_BASE_URL}/v1/analysis-jobs/${JOB_ID}" | jq
```

Expected progression:

1. `queued` -> `running` -> `completed`
2. `progress` fields updated per state
3. final `result` includes:
   - `overall_visual_safety_score`
   - `overall_text_safety_score`
   - `visual`
   - `text`
   - `human_summary`

## Troubleshooting

1. `docker not found`: install Docker Desktop and ensure daemon is running.
2. `Host key / auth` issues are unrelated to LocalStack; verify git/ssh separately.
3. If Anthropic call fails, summary stage returns deterministic fallback text.

## Notes from this Codex environment

I attempted to run LocalStack here and hit environment-specific blockers:

1. No Docker daemon available in sandbox.
2. `localstack start --host` failed due runtime plugin issues in this environment.
3. Because LocalStack could not start, API-level LocalStack E2E could not be executed in this sandbox.

The commands above are the exact run path for a normal local machine with Docker + LocalStack.
