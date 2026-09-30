from __future__ import annotations

from html import escape
from datetime import datetime, timezone


def _time(value: float) -> str:
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def render_run_status(status: dict[str, object]) -> str:
    state = escape(str(status["state"]))
    rows = [
        ("Run", status["run_id"]),
        ("State", status["state"]),
        ("Attempt", status["attempt"]),
        ("Canonical job", status.get("canonical_job_id") or "not-bound"),
        ("Canonical status", status.get("canonical_status") or "not-queried"),
        ("Queue", status.get("queue_state") or "not-applicable"),
        ("Result available", status.get("result_available", False)),
    ]
    table = "".join(
        f"<tr><th scope='row'>{escape(str(k))}</th><td>{escape(str(v))}</td></tr>"
        for k, v in rows
    )
    return (
        "<section class='run-status' aria-labelledby='run-status-title' "
        f"data-run-state='{state}'>"
        "<h2 id='run-status-title'>Run status</h2>"
        "<p>No fabricated percentage is shown. Status is reconciled from persisted operator and canonical job state.</p>"
        f"<table><tbody>{table}</tbody></table>"
        "</section>"
    )


def render_timeline(timeline: dict[str, object]) -> str:
    items = []
    for event in timeline["events"]:
        payload = escape(str(event["payload"]))
        items.append(
            "<li>"
            f"<time datetime='{escape(_time(float(event['timestamp'])), quote=True)}'>"
            f"{escape(_time(float(event['timestamp'])))}</time> "
            f"<strong>{escape(str(event['event_type']))}</strong> "
            f"<span>({escape(str(event['origin']))})</span>"
            f"<pre>{payload}</pre>"
            "</li>"
        )
    return (
        "<section class='stage-timeline' aria-labelledby='timeline-title'>"
        "<h2 id='timeline-title'>Stage timeline</h2>"
        "<p>Events are read from operator metadata, canonical persistence and the durable queue.</p>"
        f"<ol>{''.join(items)}</ol>"
        "</section>"
    )
