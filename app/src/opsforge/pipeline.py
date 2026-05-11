from datetime import UTC, datetime
from typing import Any


class PipelineValidationError(ValueError):
    pass


def summarize_input(payload: dict[str, Any]) -> str:
    title = str(payload.get("title", "")).strip()
    owner = str(payload.get("owner", "")).strip()
    data = payload.get("data") or {}
    return f"title={title}; owner={owner}; fields={len(data)}"


def process_report(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title", "")).strip()
    owner = str(payload.get("owner", "")).strip()
    data = payload.get("data")

    if payload.get("force_fail"):
        raise PipelineValidationError("forced failure requested")
    if not title or not owner:
        raise PipelineValidationError("title and owner are required")
    if not isinstance(data, dict):
        raise PipelineValidationError("data must be a JSON object")

    numeric_values = [value for value in data.values() if isinstance(value, int | float)]
    total = sum(numeric_values)
    return {
        "title": title,
        "owner": owner,
        "field_count": len(data),
        "numeric_field_count": len(numeric_values),
        "numeric_total": total,
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": f"Report '{title}' for {owner} processed {len(data)} fields.",
    }
