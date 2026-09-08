import openpyxl
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings
import io
import os

from core.decorators import admin_required
from colleges.models import College
from scanner.models import ScanLog
from core.models import AuditLog
from core.utils import generate_college_qr

# ReportLab imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

@login_required
@admin_required
def reports_home(request):
    """
    Renders the Reports landing dashboard showing available report downloads.
    """
    return render(request, 'reports/index.html')

@login_required
@admin_required
def export_attendance_excel(request):
    """
    Exports the complete audit-compliant attendance logs list to an Excel sheet.
    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="attendance_scan_logs.xlsx"'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Logs"
    
    headers = [
        "Scan Time", "College Name", "College Code", "Scan Sequence No", 
        "Verified By", "Device User Agent", "IP Address", "Scan Location", "Status", "Remarks"
    ]
    ws.append(headers)
    
    logs = ScanLog.objects.select_related('college', 'scanned_by').all().order_by('scan_time')
    for log in logs:
        ws.append([
            log.scan_time.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %I:%M:%S %p'),
            log.college.college_name,
            log.college.college_code,
            log.scan_number,
            log.scanned_by.username if log.scanned_by else "System",
            log.scanner_device,
            log.ip_address,
            log.location or "Entrance",
            log.status,
            log.remarks or ""
        ])
        
    wb.save(response)
    return response

@login_required
@admin_required
def export_rejected_excel(request):
    """
    Exports all Denied scan logs (potential intruders or over-limit delegate entries) to Excel.
    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="rejected_scan_attempts.xlsx"'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rejected Scans"
    
    headers = [
        "Scan Time", "College Name", "College Code", "Attempt No",
        "Operator", "Device Info", "IP Address", "Location", "Reason / Remarks"
    ]
    ws.append(headers)
    
    logs = ScanLog.objects.select_related('college', 'scanned_by').filter(status='Denied').order_by('-scan_time')
    for log in logs:
        ws.append([
            log.scan_time.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%d %I:%M:%S %p'),
            log.college.college_name,
            log.college.college_code,
            log.scan_number,
            log.scanned_by.username if log.scanned_by else "System",
            log.scanner_device,
            log.ip_address,
            log.location or "Entrance",
            log.remarks or ""
        ])
        
    wb.save(response)
    return response

@login_required
@admin_required
def export_volunteer_excel(request):
    """
    Exports performance metrics of all volunteer scanning operators.
    """
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="volunteer_scan_summary.xlsx"'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Volunteer Summary"
    
    headers = [
        "Volunteer Username", "Full Name", "Email Address", "Mobile",
        "Total Scans Handled", "Allowed Scans", "Denied Scans"
    ]
    ws.append(headers)
    
    # Query logs grouped by volunteer user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    volunteers = User.objects.annotate(
        total_scans=Count('scanned_logs'),
        allowed_scans=Count('scanned_logs', filter=Q(scanned_logs__status='Allowed')),
        denied_scans=Count('scanned_logs', filter=Q(scanned_logs__status='Denied'))
    ).filter(role=User.Role.VOLUNTEER)
    
    for v in volunteers:
        ws.append([
            v.username,
            f"{v.first_name} {v.last_name}".strip() or "N/A",
            v.email,
            v.mobile or "N/A",
            v.total_scans,
            v.allowed_scans,
            v.denied_scans
        ])
        
    wb.save(response)
    return response

