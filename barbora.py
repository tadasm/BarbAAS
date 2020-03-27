import requests
import os
import json
import re
import time

url = "https://www.barbora.lt/api/eshop/v1/cart/deliveries"

payload = {}
headers = {
  'Accept': '*/*',
  'Accept-Encoding': 'gzip, deflate, br',
  'Accept-Language': 'en-US,en;q=0.5',
  'Authorization': 'Basic REPLACE BY YOUR OWN AUTH HEADER',
  'Connection': 'keep-alive',
  'Cookie': 'REPLACE BY YOUR OWN AUTH COOKIE',
  'Host': 'www.barbora.lt',
  'Referer': 'https://www.barbora.lt/',
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:74.0) Gecko/20100101 Firefox/74.0',
}

try:
    r = requests.request("GET", url, headers=headers, data = payload)
    r.raise_for_status()
except requests.exceptions.RequestException as err:
    print ("OOps: Something Else",err)
except requests.exceptions.HTTPError as errh:
    print ("Http Error:",errh)
except requests.exceptions.ConnectionError as errc:
    print ("Error Connecting:",errc)
except requests.exceptions.Timeout as errt:
    print ("Timeout Error:",errt)     


resp_str = json.dumps(r.json())
today = time.ctime()

if (re.search('"available": true', resp_str)):
    print(f"Slot found at {today}")
    os.system('say "Slot found! Be quick"')
elif (re.search('"title": null', resp_str)):
    print(f"Empty response returned at {today}")
else:
    print(f"No slots at {today}")


