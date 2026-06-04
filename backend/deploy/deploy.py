#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command

def main():
    """Wrapper script to execute deploy command stages"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
    django.setup()

    # Parse arguments
    stage = 'migration'
    base_url = 'http://localhost:8000'

    for idx, arg in enumerate(sys.argv):
        if arg == '--stage' and idx + 1 < len(sys.argv):
            stage = sys.argv[idx + 1]
        elif arg.startswith('--stage='):
            stage = arg.split('=')[1]
        elif arg == '--base-url' and idx + 1 < len(sys.argv):
            base_url = sys.argv[idx + 1]
        elif arg.startswith('--base-url='):
            base_url = arg.split('=')[1]

    try:
        call_command('deploy', stage=stage, base_url=base_url)
    except Exception as e:
        sys.stderr.write(f"Deployment script failure: {str(e)}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
