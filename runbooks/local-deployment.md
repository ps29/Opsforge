# Local Deployment Runbook

## Start

```powershell
docker compose up --build
```

## Check Health

```powershell
curl.exe http://localhost:8000/health/live
curl.exe http://localhost:8000/health/ready
```

`/health/live` checks the API process. `/health/ready` checks database connectivity.

## Create A Job

```powershell
$body = @{
  title = "Daily latency report"
  owner = "platform"
  data = @{ p95 = 180; errors = 2 }
} | ConvertTo-Json

$job = Invoke-RestMethod -Method Post -Uri http://localhost:8000/reports -ContentType "application/json" -Body $body
Invoke-RestMethod http://localhost:8000/reports/$($job.id)
```

The worker should move the job from `pending` to `running`, then `succeeded`.

## Retry A Failed Job

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/jobs/<job-id>/retry
```

Only failed jobs can be retried.

## Logs

```powershell
docker compose logs api
docker compose logs worker
docker compose logs postgres
```

API and worker logs are JSON-formatted on stdout.

## Reset Local State

```powershell
docker compose down -v
docker compose up --build
```

This removes the PostgreSQL volume and starts with an empty database.

## Common Failures

- Readiness returns 503: check `docker compose logs postgres` and confirm the database healthcheck passed.
- Jobs remain pending: check `docker compose logs worker`.
- Port 8000 is busy: stop the conflicting service or change the API port mapping in `docker-compose.yml`.
