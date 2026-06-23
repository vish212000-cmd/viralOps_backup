import imaplib
import email
import re
import time

username = "kunl7sdwjbbp6rha@ethereal.email"
password = "B4WeHDUNCKzMZwWPbu"

print("Connecting to Ethereal IMAP...")
mail = imaplib.IMAP4_SSL("imap.ethereal.email")
mail.login(username, password)

# Poll the inbox for up to 15 seconds
for attempt in range(5):
    mail.select("inbox")
    status, messages = mail.search(None, "ALL")
    if messages[0]:
        latest_email_id = messages[0].split()[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                print("Subject:", msg["Subject"])
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        match = re.search(r"\d{6}", body)
                        if match:
                            print("OTP CODE:", match.group(0))
                            mail.logout()
                            exit(0)
        break
    else:
        print("Inbox is empty, waiting 3s...")
        time.sleep(3)

print("No verification email found.")
mail.logout()
