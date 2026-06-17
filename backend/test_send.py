import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.base")
os.environ["RESEND_API_KEY"] = "re_GnEPj2hU_5UzBggzzZgRiCVkck3CCy74q"
django.setup()

from anymail.message import AnymailMessage

msg = AnymailMessage(
    subject="Audit Test",
    body="Test",
    from_email="noreply@vishnumadapakula.in",
    to=["audit_123@vishnumadapakula.in"]
)
try:
    msg.send()
    print("Message ID:", msg.anymail_status.message_id)
    print("Status:", msg.anymail_status.status)
    if hasattr(msg.anymail_status, "esp_response"):
        print("ESP Response:", msg.anymail_status.esp_response.json())
except Exception as e:
    print("Exception:", type(e), e)
    if hasattr(e, "response"):
        print("Error Response:", e.response.json())
