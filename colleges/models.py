import uuid
from django.db import models

class College(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    college_name = models.CharField(max_length=255, verbose_name="College Name")
    college_code = models.CharField(max_length=50, unique=True, verbose_name="College Code")
    email = models.EmailField(verbose_name="Email Address")
    
    # Secure QR Token identifier (never exposed in plaintext as college name in QR)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="QR Secure Token")
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="QR Code Image")
    
    max_pass = models.PositiveIntegerField(default=2, verbose_name="Maximum Passes (Delegates)")
    used_pass = models.PositiveIntegerField(default=0, verbose_name="Used Passes")
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        ordering = ['-created_at']

    def remaining_passes(self):
        return max(0, self.max_pass - self.used_pass)

    def is_limit_reached(self):
        return self.used_pass >= self.max_pass

    def __str__(self):
        return f"{self.college_name} ({self.college_code})"

import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

@receiver(post_delete, sender=College)
def delete_qr_image(sender, instance, **kwargs):
    """
    Automatically deletes the corresponding QR code image from the filesystem
    when a College instance is deleted.
    """
    if instance.qr_image:
        if os.path.exists(instance.qr_image.path):
            try:
                os.remove(instance.qr_image.path)
            except Exception:
                pass

@receiver(pre_save, sender=College)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Automatically deletes the old QR code image file from the disk
    when a College object is updated with a new QR code image.
    """
    if not instance.pk:
        return False

    try:
        old_file = College.objects.get(pk=instance.pk).qr_image
    except College.DoesNotExist:
        return False

    new_file = instance.qr_image
    if not old_file == new_file:
        if old_file and os.path.exists(old_file.path):
            try:
                os.remove(old_file.path)
            except Exception:
                pass
