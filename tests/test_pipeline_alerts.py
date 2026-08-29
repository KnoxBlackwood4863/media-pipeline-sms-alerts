from media_alerts.pipeline_alerts import MediaJobEvent, deliver_job_alert


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send(self, *, to: str, body: str, idempotency_key: str) -> str:
        self.calls.append(
            {"to": to, "body": body, "idempotency_key": idempotency_key}
        )
        return "msg_test_42"


def test_completion_alert_has_stable_job_identity() -> None:
    sender = RecordingSender()
    event = MediaJobEvent(
        asset_id="asset-7",
        job_id="job-91",
        creator_phone="+14155550123",
        asset_title="Daily highlights",
        stage="processing_succeeded",
    )

    result = deliver_job_alert(event, sender)

    assert result.model_dump() == {
        "action": "sent",
        "job_id": "job-91",
        "message_id": "msg_test_42",
    }
    assert sender.calls == [
        {
            "to": "+14155550123",
            "body": 'Media job job-91 for "Daily highlights" is ready for delivery.',
            "idempotency_key": "media-job:job-91:processing_succeeded",
        }
    ]


def test_ingestion_is_recorded_without_creator_alert() -> None:
    sender = RecordingSender()
    event = MediaJobEvent(
        asset_id="asset-7",
        job_id="job-91",
        creator_phone="+14155550123",
        asset_title="Daily highlights",
        stage="asset_ingested",
    )

    result = deliver_job_alert(event, sender)

    assert result.action == "recorded"
    assert sender.calls == []
