import os
import sys
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Validate all production configuration and service keys'

    # Define required env vars by category
    REQUIRED = {
        'DJANGO': ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST'],
        'AWS_S3': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME', 'AWS_S3_REGION_NAME'],
        'EMAIL': ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD'],
        'RAZORPAY': ['RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'RAZORPAY_WEBHOOK_SECRET'],
        'GOOGLE_OAUTH': ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'],
        'AI': ['GOOGLE_API_KEY'],  # Gemini
        'TRANSCRIPTION': ['OPENAI_API_KEY'],  # Whisper
        'MONITORING': ['SENTRY_DSN'],
    }

    def handle(self, *args, **options):
        all_passed = True
        results = {}

        for category, vars_list in self.REQUIRED.items():
            self.stdout.write(f'\n{"="*50}\n{category} Configuration\n{"="*50}')
            category_passed = True
            for var in vars_list:
                val = os.getenv(var, '')
                if not val:
                    self.stdout.write(self.style.ERROR(f'  [MISSING] {var}'))
                    category_passed = False
                elif val in ['change_this', 'placeholder', 'setup_required']:
                    self.stdout.write(self.style.WARNING(f'  [UNCONFIGURED] {var} (placeholder value found)'))
                    category_passed = False
                else:
                    self.stdout.write(self.style.SUCCESS(f'  [OK] {var}'))
            
            results[category] = category_passed
            if not category_passed:
                all_passed = False

        self.stdout.write(f'\n{"="*50}\nSUMMARY\n{"="*50}')
        for cat, passed in results.items():
            icon = '✓' if passed else '✗'
            self.stdout.write(f'  {icon} {cat}: {"PASS" if passed else "FAIL"}')

        if os.getenv('STAGING_TEST_MODE') == '1':
            self.run_staging_tests()

        if not all_passed and os.getenv('BLOCK_STARTUP_ON_MISSING_SECRETS') == '1':
            self.stdout.write(self.style.ERROR('\nStartup blocked: Missing required configuration.'))
            sys.exit(1)
        elif all_passed:
            self.stdout.write(self.style.SUCCESS('\nAll configurations validated.'))

        return all_passed

    def run_staging_tests(self):
        """Ping each external service to verify API keys are valid"""
        self.stdout.write(f'\n{"="*50}\nSERVICE CONNECTIVITY TESTS\n{"="*50}')

        # AWS S3 connectivity
        try:
            import boto3
            s3 = boto3.client('s3')
            s3.list_buckets()
            self.stdout.write(self.style.SUCCESS('  [OK] AWS S3 — Connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] AWS S3 — {str(e)[:60]}'))

        # Razorpay API test
        try:
            import razorpay
            client = razorpay.Client(auth=(
                os.getenv('RAZORPAY_KEY_ID'),
                os.getenv('RAZORPAY_KEY_SECRET')
            ))
            client.order.all({'count': 1})
            self.stdout.write(self.style.SUCCESS('  [OK] Razorpay — API connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] Razorpay — {str(e)[:60]}'))

        # Google OAuth (can only verify client_id format)
        google_id = os.getenv('GOOGLE_CLIENT_ID', '')
        if google_id and google_id.endswith('.apps.googleusercontent.com'):
            self.stdout.write(self.style.SUCCESS('  [OK] Google OAuth — Client ID format valid'))
        else:
            self.stdout.write(self.style.ERROR('  [FAIL] Google OAuth — Invalid Client ID format'))

        # Gemini API test
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            model.generate_content('test')
            self.stdout.write(self.style.SUCCESS('  [OK] Gemini AI — API connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] Gemini AI — {str(e)[:60]}'))

        # OpenAI Whisper test
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            client.models.list()
            self.stdout.write(self.style.SUCCESS('  [OK] OpenAI — API connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] OpenAI — {str(e)[:60]}'))

        # Database connection test
        from django.db import connection
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('  [OK] Database — Connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] Database — {str(e)[:60]}'))

        # Redis connection test
        try:
            import redis
            r = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD', None),
                decode_responses=True
            )
            r.ping()
            self.stdout.write(self.style.SUCCESS('  [OK] Redis — Connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] Redis — {str(e)[:60]}'))

        # SMTP connection test
        try:
            import smtplib
            server = smtplib.SMTP(
                os.getenv('EMAIL_HOST'),
                int(os.getenv('EMAIL_PORT', 587))
            )
            server.starttls()
            server.login(os.getenv('EMAIL_HOST_USER'), os.getenv('EMAIL_HOST_PASSWORD'))
            server.quit()
            self.stdout.write(self.style.SUCCESS('  [OK] SMTP — Connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [FAIL] SMTP — {str(e)[:60]}'))

        # Sentry DSN test (just format validation)
        dsn = os.getenv('SENTRY_DSN', '')
        if dsn and dsn.startswith('https://'):
            self.stdout.write(self.style.SUCCESS('  [OK] Sentry — DSN format valid'))
        else:
            self.stdout.write(self.style.ERROR('  [FAIL] Sentry — Invalid DSN format'))
