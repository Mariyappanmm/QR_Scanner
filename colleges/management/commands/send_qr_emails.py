from django.core.management.base import BaseCommand
from colleges.models import College
from core.utils import send_college_qr_email

class Command(BaseCommand):
    help = "Bulk email generated QR entry passes to all active colleges using professional HTML template"

    def handle(self, *args, **options):
        active_colleges = College.objects.filter(status=College.Status.ACTIVE)
        total = active_colleges.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING("No active colleges found to email passes."))
            return

        self.stdout.write(f"Found {total} active colleges. Starting bulk dispatch...")
        sent_count = 0
        failed_count = 0

        for college in active_colleges:
            try:
                send_college_qr_email(college, request=None, action="Bulk Email QR Pass")
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f"[{sent_count}/{total}] Emailed QR Pass to {college.college_name} ({college.email})"))
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"Failed to send email to {college.college_name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Bulk dispatch completed! Sent: {sent_count}, Failed: {failed_count}"))

