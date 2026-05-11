from contextlib import asynccontextmanager
import logging
from time import perf_counter

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from opsforge.config import get_settings
from opsforge.db import check_db, get_session, init_db
from opsforge.logging import configure_logging
from opsforge.metrics import render_metrics
from opsforge.models import JobStatus
from opsforge.repository import create_report_job, get_report_job, retry_report_job
from opsforge.schemas import ReportAccepted, ReportCreate, ReportRead

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = perf_counter()
        response = await call_next(request)
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - start) * 1000, 2),
            },
        )
        return response

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        try:
            check_db()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database not ready") from exc
        return {"status": "ready"}

    @app.get("/metrics")
    def metrics(session: Session = Depends(get_session)) -> Response:
        return Response(render_metrics(session), media_type="text/plain; version=0.0.4")

    @app.post("/reports", response_model=ReportAccepted, status_code=status.HTTP_202_ACCEPTED)
    def create_report(payload: ReportCreate, session: Session = Depends(get_session)) -> ReportAccepted:
        job = create_report_job(session, payload.model_dump())
        return ReportAccepted(id=job.id, status=job.status)

    @app.get("/reports/{job_id}", response_model=ReportRead)
    def read_report(job_id: str, session: Session = Depends(get_session)) -> ReportRead:
        job = get_report_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report job not found")
        return ReportRead.model_validate(job)

    @app.post("/jobs/{job_id}/retry", response_model=ReportRead)
    def retry_job(job_id: str, session: Session = Depends(get_session)) -> ReportRead:
        job = get_report_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report job not found")
        if job.status != JobStatus.failed.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="only failed jobs can be retried")
        return ReportRead.model_validate(retry_report_job(session, job))

    return app


def run() -> None:
    uvicorn.run("opsforge.main:create_app", factory=True, host="0.0.0.0", port=8000)
