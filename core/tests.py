from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
import uuid
import tempfile
import os

from colleges.models import College
from scanner.models import ScanLog
from core.models import AuditLog

User = get_user_model()

@override_settings(MEDIA_ROOT=os.path.join(tempfile.gettempdir(), 'test_media'))
class HackathonQRPassTests(TestCase):
    def setUp(self):
        # 1. Create User Accounts with Roles
        self.super_admin = User.objects.create_user(
            username="test_super",
            email="super@event.com",
            password="password123",
            role=User.Role.SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            username="test_admin",
            email="admin@event.com",
            password="password123",
            role=User.Role.ADMIN
        )
        self.volunteer = User.objects.create_user(
            username="test_volunteer",
            email="john@event.com",
            password="password123",
            role=User.Role.VOLUNTEER
        )

        # 2. Create a test college
        self.college = College.objects.create(
            college_name="PSG College of Technology",
            college_code="PSG01",
            email="kannan@psg.edu",
            max_pass=2,
            used_pass=0,
            status=College.Status.ACTIVE
        )
        
        # 3. Create inactive test college
        self.inactive_college = College.objects.create(
            college_name="Deactivated Institute",
            college_code="DEAC01",
            email="staff@deac.edu",
            max_pass=2,
            used_pass=0,
            status=College.Status.INACTIVE
        )

        # Clients for testing
        self.client = Client()

    def test_college_pass_utilization_logic(self):
        """
        Tests College model helper properties.
        """
        self.assertEqual(self.college.remaining_passes(), 2)
        self.assertFalse(self.college.is_limit_reached())

        self.college.used_pass = 2
        self.assertTrue(self.college.is_limit_reached())
        self.assertEqual(self.college.remaining_passes(), 0)

    def test_role_based_permissions(self):
        """
        Verifies role-based access control (RBAC).
        Volunteers should NOT access dashboard or colleges, but can access scanner.
        """
        dashboard_url = reverse('dashboard')
        colleges_url = reverse('college_list')
        scanner_url = reverse('scanner_home')

        # Scenario A: Anonymous User (should redirect to login)
        response = self.client.get(dashboard_url)
        self.assertRedirects(response, f"{reverse('login')}?next={dashboard_url}")
        
        response = self.client.get(scanner_url)
        self.assertRedirects(response, f"{reverse('login')}?next={scanner_url}")

        # Scenario B: Volunteer User (No access to dashboard/colleges, yes to scanner)
        self.client.login(username="test_volunteer", password="password123")
        
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 403) # Forbidden for Volunteer
        
        response = self.client.get(colleges_url)
        self.assertEqual(response.status_code, 403) # Forbidden for Volunteer
        
        response = self.client.get(scanner_url)
        self.assertEqual(response.status_code, 200) # Allowed for Volunteer
        
        self.client.logout()

        # Scenario C: Admin User (Access to everything)
        self.client.login(username="test_admin", password="password123")
        
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(colleges_url)
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(scanner_url)
        self.assertEqual(response.status_code, 200)

    def test_scan_verification_api(self):
        """
        Tests the atomic scan validation API endpoint:
        1st Scan -> Allowed
        2nd Scan -> Allowed
        3rd Scan -> Denied (Limit Exceeded)
        """
        self.client.login(username="test_volunteer", password="password123")
        scan_api_url = reverse('api_scan')
        
        # 1. First Scan (Allowed)
        response = self.client.post(scan_api_url, {'token': str(self.college.qr_token)})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'Allowed')
        self.assertEqual(json_data['scan_number'], 1)
        self.assertEqual(json_data['remaining_passes'], 1)

        # 2. Second Scan (Allowed)
        response = self.client.post(scan_api_url, {'token': str(self.college.qr_token)})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'Allowed')
        self.assertEqual(json_data['scan_number'], 2)
        self.assertEqual(json_data['remaining_passes'], 0)

        # 3. Third Scan (Denied)
        response = self.client.post(scan_api_url, {'token': str(self.college.qr_token)})
        self.assertEqual(response.status_code, 200) # API returns status code 200 but status label 'Denied'
        json_data = response.json()
        self.assertEqual(json_data['status'], 'Denied')
        self.assertEqual(json_data['scan_number'], 3)
        self.assertEqual(json_data['remaining_passes'], 0)

        # Check database logs count
        self.assertEqual(ScanLog.objects.filter(college=self.college).count(), 3)
        self.assertEqual(ScanLog.objects.filter(college=self.college, status='Allowed').count(), 2)
        self.assertEqual(ScanLog.objects.filter(college=self.college, status='Denied').count(), 1)

    def test_scan_inactive_college_api(self):
        """
        Tests that scanning an inactive college pass is Denied.
        """
        self.client.login(username="test_volunteer", password="password123")
        scan_api_url = reverse('api_scan')
        
        response = self.client.post(scan_api_url, {'token': str(self.inactive_college.qr_token)})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'Denied')
        self.assertEqual(json_data['remarks'], 'College Status Inactive')

    def test_scan_invalid_token_api(self):
        """
        Tests that scanning a random invalid token returns 404 error.
        """
        self.client.login(username="test_volunteer", password="password123")
        scan_api_url = reverse('api_scan')
        
        fake_uuid = uuid.uuid4()
        response = self.client.post(scan_api_url, {'token': str(fake_uuid)})
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'Denied')
        self.assertEqual(json_data['error_message'], 'Invalid QR Token - College not found')

    def test_bulk_email_qr_passes_view(self):
        """
        Tests the bulk email dispatch view function.
        Checks that emails are sent for all active colleges.
        """
        from django.core import mail
        self.client.login(username="test_admin", password="password123")
        
        url = reverse('colleges_bulk_email_qr')
        response = self.client.get(url)
        
        # Verify redirect back to list
        self.assertRedirects(response, reverse('college_list'))
        
        # Verify that an email was sent for the active college
        # Note: self.inactive_college has status INACTIVE so it shouldn't get an email.
        # Total active colleges = 1 (self.college). So outbox size should be 1.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"Your Invitation to Regional AI Summit 2.0 | Visitor Pass – {self.college.college_name}")
        self.assertEqual(mail.outbox[0].to, [self.college.email])

    def test_college_create_view_no_automatic_email(self):
        """
        Tests that creating a college via the view generates a QR code
        but does NOT send an email automatically.
        """
        from django.core import mail
        from core.models import AuditLog
        
        self.client.login(username="test_admin", password="password123")
        
        # Clear outbox first
        mail.outbox = []
        
        create_url = reverse('college_create')
        data = {
            'college_name': 'New Test College',
            'college_code': 'NEW01',
            'email': 'jane@newcollege.edu',
            'max_pass': 3,
            'status': College.Status.ACTIVE
        }
        
        response = self.client.post(create_url, data)
        
        # Verify it redirects to college_detail
        new_college = College.objects.get(college_code='NEW01')
        self.assertRedirects(response, reverse('college_detail', kwargs={'pk': new_college.pk}))
        
        # Verify QR code is generated
        self.assertTrue(bool(new_college.qr_image))
        self.assertTrue(new_college.qr_image.name.endswith('.png'))
        
        # Verify that NO email was sent automatically
        self.assertEqual(len(mail.outbox), 0)
        
        # Verify AuditLog entry was created for the creation event
        audit_log = AuditLog.objects.filter(action="Create College").first()
        self.assertIsNotNone(audit_log)
        self.assertIn('New Test College', audit_log.details)

    def test_college_delete_deletes_qr_image_file(self):
        """
        Tests that deleting a college also deletes its QR code image file from disk.
        """
        import os
        
        # 1. Create a college
        college = College.objects.create(
            college_name="Delete Test College",
            college_code="DEL01",
            email="delete@college.edu",
            max_pass=2,
            used_pass=0,
            status=College.Status.ACTIVE
        )
        
        # 2. Generate QR code
        from core.utils import generate_college_qr
        generate_college_qr(college)
        
        # Verify file exists
        file_path = college.qr_image.path
        self.assertTrue(os.path.exists(file_path))
        
        # 3. Delete the college record
        college.delete()
        
        # Verify file is deleted from disk
        self.assertFalse(os.path.exists(file_path))

