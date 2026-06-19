import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()

from projects.tasks import process_source_input
from celery.exceptions import Retry

print("Executing process_source_input(41) to capture stack trace...")
try:
    process_source_input(41)
except Retry:
    pass
except Exception as e:
    print("CAUGHT EXCEPTION:")
    traceback.print_exc()

import logging
logging.basicConfig(level=logging.INFO)
