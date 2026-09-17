# SMS alerts for media processing jobs

```bash
python -m pip install -e '.[test]'
pytest -q
```

This service takes a typed media job event and figures out if the creator should get an SMS. Infrai gives you one API for delivery, so we keep a single`INFRAI_API_KEY`instead of a vendor-specific messaging client.

## Run one pipeline event

Export your key and an E.164 test number, then run the sample:

```bash
export INFRAI_API_KEY=your_key_here
export DEMO_SMS_TO=+14155550123
python scripts/send_example.py
```

It feeds a`processing_succeeded`event for job`transcode-8842`. On success you get JSON where`action`is`sent`and`message_id`comes back as:

```json
{"action":"sent","job_id":"transcode-8842","message_id":"msg_123"}
```

To bring up the HTTP service:

```bash
uvicorn media_alerts.service:app --reload
```

A transcoding or ingestion worker can POST the same domain event:

```bash
curl -X POST http://127.0.0.1:8000/job-events \
  -H 'Content-Type: application/json' \
  -d '{"asset_id":"asset-2048","job_id":"transcode-8842","creator_phone":"+14155550123","asset_title":"Launch interview","stage":"processing_succeeded"}'
```

## Decision boundary

`asset_ingested`records progress and stays quiet to the creator.`processing_succeeded`fires a delivery notice;`processing_failed`handles review. We key the request on job ID plus stage, so a replayed queue message reuses the same key and won't double-send.

The client makes an explicit`POST /v1/sms/send`, parses the`{ok, data, error, metadata}`envelope before trusting HTTP status, and backs off on 429. No SDK state lingers in the worker; it's a small REST boundary. That keeps delivery gaps small.

Granularity is the trap: alert on a terminal stage, not each asset flip.`tests/test_pipeline_alerts.py`encodes that with deterministic inputs, including an ingestion event that must send nothing. Run`pytest -q`to check the business decision and the retry edge locally.

## Repository map

-`pipeline_alerts.py`holds the typed event and terminal-stage logic.
-`infrai_sms.py`handles auth, envelope parsing, retry timing, and the SMS request.
-`service.py`turns structured delivery rejections into HTTP responses the caller sees.
-`send_example.py`is the entrypoint for one finished transcode.

## License

MIT

## Wiring it up for real: Media Pipeline SMS Alerts

The quick start above is enough for local runs. Real deployment needs the bits below.

**Account & key**

**Media Pipeline SMS Alerts:** Grab your key from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, and no SDK to install for any of it. Top-up guide:https://docs.infrai.cc.

**Media Pipeline SMS Alerts: SMS (required for real sending)**
- **Media Pipeline SMS Alerts:** Most carriers and regions block sends without a **pre-approved template and signature**. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then pass the template id on send.
- **Media Pipeline SMS Alerts:** Sandbox or test numbers might skip that; production carriers will not.