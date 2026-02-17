# Social Campaign Analyzer

## Analysis API

This service exposes an asynchronous job API for campaign content analysis.

### Endpoints

1. `POST /v1/analysis-jobs`  
   Trigger a new analysis job.
2. `GET /v1/analysis-jobs/{job_id}`  
   Fetch job status and final result.

---

## 1) Create Analysis Job

`POST /v1/analysis-jobs`

### Request

```json
{
  "campaign_id": "cmp_123",
  "source": {
    "type": "amplify",
    "reference_id": "amplify_campaign_987"
  }
}
```

### Response

`202 Accepted`

```json
{
  "job_id": "job_01JXYZ...",
  "status": "queued",
  "created_at": "2026-02-17T18:20:00Z",
  "status_url": "/v1/analysis-jobs/job_01JXYZ..."
}
```

### Notes

1. Use `Idempotency-Key` header to avoid duplicate job creation.
2. API validates `campaign_id` and `source.reference_id`.
3. The service returns immediately and processes analysis asynchronously.

---

## 2) Get Job Status / Result

`GET /v1/analysis-jobs/{job_id}`

### In-progress Response

`200 OK`

```json
{
  "job_id": "job_01JXYZ...",
  "status": "running",
  "progress": {
    "ingestion": "completed",
    "transcription": "running",
    "moderation": "pending",
    "aggregation": "pending",
    "summary": "pending"
  },
  "created_at": "2026-02-17T18:20:00Z",
  "updated_at": "2026-02-17T18:21:10Z"
}
```

### Completed Response

`200 OK`

```json
{
  "job_id": "job_01JXYZ...",
  "status": "completed",
  "result": {
    "visual": {
      "overall_score": 92.4,
      "categories": [
        {
          "name": "adult_content",
          "score": 96.0,
          "status": "Safe"
        },
        {
          "name": "violence_weapons",
          "score": 91.0,
          "status": "Safe"
        },
        {
          "name": "racy_content",
          "score": 88.0,
          "status": "Warning"
        },
        {
          "name": "medical_gore",
          "score": 95.0,
          "status": "Safe"
        },
        {
          "name": "spoof_fake_content",
          "score": 84.0,
          "status": "Warning",
          "explanation": "Potential manipulated media indicators detected."
        }
      ]
    },
    "text": {
      "overall_score": 86.3,
      "categories": [
        {
          "name": "profanity",
          "score": 90.0,
          "status": "Safe"
        },
        {
          "name": "hate_speech",
          "score": 93.0,
          "status": "Safe"
        },
        {
          "name": "misinformation",
          "score": 80.0,
          "status": "Warning"
        },
        {
          "name": "brand_mentions",
          "score": 82.0,
          "status": "Warning",
          "explanation": "Brand mention detected without clear context."
        },
        {
          "name": "disclosure_compliance",
          "score": 78.0,
          "status": "Warning",
          "explanation": "Missing clear sponsorship disclosure markers."
        },
        {
          "name": "political_content",
          "score": 87.0,
          "status": "Safe"
        }
      ]
    },
    "human_summary": "Creator content is mostly safe. Key risks are spoof/fake signals and disclosure quality."
  },
  "created_at": "2026-02-17T18:20:00Z",
  "updated_at": "2026-02-17T18:23:40Z"
}
```

---

## Status Model

Job-level status values:

1. `queued`
2. `running`
3. `completed`
4. `completed_with_warnings`
5. `failed`

---

## HTTP Errors

1. `400` invalid request payload.
2. `404` job not found.
3. `409` idempotency conflict.
4. `500` internal error while creating job.

---

## Architecture Solution

### Goal

Provide a reliable and cost-effective asynchronous content analysis pipeline using serverless AWS components.

### AWS Components

1. API Gateway
2. Lambda (`api_handler`) for `POST /v1/analysis-jobs` and `GET /v1/analysis-jobs/{job_id}`
3. Step Functions (workflow orchestration)
4. Lambda workers per pipeline stage
5. DynamoDB (`analysis_jobs`) for job status and final output
6. S3 for intermediate artifacts (ingestion output, transcripts, moderation raw responses)
7. AWS Secrets Manager for third-party API keys
8. CloudWatch Logs/Metrics for observability

### State Machine Breakdown

1. `ValidateInput`
2. `IngestContent`
3. `PrepareMedia`
4. `ParallelAnalysis`
   - `TranscribeAudio` -> `ModerateText`
   - `ModerateVisual`
5. `AggregateScores`
6. `GenerateSummaryAndPersist`
7. `MarkCompleted`

### Data Flow Between Stages

The workflow passes compact metadata and artifact references, not large payloads.

```json
{
  "job_id": "job_01JXYZ",
  "campaign_id": "cmp_123",
  "source_ref": "amplify_campaign_987",
  "artifacts": {
    "ingestion_s3_uri": "s3://bucket/jobs/job_01JXYZ/ingestion.json",
    "transcript_s3_uri": "s3://bucket/jobs/job_01JXYZ/transcript.json",
    "visual_s3_uri": "s3://bucket/jobs/job_01JXYZ/visual.json",
    "text_s3_uri": "s3://bucket/jobs/job_01JXYZ/text.json",
    "final_s3_uri": "s3://bucket/jobs/job_01JXYZ/final.json"
  }
}
```

### Reliability Strategy

1. API is asynchronous: `POST` returns `202` quickly with `job_id`.
2. Step-level retries with exponential backoff for transient provider/network failures.
3. DynamoDB remains the source of truth for job status.
4. S3 stores large outputs to keep workflow state small.

### Latency and Cost Notes

1. Use parallel moderation paths to reduce end-to-end latency.
2. Process only selected keyframes instead of every video frame.
3. Skip transcription when no audio is available.
4. Use pay-per-use serverless compute and tune Lambda memory per stage.
