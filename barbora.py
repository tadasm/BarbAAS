from twilio.rest import Client
import requests
import os
import json
import re
import time
import sys

# put your own credentials here
ACCOUNT_ID = os.environ["TWILIO_ACCOUNT_ID"]
AUTH_TOKEN = os.environ["TWILIO_ACCOUNT_AUTH_TOKEN"]
COOKIE = os.environ["BARBORA_COOKIE"]

NUMBER_TO_SEND_SMS = os.environ["TWILIO_NUMBER_TO_SEND"]
TWILIO_OUTGOING_NUMBER = os.environ["TWILIO_FROM_NUMBER"]


SMS_TO_SEND = 2
PUSH_BACK_SECONDS = 10
HOURS_TO_SLEEP = 5
sleep_long_as_informed = HOURS_TO_SLEEP * 60 * 60 * 1

client = Client(ACCOUNT_ID, AUTH_TOKEN)

print(f"Twilio Number to send SMS: {NUMBER_TO_SEND_SMS}")
print(f"Twilio Outgoing Number: {TWILIO_OUTGOING_NUMBER}")

url = "https://www.barbora.lt/api/eshop/v1/cart/deliveries"


payload = {}
headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Authorization": "Basic REPLACE BY YOUR OWN AUTH HEADER",
    "Connection": "keep-alive",
    "Cookie": "REPLACE BY YOUR OWN AUTH COOKIE",
    "Host": "www.barbora.lt",
    "Referer": "https://www.barbora.lt/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:74.0) Gecko/20100101 Firefox/74.0",
}

headers["cookie"] = COOKIE

SMS_THROTTLE = SMS_TO_SEND
while True:
    if SMS_THROTTLE == 0:
        time.sleep(sleep_long_as_informed)
        SMS_THROTTLE = SMS_TO_SEND

    try:
        r = requests.request("GET", url, headers=headers, data=payload)
        r.raise_for_status()
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
        if r.status_code == 401:
            print("No need to run, cookie expired - access denied")
            sys.exit(0)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)

    resp_str = json.dumps(r.json())
    today = time.ctime()

    if re.search('"available": true', resp_str):
        print(f"Slot found at {today}")
        client.messages.create(
            to=NUMBER_TO_SEND_SMS,
            from_=TWILIO_OUTGOING_NUMBER,
            body=f"Barbora slot found at {today}",
        )
        SMS_THROTTLE = SMS_THROTTLE - 1
        os.system('say "Slot found! Be quick"')
    elif re.search('"title": null', resp_str):
        print(f"Empty response returned at {today}")
    else:
        print(f"No slots at {today}")

    time.sleep(PUSH_BACK_SECONDS)
