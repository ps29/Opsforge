from sqlalchemy.orm import Session

from opsforge.repository import job_counts_by_status


def render_metrics(session: Session) -> str:
    counts = job_counts_by_status(session)
    total = sum(counts.values())
    lines = [
        "# HELP opsforge_jobs_total Total report jobs by status.",
        "# TYPE opsforge_jobs_total gauge",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f'opsforge_jobs_total{{status="{status}"}} {count}')
    lines.extend(
        [
            "# HELP opsforge_jobs_created_total Total report jobs created.",
            "# TYPE opsforge_jobs_created_total gauge",
            f"opsforge_jobs_created_total {total}",
            "# HELP opsforge_jobs_running Current running report jobs.",
            "# TYPE opsforge_jobs_running gauge",
            f"opsforge_jobs_running {counts.get('running', 0)}",
        ]
    )
    return "\n".join(lines) + "\n"
