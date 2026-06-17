import imaplib
import email
import re
import time

username = "clfaw2xbnhgl4hlo@ethereal.email"
password = "nS9vzZEQagVMRNA18P"

print("Connecting to IMAP...")
mail = imaplib.IMAP4_SSL("imap.ethereal.email")
mail.login(username, password)

# Wait a few seconds for the email to arrive
time.sleep(5)

mail.select("inbox")
status, messages = mail.search(None, "ALL")

if messages[0]:
    latest_email_id = messages[0].split()[-1]
    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            print("Subject:", msg["Subject"])
            
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        print("Body:", body)
                        # Extract URL
                        match = re.search(r"http[s]?://[^\s]+", body)
                        if match:
                            print("Verification URL:", match.group(0))
            else:
                body = msg.get_payload(decode=True).decode()
                print("Body:", body)
                match = re.search(r"http[s]?://[^\s]+", body)
                if match:
                    print("Verification URL:", match.group(0))
else:
    print("No messages found.")

mail.logout()
