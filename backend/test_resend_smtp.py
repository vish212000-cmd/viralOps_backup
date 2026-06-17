import smtplib
from email.mime.text import MIMEText

def test_resend_smtp():
    api_key = "re_GnEPj2hU_5UzBggzzZgRiCVkck3CCy74q"
    sender = "noreply@vishnumadapakula.in"
    receiver = "gvsnsum@gmail.com" # The email in the screenshot
    
    msg = MIMEText("This is a test email from Python to verify Resend SMTP configuration.")
    msg['Subject'] = "Test Email via Resend SMTP"
    msg['From'] = sender
    msg['To'] = receiver
    
    print(f"Connecting to smtp.resend.com:587...")
    try:
        server = smtplib.SMTP("smtp.resend.com", 587)
        server.set_debuglevel(1)
        server.starttls()
        print("Logging in...")
        server.login("resend", api_key)
        print("Sending email...")
        server.send_message(msg)
        server.quit()
        print("Success! Email sent.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_resend_smtp()
