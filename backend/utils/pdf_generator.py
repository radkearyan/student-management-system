import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that tracks total pages to render 'Page X of Y' in the running footer."""
    footer_text = "Student Management System — Official Academic Record"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(36, 20, self.footer_text)
        self.drawRightString(595.27 - 36, 20, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 30, 595.27 - 36, 30)
        self.restoreState()


class PDFGenerator:
    """Helper class to compile academic documents and payment receipts into PDFs."""
    
    @staticmethod
    def generate_hall_ticket_pdf(ticket_data):
        return True, b"%PDF-1.4 simulated binary hall ticket PDF data stream"

    @staticmethod
    def generate_marksheet_pdf(marksheet_data):
        return True, b"%PDF-1.4 simulated binary marksheet PDF data stream"

    @staticmethod
    def generate_attendance_pdf(logs, metadata=None):
        """
        Generates a professionally formatted academic PDF report of class attendance logs.
        Returns: io.BytesIO containing the generated PDF binary stream.
        """
        if metadata is None:
            metadata = {}

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        
        # Typography styles
        title_inst = ParagraphStyle(
            'InstTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#0F172A'),
            alignment=1
        )
        sub_title = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#2563EB'),
            alignment=1
        )
        meta_val = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#0F172A')
        )
        tbl_header = ParagraphStyle(
            'TblHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=1
        )
        cell_text = ParagraphStyle(
            'CellText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        cell_center = ParagraphStyle(
            'CellCenter',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B'),
            alignment=1
        )
        cell_present = ParagraphStyle(
            'CellPresent',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#15803D'),
            alignment=1
        )
        cell_absent = ParagraphStyle(
            'CellAbsent',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#DC2626'),
            alignment=1
        )

        elements = []

        # 1. Header Section
        elements.append(Paragraph("STUDENT MANAGEMENT SYSTEM", title_inst))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph("OFFICIAL CLASS ATTENDANCE REGISTER", sub_title))
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

        # 2. Metadata & Filter Details
        dept_text = metadata.get('department', 'All Departments')
        date_text = metadata.get('date', 'All Recorded Dates')
        gen_by = metadata.get('generated_by', 'Academic Administrator')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        total_count = len(logs)
        present_count = sum(1 for l in logs if l.get('status') == 'Present')
        absent_count = sum(1 for l in logs if l.get('status') == 'Absent')
        rate = f"{(present_count / total_count * 100):.1f}%" if total_count > 0 else "0.0%"

        # Info & Summary Grid
        meta_table_data = [
            [
                Paragraph(f"<b>Department:</b> {dept_text}", meta_val),
                Paragraph(f"<b>Date:</b> {date_text}", meta_val),
                Paragraph(f"<b>Total Records:</b> {total_count}", meta_val),
                Paragraph(f"<b>Attendance Rate:</b> {rate}", meta_val)
            ],
            [
                Paragraph(f"<b>Generated By:</b> {gen_by}", meta_val),
                Paragraph(f"<b>Printed On:</b> {now_str}", meta_val),
                Paragraph(f"<b>Present:</b> <font color='#15803D'><b>{present_count}</b></font>", meta_val),
                Paragraph(f"<b>Absent:</b> <font color='#DC2626'><b>{absent_count}</b></font>", meta_val)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[140, 130, 120, 133])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # 3. Attendance Table
        col_widths = [26, 75, 120, 132, 70, 55, 45]
        header_row = [
            Paragraph("#", tbl_header),
            Paragraph("Student ID", tbl_header),
            Paragraph("Student Name", tbl_header),
            Paragraph("Department", tbl_header),
            Paragraph("Date", tbl_header),
            Paragraph("Status", tbl_header),
            Paragraph("Method", tbl_header)
        ]

        table_data = [header_row]

        if logs:
            for idx, log in enumerate(logs, 1):
                status_p = Paragraph("PRESENT", cell_present) if log.get('status') == 'Present' else Paragraph("ABSENT", cell_absent)
                row = [
                    Paragraph(str(idx), cell_center),
                    Paragraph(str(log.get('student_id', '-')), cell_text),
                    Paragraph(str(log.get('name', '-')), cell_text),
                    Paragraph(str(log.get('department', '-')), cell_text),
                    Paragraph(str(log.get('date', '-')), cell_center),
                    status_p,
                    Paragraph(str(log.get('method', 'Manual')), cell_center)
                ]
                table_data.append(row)
        else:
            empty_row = [
                Paragraph("-", cell_center),
                Paragraph("No records found", cell_text),
                Paragraph("-", cell_text),
                Paragraph("-", cell_text),
                Paragraph("-", cell_center),
                Paragraph("-", cell_center),
                Paragraph("-", cell_center)
            ]
            table_data.append(empty_row)

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]

        # Alternating row colors
        for r_idx in range(1, len(table_data)):
            bg = colors.HexColor('#FFFFFF') if r_idx % 2 != 0 else colors.HexColor('#F8FAFC')
            t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

        table.setStyle(TableStyle(t_style))
        elements.append(table)
        elements.append(Spacer(1, 24))

        # 4. Verification Sign-off Box
        sig_data = [
            [
                Paragraph("<b>Faculty / Register In-charge</b><br/><br/><br/>___________________________________<br/>Signature & Date", meta_val),
                Paragraph("<b>Head of Department / Academic Dean</b><br/><br/><br/>___________________________________<br/>Signature & Seal", meta_val)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[260, 263])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(KeepTogether([sig_table]))

        # Build document
        NumberedCanvas.footer_text = "Student Management System — Official Academic Attendance Registry"
        doc.build(elements, canvasmaker=NumberedCanvas)
        buf.seek(0)
        return buf

    @staticmethod
    def generate_fee_receipt_pdf(receipt):
        """
        Generates a formatted academic PDF report of a fee payment receipt.
        Returns: io.BytesIO containing the generated PDF binary stream.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Typography styles
        title_style = ParagraphStyle(
            'ReceiptInstTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#002D62')
        )
        address_style = ParagraphStyle(
            'ReceiptInstAddress',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#475569')
        )
        motto_style = ParagraphStyle(
            'ReceiptInstMotto',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#B8860B')
        )
        banner_style = ParagraphStyle(
            'ReceiptBanner',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=colors.white,
            alignment=1
        )
        meta_val = ParagraphStyle(
            'ReceiptMetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#0F172A')
        )
        tbl_header = ParagraphStyle(
            'ReceiptTblHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#002D62'),
            alignment=0
        )
        cell_text = ParagraphStyle(
            'ReceiptCellText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1E293B')
        )
        cell_bold = ParagraphStyle(
            'ReceiptCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#002D62')
        )

        elements = []

        # 1. Header with Logo & Title
        logo_path = os.path.abspath('frontend/assets/images/svpcet_logo.jpg')
        has_logo = os.path.exists(logo_path)

        header_text = [
            Paragraph("STUDENT MANAGEMENT SYSTEM", title_style),
            Paragraph("Gavsi Manapur, Wardha Road, Nagpur, Maharashtra 441108", address_style),
            Paragraph("Motto: <i>\"Arise and Shine\"</i>", motto_style),
            Spacer(1, 4),
            Table(
                [[Paragraph("OFFICIAL FEE PAYMENT RECEIPT", banner_style)]],
                colWidths=[240],
                style=[
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#002D62')),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]
            )
        ]

        if has_logo:
            img = Image(logo_path, width=65, height=65)
            header_table = Table([[img, header_text]], colWidths=[80, 443])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(header_table)
        else:
            elements.extend(header_text)

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#002D62"), spaceAfter=10))

        # 2. Receipt Meta Details (Receipt No, Date, Txn ID, Method)
        rec_no = receipt.get('receipt_no', f"REC-{receipt.get('fee_id', '001')}")
        pay_date = str(receipt.get('payment_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        txn_id = receipt.get('txn_id', 'TXN-ONLINE')
        method = receipt.get('payment_method', 'Online NetBanking / Card Gateway')

        meta_data = [
            [
                Paragraph(f"<b>Receipt No:</b> <font color='#002D62'>{rec_no}</font>", meta_val),
                Paragraph(f"<b>Payment Date:</b> {pay_date}", meta_val),
            ],
            [
                Paragraph(f"<b>Transaction ID:</b> <font color='#002D62'>{txn_id}</font>", meta_val),
                Paragraph(f"<b>Payment Method:</b> {method}", meta_val),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[260, 263])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # 3. Student Details Block
        stu_name = receipt.get('name', 'N/A')
        stu_id = receipt.get('student_id', 'N/A')
        dept = receipt.get('department', 'General')
        course = receipt.get('course', f"B.Tech {dept}")
        sem = receipt.get('semester', 1)

        stu_data = [
            [
                Paragraph(f"<b>Student Name:</b> {stu_name}", meta_val),
                Paragraph(f"<b>Student ID (Roll No):</b> {stu_id}", meta_val),
            ],
            [
                Paragraph(f"<b>Department:</b> {dept}", meta_val),
                Paragraph(f"<b>Academic Program:</b> {course} (Sem {sem})", meta_val),
            ]
        ]
        stu_table = Table(stu_data, colWidths=[260, 263])
        stu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(stu_table)
        elements.append(Spacer(1, 14))

        # 4. Fee Itemized Table
        amount = float(receipt.get('amount', 0))
        fee_data = [
            [
                Paragraph("<b>Sr. No.</b>", tbl_header),
                Paragraph("<b>Description of Account Head</b>", tbl_header),
                Paragraph("<b>Particulars</b>", tbl_header),
                Paragraph("<b>Amount (INR)</b>", tbl_header),
            ],
            [
                Paragraph("1", cell_text),
                Paragraph(receipt.get('account_head', 'Tuition Fee Account'), cell_text),
                Paragraph("Semester Academic Tuition Fee Settlement", cell_text),
                Paragraph(f"₹ {amount:,.2f}", cell_bold),
            ],
            [
                Paragraph("", cell_text),
                Paragraph("<b>Total Amount Paid (INR)</b>", cell_bold),
                Paragraph("<b>PAID IN FULL (ONLINE)</b>", cell_bold),
                Paragraph(f"<b>₹ {amount:,.2f}</b>", cell_bold),
            ]
        ]
        fee_table = Table(fee_data, colWidths=[45, 160, 200, 118])
        fee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#002D62')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#EFF6FF')),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor('#002D62')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(fee_table)
        elements.append(Spacer(1, 14))

        # 5. Status Banner
        status_banner = Table(
            [[
                Paragraph("<b>Payment Status:</b> <font color='#15803D'><b>VERIFIED & RECEIVED</b></font> &nbsp;|&nbsp; <i>This is an official system-generated electronic receipt.</i>", meta_val)
            ]],
            colWidths=[523],
            style=[
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDF4')),
                ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#86EFAC')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]
        )
        elements.append(status_banner)
        elements.append(Spacer(1, 30))

        # 6. Sign-off & Electronic Stamp
        sig_data = [
            [
                Paragraph("<b>Student's Copy</b><br/><br/><br/>____________________________<br/>Student Acknowledgement", meta_val),
                Paragraph("<font color='#1D4ED8'><b>[ E-PAID VERIFIED ]</b></font><br/><br/><br/>____________________________<br/>Accounts Officer / Cashier", meta_val)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[260, 263])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(KeepTogether([sig_table]))

        # Build document with NumberedCanvas
        NumberedCanvas.footer_text = "Student Management System — Official Fee Payment Receipt"
        doc.build(elements, canvasmaker=NumberedCanvas)
        buf.seek(0)
        return buf

    @staticmethod
    def generate_student_list_pdf(students, metadata=None):
        if metadata is None:
            metadata = {}

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        title_inst = ParagraphStyle('InstTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor('#0F172A'), alignment=1)
        sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor('#2563EB'), alignment=1)
        meta_val = ParagraphStyle('MetaVal', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#0F172A'))
        tbl_header = ParagraphStyle('TblHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white, alignment=1)
        cell_text = ParagraphStyle('CellText', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#1E293B'))
        cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#1E293B'), alignment=1)

        elements = []
        elements.append(Paragraph("STUDENT MANAGEMENT SYSTEM", title_inst))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph("OFFICIAL STUDENT ENROLLMENT REPORT", sub_title))
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

        dept_text = metadata.get('department', 'All Departments')
        course_text = metadata.get('course', 'All Courses')
        gen_by = metadata.get('generated_by', 'Administrator')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        meta_table_data = [
            [
                Paragraph(f"<b>Department:</b> {dept_text}", meta_val),
                Paragraph(f"<b>Course:</b> {course_text}", meta_val),
                Paragraph(f"<b>Total Students:</b> {len(students)}", meta_val),
            ],
            [
                Paragraph(f"<b>Generated By:</b> {gen_by}", meta_val),
                Paragraph(f"<b>Printed On:</b> {now_str}", meta_val),
                Paragraph(f"<b>Status:</b> Active Directory", meta_val)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[175, 175, 173])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        col_widths = [26, 75, 120, 110, 132, 60]
        header_row = [
            Paragraph("#", tbl_header),
            Paragraph("Student ID", tbl_header),
            Paragraph("Student Name", tbl_header),
            Paragraph("Department", tbl_header),
            Paragraph("Email Address", tbl_header),
            Paragraph("Gender", tbl_header)
        ]
        table_data = [header_row]

        if students:
            for idx, s in enumerate(students, 1):
                row = [
                    Paragraph(str(idx), cell_center),
                    Paragraph(str(s.get('student_id', '-')), cell_text),
                    Paragraph(str(s.get('name', '-')), cell_text),
                    Paragraph(str(s.get('department', '-')), cell_text),
                    Paragraph(str(s.get('email', '-')), cell_text),
                    Paragraph(str(s.get('gender', '-')), cell_center)
                ]
                table_data.append(row)
        else:
            table_data.append([Paragraph("-", cell_center), Paragraph("No student records found", cell_text), Paragraph("-", cell_text), Paragraph("-", cell_text), Paragraph("-", cell_text), Paragraph("-", cell_center)])

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]
        for r_idx in range(1, len(table_data)):
            bg = colors.HexColor('#FFFFFF') if r_idx % 2 != 0 else colors.HexColor('#F8FAFC')
            t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

        table.setStyle(TableStyle(t_style))
        elements.append(table)

        NumberedCanvas.footer_text = "Student Management System — Official Student Enrollment Directory"
        doc.build(elements, canvasmaker=NumberedCanvas)
        buf.seek(0)
        return buf

    @staticmethod
    def generate_marks_report_pdf(marks_list, metadata=None):
        if metadata is None:
            metadata = {}

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        title_inst = ParagraphStyle('InstTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor('#0F172A'), alignment=1)
        sub_title = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=colors.HexColor('#2563EB'), alignment=1)
        meta_val = ParagraphStyle('MetaVal', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#0F172A'))
        tbl_header = ParagraphStyle('TblHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white, alignment=1)
        cell_text = ParagraphStyle('CellText', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#1E293B'))
        cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#1E293B'), alignment=1)
        cell_pass = ParagraphStyle('CellPass', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#15803D'), alignment=1)
        cell_fail = ParagraphStyle('CellFail', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#DC2626'), alignment=1)

        elements = []
        elements.append(Paragraph("STUDENT MANAGEMENT SYSTEM", title_inst))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph("EXAMINATION MARKS & ACADEMIC RESULT REPORT", sub_title))
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

        sub_text = metadata.get('subject', 'All Subjects')
        status_text = metadata.get('status', 'All Statuses')
        gen_by = metadata.get('generated_by', 'Academic Controller')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        meta_table_data = [
            [
                Paragraph(f"<b>Subject / Exam:</b> {sub_text}", meta_val),
                Paragraph(f"<b>Status Filter:</b> {status_text}", meta_val),
                Paragraph(f"<b>Total Entries:</b> {len(marks_list)}", meta_val),
            ],
            [
                Paragraph(f"<b>Generated By:</b> {gen_by}", meta_val),
                Paragraph(f"<b>Printed On:</b> {now_str}", meta_val),
                Paragraph(f"<b>Academic Board:</b> Certified", meta_val)
            ]
        ]
        meta_table = Table(meta_table_data, colWidths=[175, 175, 173])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        col_widths = [26, 75, 110, 110, 55, 50, 45, 52]
        header_row = [
            Paragraph("#", tbl_header),
            Paragraph("Student ID", tbl_header),
            Paragraph("Student Name", tbl_header),
            Paragraph("Subject", tbl_header),
            Paragraph("Obtained", tbl_header),
            Paragraph("Max", tbl_header),
            Paragraph("Grade", tbl_header),
            Paragraph("Status", tbl_header)
        ]
        table_data = [header_row]

        if marks_list:
            for idx, m in enumerate(marks_list, 1):
                status_str = str(m.get('status', 'PASS')).upper()
                status_p = Paragraph(status_str, cell_pass) if status_str == 'PASS' else Paragraph(status_str, cell_fail)
                row = [
                    Paragraph(str(idx), cell_center),
                    Paragraph(str(m.get('student_id', '-')), cell_text),
                    Paragraph(str(m.get('name', '-')), cell_text),
                    Paragraph(str(m.get('subject', '-')), cell_text),
                    Paragraph(str(m.get('marks_obtained', 0)), cell_center),
                    Paragraph(str(m.get('max_marks', 100)), cell_center),
                    Paragraph(str(m.get('grade', '-')), cell_center),
                    status_p
                ]
                table_data.append(row)
        else:
            table_data.append([Paragraph("-", cell_center), Paragraph("No examination mark records found", cell_text), Paragraph("-", cell_text), Paragraph("-", cell_text), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center), Paragraph("-", cell_center)])

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]
        for r_idx in range(1, len(table_data)):
            bg = colors.HexColor('#FFFFFF') if r_idx % 2 != 0 else colors.HexColor('#F8FAFC')
            t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

        table.setStyle(TableStyle(t_style))
        elements.append(table)

        NumberedCanvas.footer_text = "Student Management System — Official Examination Result Registry"
        doc.build(elements, canvasmaker=NumberedCanvas)
        buf.seek(0)
        return buf

