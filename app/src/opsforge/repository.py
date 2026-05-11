from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from opsforge.models import JobStatus, ReportJob
from opsforge.pipeline import summarize_input


def create_report_job(session: Session, payload: dict) -> ReportJob:
    job = ReportJob(
        status=JobStatus.pending.value,
        payload=payload,
        input_summary=summarize_input(payload),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_report_job(session: Session, job_id: str) -> ReportJob | None:
    return session.get(ReportJob, job_id)


def retry_report_job(session: Session, job: ReportJob) -> ReportJob:
    now = datetime.now(UTC)
    job.status = JobStatus.pending.value
    job.failure_reason = None
    job.started_at = None
    job.finished_at = None
    job.updated_at = now
    session.commit()
    session.refresh(job)
    return job


def claim_next_pending_job(session: Session) -> ReportJob | None:
    statement: Select[tuple[ReportJob]] = (
        select(ReportJob)
        .where(ReportJob.status == JobStatus.pending.value)
        .order_by(ReportJob.created_at)
        .limit(1)
    )
    job = session.scalars(statement).first()
    if job is None:
        return None

    now = datetime.now(UTC)
    job.status = JobStatus.running.value
    job.attempts += 1
    job.started_at = now
    job.finished_at = None
    job.failure_reason = None
    job.updated_at = now
    session.commit()
    session.refresh(job)
    return job


def mark_succeeded(session: Session, job: ReportJob, output: dict) -> ReportJob:
    if job.status == JobStatus.succeeded.value and job.output is not None:
        return job

    now = datetime.now(UTC)
    job.status = JobStatus.succeeded.value
    job.output = output
    job.failure_reason = None
    job.finished_at = now
    job.updated_at = now
    session.commit()
    session.refresh(job)
    return job


def mark_failed(session: Session, job: ReportJob, reason: str) -> ReportJob:
    now = datetime.now(UTC)
    job.status = JobStatus.failed.value
    job.failure_reason = reason
    job.finished_at = now
    job.updated_at = now
    session.commit()
    session.refresh(job)
    return job


def job_counts_by_status(session: Session) -> dict[str, int]:
    rows = session.execute(select(ReportJob.status, func.count(ReportJob.id)).group_by(ReportJob.status))
    counts = {status.value: 0 for status in JobStatus}
    counts.update({status: count for status, count in rows})
    return counts
