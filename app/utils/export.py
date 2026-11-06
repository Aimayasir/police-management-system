import io
import csv
from datetime import datetime, date
from flask import Response
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def export_to_csv(headers, rows, filename='export.csv'):
    """Generate and return a downloadable CSV response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    
    csv_bytes = output.getvalue().encode('utf-8-sig')
    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


def export_to_pdf(title, headers, rows, filename='export.pdf', orientation='portrait'):
    """Generate official tabular PDF report using ReportLab with authentic Punjab Police header and footer."""
    buffer = io.BytesIO()
    pagesize = landscape(letter) if orientation == 'landscape' else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=30,
        rightMargin=30,
        topMargin=26,
        bottomMargin=26
    )

    styles = getSampleStyleSheet()
    gov_header_style = ParagraphStyle(
        'GovHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=1,
        textColor=colors.HexColor('#1e293b')
    )
    station_sub_style = ParagraphStyle(
        'StationSub',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#475569')
    )
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#b91c1c'),
        spaceAfter=4
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    header_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    footer_text_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#64748b')
    )
    sign_style = ParagraphStyle(
        'SignText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []
    # 1. Punjab Police Header
    elements.append(Paragraph("GOVERNMENT OF THE PUNJAB — POLICE DEPARTMENT", gov_header_style))
    elements.append(Paragraph("POLICE STATION CIVIL LINES, LAHORE DIVISION", station_sub_style))
    elements.append(Paragraph(f"OFFICIAL RECORD REPORT: {title.upper()}", title_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=8))

    # 2. Table of Records
    table_data = [[Paragraph(str(h), header_style) for h in headers]]
    for row in rows:
        row_cells = []
        for cell in row:
            text = str(cell) if cell is not None else ''
            row_cells.append(Paragraph(text, cell_style))
        table_data.append(row_cells)

    if len(table_data) == 1:
        table_data.append([Paragraph("No records found.", cell_style)] + [Paragraph("", cell_style)] * (len(headers) - 1))

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(table)
    elements.append(Spacer(1, 14))

    # 3. Footer with Date and Signatures
    gen_time_str = datetime.utcnow().strftime('%d-%b-%Y at %H:%M UTC')
    sig_width = 360 if orientation == 'landscape' else 270
    footer_table = Table([
        [
            Paragraph(f"<b>Certified Law Enforcement Dispatch</b><br/>Generated: {gen_time_str}<br/>Official Record &bull; Confidential &bull; Punjab Police", footer_text_style),
            Paragraph("____________________________<br/><b>Station House Officer (SHO)</b><br/>Civil Lines Police Station, Lahore", sign_style)
        ]
    ], colWidths=[sig_width, sig_width])
    elements.append(KeepTogether(footer_table))

    doc.build(elements)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


def generate_fir_pdf(fir):
    """
    Generate an official printable First Information Report (FIR) PDF
    with authentic police station header, legal sections (PPC), complainant details,
    narrative of occurrence, and signature blocks under Section 154 Cr.P.C.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    header_title_style = ParagraphStyle(
        'FIRHeader',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor('#1e293b')
    )
    station_sub_style = ParagraphStyle(
        'FIRSub',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#475569')
    )
    section_title = ParagraphStyle(
        'FIRSec',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=4,
        spaceBefore=8
    )
    body_text = ParagraphStyle(
        'FIRBody',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )
    bold_text = ParagraphStyle(
        'FIRBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    elements = []

    # 1. Police Station Header
    st_name = fir.station.name if fir.station else "Police Station Civil Lines"
    st_dist = fir.station.district if fir.station else "Lahore District"
    st_prov = fir.station.state if fir.station else "Punjab"

    elements.append(Paragraph(f"GOVERNMENT OF THE {st_prov.upper()} - POLICE DEPARTMENT", header_title_style))
    elements.append(Paragraph(f"{st_name.upper()}, {st_dist.upper()}", header_title_style))
    elements.append(Paragraph("FIRST INFORMATION REPORT (F.I.R.)", ParagraphStyle('FIRTag', fontName='Helvetica-Bold', fontSize=12, leading=15, alignment=1, textColor=colors.HexColor('#b91c1c'))))
    elements.append(Paragraph("(Under Section 154 Code of Criminal Procedure - Cr.P.C.)", station_sub_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceAfter=8))

    # 2. Key Metadata Grid
    meta_data = [
        [
            Paragraph("<b>FIR Number:</b>", bold_text), Paragraph(fir.fir_number, bold_text),
            Paragraph("<b>Police Station:</b>", bold_text), Paragraph(st_name, body_text)
        ],
        [
            Paragraph("<b>Date & Time Reported:</b>", bold_text),
            Paragraph(fir.created_at.strftime('%d-%b-%Y %H:%M') if fir.created_at else '-', body_text),
            Paragraph("<b>Date of Occurrence:</b>", bold_text),
            Paragraph(fir.incident_date_time.strftime('%d-%b-%Y %H:%M') if fir.incident_date_time else '-', body_text)
        ],
        [
            Paragraph("<b>Offense Classification:</b>", bold_text),
            Paragraph(fir.crime_type.name if fir.crime_type else 'General Offense', body_text),
            Paragraph("<b>Applicable Laws (PPC):</b>", bold_text),
            Paragraph(f"<b>{fir.crime_type.relevant_sections if (fir.crime_type and fir.crime_type.relevant_sections) else 'Section 154 CrPC'}</b>", ParagraphStyle('PPC', parent=bold_text, textColor=colors.HexColor('#b91c1c')))
        ],
        [
            Paragraph("<b>Cognizable Offense:</b>", bold_text),
            Paragraph("YES (Section 154 CrPC Cognizable)" if fir.is_cognizable else "NO", body_text),
            Paragraph("<b>Investigation Status:</b>", bold_text),
            Paragraph(fir.status_rel.name if fir.status_rel else 'Registered', bold_text)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[130, 140, 120, 150])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc'))
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))

    # 3. Complainant / Informant Details
    elements.append(Paragraph("1. COMPLAINANT / INFORMANT DETAILS", section_title))
    comp_name = fir.complainant.full_name if fir.complainant else "The State / Police Suo Moto"
    comp_cnic = fir.complainant.national_id if (fir.complainant and fir.complainant.national_id) else "N/A"
    comp_phone = fir.complainant.phone if (fir.complainant and fir.complainant.phone) else "-"
    comp_addr = fir.complainant.address if fir.complainant else "Territorial Jurisdiction"

    comp_data = [
        [Paragraph("<b>Name of Informant:</b>", bold_text), Paragraph(comp_name, body_text),
         Paragraph("<b>National ID / CNIC:</b>", bold_text), Paragraph(comp_cnic, body_text)],
        [Paragraph("<b>Contact Phone:</b>", bold_text), Paragraph(comp_phone, body_text),
         Paragraph("<b>Permanent Address:</b>", bold_text), Paragraph(comp_addr, body_text)]
    ]
    comp_table = Table(comp_data, colWidths=[130, 140, 120, 150])
    comp_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(comp_table)
    elements.append(Spacer(1, 8))

    # 4. Place of Occurrence
    elements.append(Paragraph("2. PLACE OF OCCURRENCE & JURISDICTION", section_title))
    loc_data = [
        [Paragraph("<b>Incident Location:</b>", bold_text), Paragraph(fir.incident_location, body_text)],
        [Paragraph("<b>Distance / Direction from PS:</b>", bold_text), Paragraph(f"{fir.distance_from_station or '2.5 KM'} from Police Station beat", body_text)]
    ]
    loc_table = Table(loc_data, colWidths=[150, 390])
    loc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(loc_table)
    elements.append(Spacer(1, 8))

    # 5. Narrative of Incident / Facts of the Case
    elements.append(Paragraph("3. COMPLAINT NARRATIVE & PARTICULARS OF OCCURRENCE", section_title))
    summary_p = Paragraph(fir.incident_details or "No incident details recorded.", body_text)
    narrative_table = Table([[summary_p]], colWidths=[540])
    narrative_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    elements.append(narrative_table)
    elements.append(Spacer(1, 14))

    # 6. Official Signatures Block
    elements.append(Paragraph("4. STATUTORY VERIFICATION & SIGNATURES", section_title))
    elements.append(Spacer(1, 20))
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Complainant / Informant</b><br/>Thumb Impression / Signature", ParagraphStyle('Sig1', fontName='Helvetica', fontSize=8, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Duty Officer (Moharrir)</b><br/>Police Station Duty Book", ParagraphStyle('Sig2', fontName='Helvetica', fontSize=8, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Station House Officer (SHO)</b><br/>Official Seal & Signature", ParagraphStyle('Sig3', fontName='Helvetica', fontSize=8, leading=10, alignment=1))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.append(KeepTogether(sig_table))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename="FIR_{fir.fir_number}.pdf"'}
    )


