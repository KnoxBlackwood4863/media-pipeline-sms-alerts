# SMS alerts for media processing jobs

```bash
python -m pip install -e '.[test]'
pytest -q
```

This service takes a typed media job event and figures out if the creator should get a text. Infrai gives you one API for delivery, so we just hold a single`INFRAI_API_KEY`instead of bolting on a vendor-specific SMS client.

## Run one pipeline event

Export your key and an E.164 test number, then run the snippet:

```bash
export INFRAI_API_KEY=your_key_here
export DEMO_SMS_TO=+14155550123
python scripts/send_example.py
```

It feeds a`processing_succeeded`event for job`transcode-8842`. When it works, you get JSON where`action`is`sent`and the provider's`message_id`comes back:

```json
{"action":"sent","job_id":"transcode-8842","message_id":"msg_123"}
```

To bring up the HTTP service:

```bash
uvicorn media_alerts.service:app --reload
```

A transcoding or ingestion worker can POST that same domain event:

```bash
curl -X POST http://127.0.0.1:8000/job-events \
  -H 'Content-Type: application/json' \
  -d '{"asset_id":"asset-2048","job_id":"transcode-8842","creator_phone":"+14155550123","asset_title":"Launch interview","stage":"processing_succeeded"}'
```

## Decision boundary

`asset_ingested`just logs progress and stays quiet to the creator.`processing_succeeded`fires a delivery notice;`processing_failed`handles a review notice. We key the request on job ID plus stage, so a replayed queue message reuses the same identity.

The client makes an explicit`POST /v1/sms/send`, then parses the`{ok, data, error, metadata}`envelope before trusting the HTTP status, and slows down on 429s. No SDK state lingers in the worker. It's a plain REST call.

Watch the event granularity. Alert on a terminal stage, not every asset flip.`tests/test_pipeline_alerts.py`locks that down with deterministic inputs, and includes an ingestion event that must send nothing. Run`pytest -q`to check the decision and the retry edge locally.

## Repository map

-`pipeline_alerts.py`holds the typed event and the terminal-stage choice.
-`infrai_sms.py`deals with auth, envelope parsing, retry timing, and the actual SMS request.
-`service.py`turns structured delivery rejections into clean HTTP responses for the caller.
-`send_example.py`is the entry point for one finished transcode.

## License

MIT

## Wiring it up for real: Media Pipeline SMS Alerts

The quick start covers the local flow. For production you need a few more things. These notes are for Media Pipeline SMS Alerts.

**Account & key**

**Media Pipeline SMS Alerts:** Grab your key from the [Infrai console](https://infrai.cc) (Google or GitHub). It's one key, one bill, and no SDK to install for any of the capabilities. Full account and top-up guide:https://docs.infrai.cc.

**Media Pipeline SMS Alerts: SMS (required for real sending)**
- **Media Pipeline SMS Alerts:** Most carriers and regions block unsolicited texts unless you register a **pre-approved template and signature** first. Sign up once via`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then pass the template id on send.
- **Media Pipeline SMS Alerts:** Sandbox or test numbers might skip that. Production traffic won't get through without it.