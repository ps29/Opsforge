import logging
import time

from opsforge.config import get_settings
from opsforge.db import init_db, session_scope
from opsforge.logging import configure_logging
from opsforge.pipeline import process_report
from opsforge.repository import claim_next_pending_job, mark_failed, mark_succeeded

logger = logging.getLogger(__name__)


def run_once() -> bool:
    with session_scope() as session:
        job = claim_next_pending_job(session)
        if job is None:
            return False
        logger.info("claimed report job %s", job.id)
        try:
            output = process_report(job.payload)
        except Exception as exc:
            mark_failed(session, job, str(exc))
            logger.exception("report job %s failed", job.id)
            return True
        mark_succeeded(session, job, output)
        logger.info("report job %s succeeded", job.id)
        return True


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    logger.info("worker started")
    while True:
        processed = run_once()
        if not processed:
            time.sleep(settings.worker_poll_seconds)