def generate_case_pdf(case):
    """
    Generate an official Case Summary and Investigation Docket PDF
    including suspect details, collected evidence items, and court proceedings.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CaseHeader',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=1,
        textColor=colors.HexColor('#0f172a')
    )
    sec_title = ParagraphStyle(
        'CaseSec',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=6,
        spaceAfter=4
    )
    body_text = ParagraphStyle('CaseBody', fontName='Helvetica', fontSize=8, leading=10)
    bold_text = ParagraphStyle('CaseBold', fontName='Helvetica-Bold', fontSize=8, leading=10)
    hdr_text = ParagraphStyle('Hdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    elements = []

    # Header
    elements.append(Paragraph("POLICE DEPARTMENT - INVESTIGATION CASE DOCKET", title_style))
    elements.append(Paragraph(f"CASE FILE: {case.case_number} - {case.case_title}", ParagraphStyle('Sub', fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1, textColor=colors.HexColor('#b91c1c'))))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1e3a8a'), spaceAfter=8))

    # Basic Info Table
    lead_name = case.lead_investigator.full_name if case.lead_investigator else "Unassigned"
    io_badge = case.lead_investigator.badge_number if case.lead_investigator else "-"
    fir_num = case.fir.fir_number if case.fir else "Direct Investigation"

    meta_rows = [
        [Paragraph("<b>Case Number:</b>", bold_text), Paragraph(case.case_number, bold_text),
         Paragraph("<b>Current Status:</b>", bold_text), Paragraph(case.case_status, bold_text)],
        [Paragraph("<b>Primary FIR:</b>", bold_text), Paragraph(fir_num, body_text),
         Paragraph("<b>Date Opened:</b>", bold_text), Paragraph(case.date_opened.strftime('%d-%b-%Y') if case.date_opened else '-', body_text)],
        [Paragraph("<b>Lead Investigator (IO):</b>", bold_text), Paragraph(f"{lead_name} (Badge: {io_badge})", body_text),
         Paragraph("<b>Crime Classification:</b>", bold_text), Paragraph(case.crime_type.name if case.crime_type else 'General', body_text)]
    ]
    meta_table = Table(meta_rows, colWidths=[130, 140, 130, 140])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('PADDING', (0, 0), (-1, -1), 3)
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))

    # Case Summary
    elements.append(Paragraph("INVESTIGATION BRIEF & FACTS", sec_title))
    summary_box = Table([[Paragraph(case.summary or "No summary recorded.", body_text)]], colWidths=[540])
    summary_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]))
    elements.append(summary_box)
    elements.append(Spacer(1, 8))

    # Suspects / Accused
    elements.append(Paragraph("ACCUSED SUSPECTS IN DOCKET", sec_title))
    accused_links = case.case_accused.all() if hasattr(case.case_accused, 'all') else case.case_accused
    acc_rows = [[Paragraph("Suspect Name", hdr_text), Paragraph("CNIC Number", hdr_text), Paragraph("Role / Status", hdr_text), Paragraph("Arrest Date", hdr_text)]]
    for ca in accused_links:
        a = ca.accused
        acc_rows.append([
            Paragraph(a.full_name if a else 'Unknown', body_text),
            Paragraph(a.national_id if (a and a.national_id) else '-', body_text),
            Paragraph(ca.arrest_status or 'Accused', body_text),
            Paragraph(ca.arrest_date.strftime('%d-%b-%Y') if ca.arrest_date else 'Absconding / At Large', body_text)
        ])
    if len(acc_rows) == 1:
        acc_rows.append([Paragraph("No suspects nominated in case file yet.", body_text), Paragraph("", body_text), Paragraph("", body_text), Paragraph("", body_text)])

    acc_table = Table(acc_rows, colWidths=[160, 120, 130, 130])
    acc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 3)
    ]))
    elements.append(acc_table)
    elements.append(Spacer(1, 8))

    # Recovered Evidence
    elements.append(Paragraph("RECOVERED EVIDENCE & PROPERTY", sec_title))
    ev_list = case.evidences.all() if hasattr(case.evidences, 'all') else case.evidences
    ev_rows = [[Paragraph("Evidence #", hdr_text), Paragraph("Item Description", hdr_text), Paragraph("Seized Location", hdr_text), Paragraph("Malkhana Status", hdr_text)]]
    for ev in ev_list:
        ev_rows.append([
            Paragraph(ev.evidence_number, bold_text),
            Paragraph(ev.item_name, body_text),
            Paragraph(ev.collected_from_location[:25], body_text),
            Paragraph(ev.chain_of_custody_status, body_text)
        ])
    if len(ev_rows) == 1:
        ev_rows.append([Paragraph("No physical exhibits logged for this case.", body_text), Paragraph("", body_text), Paragraph("", body_text), Paragraph("", body_text)])

    ev_table = Table(ev_rows, colWidths=[120, 180, 120, 120])
    ev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 3)
    ]))
    elements.append(ev_table)
    elements.append(Spacer(1, 8))

    # Court Hearings
    elements.append(Paragraph("COURT PROCEEDINGS & HEARINGS", sec_title))
    hearings = case.case_hearings.all() if hasattr(case.case_hearings, 'all') else case.case_hearings
    h_rows = [[Paragraph("Date", hdr_text), Paragraph("Hearing Type", hdr_text), Paragraph("Court / Magistrate", hdr_text), Paragraph("Ruling / Remarks", hdr_text)]]
    for h in hearings:
        h_rows.append([
            Paragraph(h.hearing_date.strftime('%d-%b-%Y') if h.hearing_date else '-', body_text),
            Paragraph(h.hearing_type, body_text),
            Paragraph(h.court.name if h.court else (h.judge.name if h.judge else 'Judicial Court'), body_text),
            Paragraph(h.outcome or h.judge_remarks or 'Sub Judice', body_text)
        ])
    if len(h_rows) == 1:
        h_rows.append([Paragraph("No court hearings scheduled yet.", body_text), Paragraph("", body_text), Paragraph("", body_text), Paragraph("", body_text)])

    h_table = Table(h_rows, colWidths=[100, 130, 150, 160])
    h_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 3)
    ]))
    elements.append(h_table)
    elements.append(Spacer(1, 16))

    # Signatures
    elements.append(KeepTogether(Table([
        [
            Paragraph("____________________________<br/><b>Lead Investigating Officer (IO)</b><br/>Signature & Badge", ParagraphStyle('IO', fontName='Helvetica', fontSize=8, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Sub-Divisional Police Officer (DSP/SHO)</b><br/>Approved & Countersigned", ParagraphStyle('SHO', fontName='Helvetica', fontSize=8, leading=10, alignment=1))
        ]
    ], colWidths=[270, 270])))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename="Case_{case.case_number}.pdf"'}
    )


def generate_duty_roster_pdf(rosters, duty_date=None):
    """
    Generate an official Daily Police Duty Roster (Roznamcha) PDF
    listing shifts, officers, deployment points, and weapons.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'RosterHeader',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        alignment=1,
        textColor=colors.HexColor('#0f172a')
    )
    hdr_text = ParagraphStyle('HdrR', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)
    cell_text = ParagraphStyle('CellR', fontName='Helvetica', fontSize=8, leading=10)
    bold_cell = ParagraphStyle('BCell', fontName='Helvetica-Bold', fontSize=8, leading=10)

    elements = []

    date_str = duty_date.strftime('%A, %d %B %Y') if duty_date else datetime.utcnow().strftime('%A, %d %B %Y')
    elements.append(Paragraph("POLICE STATION CIVIL LINES, LAHORE - DAILY DUTY ROSTER", title_style))
    elements.append(Paragraph(f"Official Station Roznamcha Deployment Order - {date_str}", ParagraphStyle('RosterSub', fontName='Helvetica', fontSize=10, leading=13, alignment=1, textColor=colors.HexColor('#475569'))))
    elements.append(Spacer(1, 10))

    headers = [
        Paragraph("Shift", hdr_text),
        Paragraph("Badge #", hdr_text),
        Paragraph("Officer Name", hdr_text),
        Paragraph("Rank / Role", hdr_text),
        Paragraph("Assigned Beat / Point", hdr_text),
        Paragraph("Duty Type", hdr_text),
        Paragraph("Remarks / Instructions", hdr_text)
    ]
    table_rows = [headers]

    for r in rosters:
        off = r.officer
        table_rows.append([
            Paragraph(r.shift.name if r.shift else 'General', cell_text),
            Paragraph(off.badge_number if off else '-', bold_cell),
            Paragraph(off.full_name if off else 'Personnel', cell_text),
            Paragraph(off.rank.name if (off and off.rank) else '-', cell_text),
            Paragraph(r.assigned_area or 'Beat Patrol', cell_text),
            Paragraph(r.duty_type or 'On Duty', cell_text),
            Paragraph(r.remarks or 'Active deployment', cell_text)
        ])

    if len(table_rows) == 1:
        table_rows.append([Paragraph("No roster deployments recorded for this date.", cell_text)] + [Paragraph("", cell_text)]*6)

    table = Table(table_rows, repeatRows=1, colWidths=[100, 80, 140, 120, 150, 90, 110])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(KeepTogether(Table([
        [
            Paragraph("____________________________<br/><b>Station Moharrir (Clerk)</b><br/>Duty Register In-Charge", ParagraphStyle('M', fontName='Helvetica', fontSize=8, leading=10, alignment=1)),
            Paragraph("____________________________<br/><b>Station House Officer (SHO)</b><br/>Approved & Dispatched", ParagraphStyle('S', fontName='Helvetica', fontSize=8, leading=10, alignment=1))
        ]
    ], colWidths=[370, 370])))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'inline; filename="Duty_Roster_{datetime.utcnow().strftime("%Y%m%d")}.pdf"'}
    )
