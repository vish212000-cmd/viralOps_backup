import os
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Check that all required production secrets and environment variables are configured'

    def handle(self, *args, **options):
        required_vars = [
            'SECRET_KEY',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'RAZORPAY_KEY_ID',
            'RAZORPAY_KEY_SECRET',
        ]
        
        warning_vars = [
            'GEMINI_API_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'EMAIL_HOST',
            'EMAIL_HOST_USER',
            'EMAIL_HOST_PASSWORD'
        ]

        missing_required = []
        for var in required_vars:
            val = os.getenv(var)
            if not val:
                missing_required.append(var)
            elif var == 'SECRET_KEY' and val == 'django-insecure-060b&@4r83dz(o()bj8a%hyd@x5ar1!(f9#5o)--bgl!g^f_q8':
                self.stderr.write(self.style.ERROR("SECRET_KEY must not use the default insecure key in production."))
                missing_required.append(var)

        missing_warnings = [var for var in warning_vars if not os.getenv(var)]

        if missing_required:
            self.stderr.write(self.style.ERROR(f"CRITICAL: Missing required environment variables: {', '.join(missing_required)}"))
            raise CommandError("Production secrets validation failed.")
            
        self.stdout.write(self.style.SUCCESS("All required production secrets are configured successfully!"))
        
        if missing_warnings:
            self.stdout.write(self.style.WARNING(f"Warning: The following optional integration variables are not set: {', '.join(missing_warnings)}"))
