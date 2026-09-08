import qrcode
import io
import os
from django.core.files import File
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from email.mime.image import MIMEImage

def generate_college_qr(college):
    """
    Generates a secure QR Code image for a college instance.
    The QR contains ONLY the verification URL containing the unique secure UUID token.
    No human-readable college names, pass limits, or count information is stored inside the QR code data.
    """
    base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    # URL format matching the scanner verification page
    verify_url = f"{base_url.rstrip('/')}/scanner/verify/{college.qr_token}/"
    
    # Configure QR code generator
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error tolerance for camera scans
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    
    # Render QR code image
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")  # Corporate Dark Blue
    
    # Write image to in-memory byte buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    
    # Save the buffer into Django's file field
    file_name = f"qr_{college.college_code}.png"
    college.qr_image.save(file_name, File(buffer), save=False)
    college.save()

import email.policy

class RelatedEmailMultiAlternatives(EmailMultiAlternatives):
    def __init__(self, *args, **kwargs):
        self.related_attachments = []
        super().__init__(*args, **kwargs)
        
    def attach_related(self, content, maintype, subtype, cid):
        self.related_attachments.append((content, maintype, subtype, cid))
        
    def message(self, *, policy=email.policy.default):
        msg = super().message(policy=policy)
        if self.related_attachments:
            html_part = self._find_html_part(msg)
            if html_part:
                for content, maintype, subtype, cid in self.related_attachments:
                    html_part.add_related(
                        content,
                        maintype=maintype,
                        subtype=subtype,
                        cid=f"<{cid}>"
                    )
        return msg

    def _find_html_part(self, part):
        if part.get_content_type() == 'text/html':
            return part
        if part.is_multipart():
            for subpart in part.iter_parts():
                found = self._find_html_part(subpart)
                if found:
                    return found
        return None

def send_college_qr_email(college, request=None, action=None):
    """
    Sends a professional HTML cold email invitation with an embedded, inline QR visitor pass.
    """
    # 1. Ensure QR exists
    if not college.qr_image:
        generate_college_qr(college)

    # 2. Get event parameters from settings
    event_date = getattr(settings, 'EVENT_DATE', 'October 10, 2026')
    event_venue = getattr(settings, 'EVENT_VENUE', 'Yuvaasoft Technologies Innovation Center, Bangalore')
    event_time = getattr(settings, 'EVENT_TIME', '09:30 AM - 05:30 PM (IST)')
    outreach_name = getattr(settings, 'EVENT_OUTREACH_NAME', 'Anjali Sharma')
    outreach_email = getattr(settings, 'EVENT_OUTREACH_EMAIL', 'teamkdns19@gmail.com')
    outreach_phone = getattr(settings, 'EVENT_OUTREACH_PHONE', '+91 98765 43210')

    # 3. Build Subject
    subject = f"Your Invitation to Regional AI Summit 2.0 | Visitor Pass – {college.college_name}"

    # 4. Prepare context for template rendering
    snr_logo_url = getattr(settings, 'SNR_LOGO_URL', 'https://sriramakrishna.com/wp-content/uploads/2024/09/SNR.png.png')
    srit_logo_url = getattr(settings, 'SRIT_LOGO_URL', 'https://media.canva.com/v2/image-resize/format:PNG/height:285/quality:100/uri:ifs%3A%2F%2FM%2F4f84833d-30d1-493e-b6e6-f7c2f8b507ee/watermark:F/width:940?csig=AAAAAAAAAAAAAAAAAAAAAEACwmjE5JmHM_YEyZ4wFXe6qZbJ8M0vgKw95yUxvk0T&exp=1788859108&osig=AAAAAAAAAAAAAAAAAAAAAMXnNBZeWay8xfNq-Tq5llWvxryVfVzjSmo344i2v6Ga&signer=media-rpc&x-canva-quality=screen_3x')
    ras_logo_url = getattr(settings, 'RAS_LOGO_URL', 'https://wonderful-malabi-521a08.netlify.app/ras2.0_logo.png')
    yuvaasoft_logo_url = getattr(settings, 'YUVAASOFT_LOGO_URL', 'https://www.yuvaasoft.com/static/image/yuvaasoft_logo.png')
    registration_url = getattr(settings, 'REGISTRATION_URL', 'https://www.regionalaisummit.com/')
    visitor_pass_brochure_url = getattr(settings, 'VISITOR_PASS_BROCHURE_URL', 'https://www.regionalaisummit.com/')
    ras_benefits_brochure_url = getattr(settings, 'RAS_BENEFITS_BROCHURE_URL', 'https://www.regionalaisummit.com/')

    context = {
        'college': college,
        'COLLEGE_NAME': college.college_name,
        'PASS_TYPE': f"Institutional Group Pass ({college.max_pass} Visitors)" if college.max_pass > 1 else "Individual Visitor Pass",
        'QR_CODE_URL': 'cid:qr_code',
        'REGISTRATION_URL': registration_url,
        'VISITOR_PASS_BROCHURE_URL': visitor_pass_brochure_url,
        'RAS_BENEFITS_BROCHURE_URL': ras_benefits_brochure_url,
        'SNR_LOGO_URL': snr_logo_url,
        'SRIT_LOGO_URL': srit_logo_url,
        'RAS_LOGO_URL': ras_logo_url,
        'YUVAASOFT_LOGO_URL': yuvaasoft_logo_url,
        'event_date': event_date,
        'event_venue': event_venue,
        'event_time': event_time,
        'outreach_name': outreach_name,
        'outreach_email': outreach_email,
        'outreach_phone': outreach_phone,
    }

    # 5. Render HTML and generate text fallback
    html_content = render_to_string('emails/visitor_pass_email.html', context)

    # 6. Create EmailMessage
    email = RelatedEmailMultiAlternatives(
        subject=subject,
        body=html_content,  # Force HTML content as main body to prevent raw template display issues
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[college.email]
    )
    email.content_subtype = "html"  # Set primary content type to HTML
    email.attach_alternative(html_content, "text/html")

    # 7. Embed QR image inline
    with open(college.qr_image.path, 'rb') as f:
        email.attach_related(f.read(), "image", "png", "qr_code")

    # 8. Send the email
    email.send()

    # 9. Create Audit Log
    from core.models import AuditLog
    user = request.user if (request and request.user and request.user.is_authenticated) else None
    ip_address = request.META.get('REMOTE_ADDR') if request else '127.0.0.1'
    
    if not action:
        action = "Email QR Pass" if request else "Bulk Email QR Pass"
        
    AuditLog.objects.create(
        user=user,
        action=action,
        details=f"Sent professional HTML QR Pass email to {college.college_name} ({college.email})",
        ip_address=ip_address
    )

