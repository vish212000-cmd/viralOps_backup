import requests
import time
import re

sid_token = "2npkv0mjugnpljinb2sv5q66up"
email = "hosdztzf@guerrillamailblock.com"
print("Checking for emails...")
for _ in range(10):
    time.sleep(5)
    r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=get_email_list&offset=0&sid_token={sid_token}", headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code == 200:
        data = r.json()
        if data.get("list"):
            for msg in data["list"]:
                if msg["mail_id"] != "1": # Ignore the welcome email
                    print("Found email!", msg["mail_subject"])
                    mail_id = msg["mail_id"]
                    r_msg = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={mail_id}&sid_token={sid_token}", headers={"User-Agent": "Mozilla/5.0"})
                    body = r_msg.json().get("mail_body", "")
                    print("Body:", body)
                    match = re.search(r"http[s]?://[^\s\"']+", body)
                    if match:
                        print("Verification URL:", match.group(0))
                    exit(0)
    print("Waiting...")
print("No email arrived.")
