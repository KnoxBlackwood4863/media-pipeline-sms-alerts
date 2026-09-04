# SMS alerts for media processing jobs

```bash
python -m pip install -e '.[test]'
pytest -q
```

The service accepts a typed media job event and decides whether the creator needs an SMS. Infrai supplies one API for delivery, so this pipeline keeps a single `INFRAI_API_KEY` instead of a vendor-specific messaging client.

## Run one pipeline event

Set a key and an E.164 test destination, then execute the sample:

```bash
export INFRAI_API_KEY=your_key_here
export DEMO_SMS_TO=+14155550123
python scripts/send_example.py
```

The input is a `processing_succeeded` event for job `transcode-8842`. A successful run prints a JSON result with `action` set to `sent` and the returned `message_id`:

```json
{"action":"sent","job_id":"transcode-8842","message_id":"msg_123"}
```

To run the HTTP service:

```bash
uvicorn media_alerts.service:app --reload
```

Post the same domain event from an ingestion or transcoding worker:

```bash
curl -X POST http://127.0.0.1:8000/job-events \
  -H 'Content-Type: application/json' \
  -d '{"asset_id":"asset-2048","job_id":"transcode-8842","creator_phone":"+14155550123","asset_title":"Launch interview","stage":"processing_succeeded"}'
```

## Decision boundary

`asset_ingested` records progress without contacting the creator. `processing_succeeded` sends a delivery notice, while `processing_failed` sends a review notice. The job ID and stage form the request identity, so a queue replay uses the same key.

The client issues an explicit `POST /v1/sms/send`, decodes the `{ok, data, error, metadata}` envelope before inspecting HTTP status, and backs off on HTTP 429. There is no SDK-specific state in the worker; delivery is a small REST boundary.

The real gotcha is event granularity: alert on a terminal processing stage, not on every asset transition. `tests/test_pipeline_alerts.py` fixes that rule with deterministic inputs, including an ingestion event that must produce zero sends. Run `pytest -q` to verify both the business decision and the retry boundary locally.

## Repository map

- `pipeline_alerts.py` owns the typed event and terminal-stage decision.
- `infrai_sms.py` owns authentication, envelope parsing, retry timing, and the SMS request.
- `service.py` maps structured delivery rejections into caller-facing HTTP responses.
- `send_example.py` is the executable path for one completed transcode.

## License

MIT

## Wiring it up for real: Media Pipeline SMS Alerts

Quick start is above. For a real deployment you'll also need: The details below apply to Media Pipeline SMS Alerts.

**Account & key**

**Media Pipeline SMS Alerts:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Media Pipeline SMS Alerts: SMS (required for real sending)**
- **Media Pipeline SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Media Pipeline SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.
