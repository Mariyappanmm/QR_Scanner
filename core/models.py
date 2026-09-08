from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="User"
    )
    action = models.CharField(max_length=255, verbose_name="Action Performed")
    details = models.TextField(verbose_name="Activity Details")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP Address")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else "System"
        return f"{username} - {self.action} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
