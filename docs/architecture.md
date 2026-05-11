# Local Architecture

OpsForge starts with a local baseline so application defects are separated from cloud infrastructure defects.

The local system has three runtime components:

- `api`: FastAPI service that accepts report requests and exposes health, readiness, metrics, and report lookup endpoints.
- `worker`: asynchronous job processor that polls pending report jobs and runs the report pipeline.
- `postgres`: durable local state for report jobs.

The report pipeline is intentionally small:

1. The API validates incoming JSON and stores a `pending` job.
2. The worker claims one pending job and marks it `running`.
3. The worker validates the job payload and generates a report summary.
4. The worker marks the job `succeeded` with output or `failed` with a failure reason.
5. Failed jobs can be retried without creating a duplicate job.

Future AWS mapping:

- Docker image -> ECR.
- PostgreSQL -> RDS.
- Worker polling -> SQS-backed worker.
- Compose service deployment -> ECS or Kubernetes.
- Structured stdout logs -> CloudWatch Logs.
