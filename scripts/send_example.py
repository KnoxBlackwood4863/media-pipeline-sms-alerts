"""Send one processing-complete alert to DEMO_SMS_TO."""

import os

from media_alerts.infrai_sms import InfraiSmsClient
from media_alerts.pipeline_alerts import MediaJobEvent, deliver_job_alert


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    phone = os.environ["DEMO_SMS_TO"]
    event = MediaJobEvent(
        asset_id="asset-2048",
        job_id="transcode-8842",
        creator_phone=phone,
        asset_title="Launch interview",
        stage="processing_succeeded",
    )
    client = InfraiSmsClient(api_key)
    try:
        result = deliver_job_alert(event, client)
        print(result.model_dump_json())
    finally:
        client.close()


if __name__ == "__main__":
    main()
