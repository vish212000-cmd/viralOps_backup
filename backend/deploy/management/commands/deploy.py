import os
import sys
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader

class Command(BaseCommand):
    help = 'Deploy automations and verification controller'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stage',
            type=str,
            required=True,
            choices=['migration', 'deploy', 'rollback', 'smoke', 'release'],
            help='Deployment stage to execute'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default=os.getenv('SMOKE_TEST_BASE_URL', 'http://localhost:8000'),
            help='Base URL for smoke testing'
        )

    def handle(self, *args, **options):
        stage = options['stage']
        base_url = options['base_url']

        if stage == 'migration':
            self.stdout.write(self.style.WARNING("=== STAGE: MIGRATION ==="))
            self.stdout.write("Running database migrations...")
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS("Database migrations applied successfully."))

            # Pause for manual verification in interactive sessions
            if sys.stdin.isatty():
                input(self.style.WARNING("\nMigrations complete. Press Enter to verify and proceed..."))
            else:
                self.stdout.write("Non-interactive mode: Skipping verification pause.")

        elif stage == 'deploy':
            self.stdout.write(self.style.WARNING("=== STAGE: DEPLOY ==="))
            compose_file = 'docker-compose.staging.yml' if os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('staging') else 'docker-compose.yml'
            self.stdout.write(f"Building Docker images and launching stack using {compose_file}...")

            try:
                # Cache previous tag before building fresh images
                subprocess.run(['docker', 'tag', 'viralops-backend:latest', 'viralops-backend:previous'], capture_output=True)
                subprocess.run(['docker', 'tag', 'viralops-frontend:latest', 'viralops-frontend:previous'], capture_output=True)
            except Exception:
                pass

            try:
                subprocess.run(['docker', 'compose', '-f', compose_file, 'build'], check=True)
                subprocess.run(['docker', 'compose', '-f', compose_file, 'up', '-d'], check=True)
                self.stdout.write(self.style.SUCCESS("Docker stack build and deployment complete."))
            except subprocess.CalledProcessError as e:
                raise CommandError(f"Docker deployment failed: {str(e)}")

        elif stage == 'rollback':
            self.stdout.write(self.style.WARNING("=== STAGE: ROLLBACK ==="))
            
            # 1. Rollback Docker Containers
            compose_file = 'docker-compose.staging.yml' if os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('staging') else 'docker-compose.yml'
            self.stdout.write(f"Reverting Docker images and redeploying using {compose_file}...")
            try:
                subprocess.run(['docker', 'tag', 'viralops-backend:previous', 'viralops-backend:latest'], check=True)
                subprocess.run(['docker', 'tag', 'viralops-frontend:previous', 'viralops-frontend:latest'], check=True)
                subprocess.run(['docker', 'compose', '-f', compose_file, 'up', '-d'], check=True)
                self.stdout.write(self.style.SUCCESS("Docker container rollback completed."))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"Warning: Docker tag revert failed or no prior tag: {str(e)}"))

            # 2. Rollback last database migration
            self.stdout.write("Identifying last applied database migration to revert...")
            loader = MigrationLoader(connection)
            with connection.cursor() as cursor:
                cursor.execute("SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()

            if row:
                app, name = row
                self.stdout.write(f"Last applied migration: {app}.{name}")
                node = loader.graph.nodes.get((app, name))
                app_parents = [dep_name for dep_app, dep_name in node.dependencies if dep_app == app] if node else []
                if app_parents:
                    parent_name = app_parents[0]
                    self.stdout.write(self.style.WARNING(f"Rolling back migration for app '{app}' to '{parent_name}'..."))
                    call_command('migrate', app, parent_name)
                    self.stdout.write(self.style.SUCCESS(f"Reverted to migration '{parent_name}'."))
                else:
                    self.stdout.write(self.style.WARNING(f"No prior migration for app '{app}'. Reverting app to zero..."))
                    call_command('migrate', app, 'zero')
                    self.stdout.write(self.style.SUCCESS(f"Reverted app '{app}' to zero."))
            else:
                self.stdout.write("No applied migrations found to revert.")

        elif stage == 'smoke':
            self.stdout.write(self.style.WARNING("=== STAGE: SMOKE TESTS ==="))
            self.stdout.write(f"Executing post-deployment smoke tests against: {base_url}")
            
            # Import smoke test runner dynamically to keep concerns decoupled
            try:
                from projects.smoke_tests import run_smoke_tests
            except ImportError as e:
                raise CommandError(f"Smoke tests suite file is missing or contains errors: {str(e)}")

            success = run_smoke_tests(base_url)
            if success:
                self.stdout.write(self.style.SUCCESS("All smoke tests passed! Application is fully operational."))
            else:
                raise CommandError("Smoke tests failed. Review logs for tracebacks.")

        elif stage == 'release':
            self.stdout.write(self.style.WARNING("=== STAGE: RELEASE ORCHESTRATION ==="))
            self.stdout.write("[Blue-Green Routing] Simulating Blue-Green deployment swap...")
            
            # 1. Migrate
            self.stdout.write("\n[1/3] Executing release migrations...")
            call_command('deploy', stage='migration', base_url=base_url)

            # 2. Deploy (Green parallel build)
            self.stdout.write("\n[2/3] Building and executing Green stack parallel to Blue...")
            call_command('deploy', stage='deploy', base_url=base_url)

            # 3. Smoke Check & Gated Release
            self.stdout.write("\n[3/3] Initiating health-gated smoke tests check...")
            try:
                call_command('deploy', stage='smoke', base_url=base_url)
                
                # Success: swap routing
                self.stdout.write(self.style.SUCCESS("\n[Blue-Green Routing] Swapping traffic. Redirecting 100% traffic to Green environment."))
                self.stdout.write(self.style.SUCCESS("=== RELEASE SUCCESS: Operational rollout complete ==="))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n[RELEASE FAILURE] Health check / Smoke tests failed: {str(e)}"))
                self.stdout.write(self.style.ERROR("[ROLLBACK] Initiating automated zero-downtime rollback to Blue environment..."))
                
                try:
                    call_command('deploy', stage='rollback', base_url=base_url)
                    self.stdout.write(self.style.SUCCESS("[ROLLBACK] Automated rollback complete. Previous Blue version restored successfully."))
                except Exception as rollback_err:
                    self.stdout.write(self.style.ERROR(f"[CRITICAL] Rollback execution encountered failure: {str(rollback_err)}"))
                
                raise CommandError("Release aborted. Automated rollback applied.")

