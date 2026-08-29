"""HTTP entry point for media job events."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_sms import InfraiError, InfraiSmsClient
from .pipeline_alerts import AlertResult, MediaJobEvent, deliver_job_alert

app = FastAPI(title="Media pipeline SMS alerts")


@app.post("/job-events", response_model=AlertResult)
def accept_job_event(event: MediaJobEvent) -> AlertResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiSmsClient(api_key)
    try:
        return deliver_job_alert(event, client)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    finally:
        client.close()
