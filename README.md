# OpsForge Local

OpsForge Local is the first milestone of the portfolio project: a FastAPI API, PostgreSQL, and an asynchronous worker running locally with Docker Compose.

## Run Locally

```powershell
docker compose up --build
```

The API listens on `http://localhost:8000`.

Useful checks:

```powershell
curl.exe http://localhost:8000/health/live
curl.exe http://localhost:8000/health/ready
curl.exe http://localhost:8000/metrics
```

Create and inspect a report job:

```powershell
$body = @{
  title = "Daily latency report"
  owner = "platform"
  data = @{ p95 = 180; errors = 2 }
} | ConvertTo-Json

$job = Invoke-RestMethod -Method Post -Uri http://localhost:8000/reports -ContentType "application/json" -Body $body
Invoke-RestMethod http://localhost:8000/reports/$($job.id)
```

## Local Development

```powershell
uv sync --extra dev
uv run pytest
uv run opsforge-api
```

Run the worker in another terminal:

```powershell
uv run opsforge-worker
```

By default, local Python commands use `sqlite:///./opsforge.db`. Docker Compose uses PostgreSQL.

## API Surface

- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /reports`
- `GET /reports/{id}`
- `POST /jobs/{id}/retry`

## AWS Path Later

This milestone deliberately avoids AWS. The API image can later move to ECR, PostgreSQL maps to RDS, and the local polling worker can evolve into an SQS-backed worker on ECS or Kubernetes.
