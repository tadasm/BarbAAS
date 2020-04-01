from twilio.rest import Client
import requests
import os
import json
import re
import time
import sys

TWILIO_ACCOUNT_ID = os.environ.get("TWILIO_ACCOUNT_ID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_ACCOUNT_AUTH_TOKEN")
NUMBER_TO_SEND_SMS = os.environ.get("TWILIO_NUMBER_TO_SEND")
TWILIO_OUTGOING_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")

HOURS_TO_SLEEP = int(os.environ.get("HOURS_TO_SLEEP_AFTER_GETTING_SLOT", "6"))

COOKIE = os.environ["BARBORA_COOKIE"]
MS_TEAMS_WEBHOOK = os.environ.get("MS_TEAMS_WEBHOOK")
NOTIFICATIONS_TO_SEND = int(os.environ.get("NOTIFICATIONS_TO_SEND", "2"))

DRY_RUN = os.environ.get("DRY_RUN")

PUSH_BACK_SECONDS = int(os.environ.get("PUSH_BACK_BARBORA_API_IN_SECONDS", "30"))
sleep_long_as_informed = HOURS_TO_SLEEP * 60 * 60 * 1


if (
    TWILIO_ACCOUNT_ID
    and TWILIO_AUTH_TOKEN
    and TWILIO_OUTGOING_NUMBER
    and NUMBER_TO_SEND_SMS
):
    twilio_client = Client(TWILIO_ACCOUNT_ID, TWILIO_AUTH_TOKEN)
    print(f"Twilio Number to send SMS: {NUMBER_TO_SEND_SMS}")
    print(f"Twilio Outgoing Number: {TWILIO_OUTGOING_NUMBER}")
else:
    print(f"Twilio SMS Notifications disabled")

if MS_TEAMS_WEBHOOK:
    print(f"MS Teams Notifications Enabled")
else:
    print(f"MS Teams Notifications disabled")


BARBORA_URL = "https://www.barbora.lt/api/eshop/v1/cart/deliveries"

BARBORA_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Authorization": "Basic YXBpa2V5OlNlY3JldEtleQ==",
    "Connection": "keep-alive",
    "Host": "www.barbora.lt",
    "Referer": "https://www.barbora.lt/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
}

BARBORA_HEADERS["cookie"] = COOKIE


def send_notifications():
    if twilio_client:
        twilio_client.messages.create(
            to=NUMBER_TO_SEND_SMS,
            from_=TWILIO_OUTGOING_NUMBER,
            body=f"Barbora slot found at {today}",
        )

    if MS_TEAMS_WEBHOOK:
        send_message_to_teams(
            MS_TEAMS_WEBHOOK,
            "There are slots, book now [barbora.lt](https://www.barbora.lt)",
        )


def send_message_to_teams(wehook, message):
    message = {
        "@context": "http://schema.org/extensions",
        "@type": "MessageCard",
        "title": "Barbora Bot",
        "text": message,
    }
    requests.post(url=wehook, json=message)


def get_delivery_data():
    try:
        r = requests.request("GET", BARBORA_URL, headers=BARBORA_HEADERS)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
        if r.status_code == 401:
            print("No need to run, cookie expired - access denied")
            if MS_TEAMS_WEBHOOK:
                send_message_to_teams(
                    MS_TEAMS_WEBHOOK, "Failure: Coockie expired. Bot stopped working"
                )
            sys.exit(0)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)

    return


NOTIFICATIONS_THROTTLE = NOTIFICATIONS_TO_SEND
while True:
    if NOTIFICATIONS_THROTTLE == 0:
        time.sleep(sleep_long_as_informed)
        NOTIFICATIONS_THROTTLE = NOTIFICATIONS_TO_SEND
        print(f"Going to sleep for {HOURS_TO_SLEEP} hours")
        if MS_TEAMS_WEBHOOK:
            send_message_to_teams(
                MS_TEAMS_WEBHOOK, f"Going for sleep for {HOURS_TO_SLEEP} hours"
            )

    today = time.ctime()

    if not DRY_RUN:
        response = get_delivery_data()

        try:
            resp_str = json.dumps(response.json())
        except Exception as e:
            print(f"Was not able to parse response. Error: {e}")
            continue

    if DRY_RUN or re.search('"available": true', resp_str):
        print(f"Slot found at {today}")
        send_notifications()
        NOTIFICATIONS_THROTTLE = NOTIFICATIONS_THROTTLE - 1
    elif re.search('"title": null', resp_str):
        print(f"Empty response returned at {today}")
    else:
        print(f"No slots at {today}")

    time.sleep(PUSH_BACK_SECONDS)
