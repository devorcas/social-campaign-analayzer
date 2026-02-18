# SAM Deployment

This folder contains AWS SAM infrastructure for the Social Campaign Analyzer stack.

## Files

1. `template.yaml`  
   Defines API Gateway, Lambda functions, Step Functions workflow, DynamoDB table, and S3 artifacts bucket.
2. `workflow.asl.json`  
   Step Functions definition used by `AWS::Serverless::StateMachine`.

## Build and Validate

```bash
cd cicd/sam
sam build --template-file template.yaml
sam validate --template-file .aws-sam/build/template.yaml
```

## Deploy (example)

```bash
cd cicd/sam
sam deploy \
  --guided \
  --template-file .aws-sam/build/template.yaml \
  --parameter-overrides EnvironmentName=dev AnthropicApiKey=<your_key>
```

## Notes

1. `CodeUri` points to repository root so handlers under `services/*` and shared modules under `shared/*` are available.
2. `ANTHROPIC_API_KEY` is passed as a parameter for now. Move to AWS Secrets Manager before production.
