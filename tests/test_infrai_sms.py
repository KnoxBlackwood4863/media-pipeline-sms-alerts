import httpx

from media_alerts.infrai_sms import InfraiSmsClient


def test_send_retries_429_and_preserves_request_identity() -> None:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"message_id": "msg_123"}, "error": None, "metadata": {}},
        )

    client = InfraiSmsClient(
        "test-key",
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
    )
    try:
        message_id = client.send(
            to="+14155550123",
            body="Media job job-91 is ready for delivery.",
            idempotency_key="media-job:job-91:processing_succeeded",
        )
    finally:
        client.close()

    assert message_id == "msg_123"
    assert sleeps == [2.0]
    assert [request.method for request in requests] == ["POST", "POST"]
    assert {request.headers["Idempotency-Key"] for request in requests} == {
        "media-job:job-91:processing_succeeded"
    }
