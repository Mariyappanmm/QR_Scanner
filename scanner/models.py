from django.db import models
from django.conf import settings
from colleges.models import College

class ScanLog(models.Model):
    class Status(models.TextChoices):
        ALLOWED = 'Allowed', 'Allowed'
        DENIED = 'Denied', 'Denied'

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name='scan_logs',
        verbose_name="College"
    )
    
    # 1 for first delegate, 2 for second, or 0/null/exceeded count for Denied entries
    scan_number = models.PositiveIntegerField(verbose_name="Scan Sequence Number")
    
    scan_time = models.DateTimeField(auto_now_add=True, verbose_name="Scan Time")
    
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scanned_logs',
        verbose_name="Scanned By"
    )
    
    scanner_device = models.CharField(max_length=255, verbose_name="Scanner Device/User-Agent")
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Scan Location")
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Scan Status"
    )
    
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")

    class Meta:
        ordering = ['-scan_time']

    def __str__(self):
        return f"{self.college.college_name} - {self.status} at {self.scan_time.strftime('%Y-%m-%d %H:%M')}"