@login_required
@admin_required
def export_pdf_report(request):
    """
    Generates a printable PDF event attendance summary report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=30
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F2937'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    # Header block
    story.append(Paragraph("Hackathon E-QR Delegate Attendance Report", title_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %I:%M %p')} | Control Center Administrator Summary", subtitle_style))
    
    # Statistics Summary Table
    story.append(Paragraph("Registration & Entry Metrics", h2_style))
    total_colleges = College.objects.count()
    total_passes = sum(c.max_pass for c in College.objects.all())
    used_passes = sum(c.used_pass for c in College.objects.all())
    remaining_passes = max(0, total_passes - used_passes)
    denied_scans = ScanLog.objects.filter(status='Denied').count()
    
    summary_data = [
        ["Metric description", "Count"],
        ["Invited Colleges", str(total_colleges)],
        ["Allocated Delegate Passes", str(total_passes)],
        ["Scanned (Checked In) Passes", str(used_passes)],
        ["Remaining Available Passes", str(remaining_passes)],
        ["Rejected Entry Attempts", str(denied_scans)],
    ]
    
    summary_table = Table(summary_data, colWidths=[250, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Recent Log Table
    story.append(Paragraph("Recent Scan Entries (Chronological Order)", h2_style))
    recent_logs = ScanLog.objects.select_related('college').all().order_by('-scan_time')[:15]
    
    log_data = [["Time", "College Code", "College Name", "Seq", "Status"]]
    for log in recent_logs:
        log_data.append([
            log.scan_time.astimezone(timezone.get_current_timezone()).strftime('%I:%M %p'),
            log.college.college_code,
            log.college.college_name[:30] + ('...' if len(log.college.college_name) > 30 else ''),
            str(log.scan_number),
            log.status
        ])
        
    log_table = Table(log_data, colWidths=[65, 80, 220, 45, 75])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    
    story.append(log_table)
    
    doc.build(story)
    
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_summary_report.pdf"'
    response.write(pdf_content)
    return response

@login_required
@admin_required
def export_pdf_passes(request):
    """
    Generates a bulk print-ready PDF booklet containing delegate pass sheets for all active colleges.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PassTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        alignment=1, # Center
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'PassSubtitle',
        fontName='Helvetica',
        fontSize=10,
        alignment=1, # Center
        textColor=colors.HexColor('#64748B'),
        spaceAfter=25
    )
    college_style = ParagraphStyle(
        'PassCollege',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=1, # Center
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=5
    )
    code_style = ParagraphStyle(
        'PassCode',
        fontName='Helvetica-Bold',
        fontSize=12,
        alignment=1, # Center
        textColor=colors.HexColor('#EF4444'),
        spaceAfter=30
    )
    details_label_style = ParagraphStyle(
        'PassDetailsLabel',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#475569')
    )
    details_value_style = ParagraphStyle(
        'PassDetailsVal',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1E293B')
    )
    
    colleges = College.objects.filter(status=College.Status.ACTIVE)
    
    if not colleges.exists():
        story.append(Paragraph("No active colleges registered to print passes.", title_style))
        doc.build(story)
        buffer.seek(0)
        return HttpResponse(buffer.getvalue(), content_type='application/pdf')
        
    for index, college in enumerate(colleges):
        if not college.qr_image:
            generate_college_qr(college)
            
        # Draw dotted cutout border lines using ReportLab Table
        story.append(Paragraph("HACKATHON DELEGATE PASS", title_style))
        story.append(Paragraph("Please display this QR code at the registration desk for delegate entry.", subtitle_style))
        story.append(Paragraph(college.college_name, college_style))
        story.append(Paragraph(f"COLLEGE CODE: {college.college_code}", code_style))
        
        # QR Code Image inclusion
        qr_path = college.qr_image.path
        if os.path.exists(qr_path):
            story.append(Image(qr_path, width=200, height=200))
        story.append(Spacer(1, 20))
        
        # Pass Details table info
        pass_info = [
            [Paragraph("Delegate Entry Limit:", details_label_style), Paragraph(f"{college.max_pass} Delegates", details_value_style)],
            [Paragraph("Secure Token ID:", details_label_style), Paragraph(str(college.qr_token), details_value_style)]
        ]
        info_table = Table(pass_info, colWidths=[150, 250])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(info_table)
        
        # Add PageBreak except for the last page
        if index < len(colleges) - 1:
            story.append(PageBreak())
            
    doc.build(story)
    
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="bulk_delegate_passes.pdf"'
    response.write(pdf_content)
    return response
