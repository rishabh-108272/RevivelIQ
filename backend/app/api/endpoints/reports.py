import io
import datetime
import subprocess
import sys
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import Customer, Contract, Invoice, SupportTicket, Recommendation, User

router = APIRouter()

def get_report_data(db: Session, organization_id: int) -> Dict[str, Any]:
    """Compiles all necessary metrics for the Board Report."""
    customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
    if not customers:
        return {}
        
    cust_ids = [c.id for c in customers]
    
    total_rev_at_risk = sum(c.revenue_at_risk for c in customers)
    high_risk_custs = [c for c in customers if c.risk_level == "High"]
    
    # Sort high risk customers by exposure
    high_risk_custs = sorted(high_risk_custs, key=lambda c: c.revenue_at_risk, reverse=True)
    
    # Top Churn Drivers
    overdue_invoices_count = db.query(Invoice).filter(Invoice.customer_id.in_(cust_ids), Invoice.status == "Overdue").count()
    open_tickets_count = db.query(SupportTicket).filter(SupportTicket.customer_id.in_(cust_ids), SupportTicket.status != "Resolved").count()
    high_priority_tickets_count = db.query(SupportTicket).filter(SupportTicket.customer_id.in_(cust_ids), SupportTicket.status != "Resolved", SupportTicket.priority == "High").count()
    
    # Expiring contracts (next 60 days)
    now = datetime.datetime.utcnow()
    sixty_days_hence = now + datetime.timedelta(days=60)
    expiring_contracts = db.query(Contract).filter(
        Contract.customer_id.in_(cust_ids),
        Contract.status == "Active",
        Contract.end_date <= sixty_days_hence
    ).count()
    
    churn_drivers = []
    if expiring_contracts > 0:
        churn_drivers.append(f"Imminent Renewal Deadlines: {expiring_contracts} contract(s) expiring within 60 days.")
    if overdue_invoices_count > 0:
        churn_drivers.append(f"Collections Delays: {overdue_invoices_count} overdue invoice(s) outstanding.")
    if high_priority_tickets_count > 0:
        churn_drivers.append(f"Unresolved Support Tickets: {high_priority_tickets_count} High Priority case(s) unresolved.")
    if not churn_drivers:
        churn_drivers.append("No active systemic risk drivers identified.")
        
    # Recovery opportunities & ROI
    recs = db.query(Recommendation).filter(
        Recommendation.customer_id.in_(cust_ids),
        Recommendation.status == "Pending"
    ).all()
    
    total_net_recovery = sum(r.net_recovery_value for r in recs)
    total_execution_cost = sum(r.cost_to_execute for r in recs)
    total_gross_impact = sum(r.revenue_impact_estimate for r in recs)
    
    # Top recommendations
    top_recs = sorted(recs, key=lambda r: r.net_recovery_value, reverse=True)[:3]
    recommended_actions = []
    for r in top_recs:
        cust_name = db.query(Customer.name).filter(Customer.id == r.customer_id).scalar() or "Unknown Client"
        recommended_actions.append({
            "client": cust_name,
            "action": r.title,
            "net_recovery": r.net_recovery_value,
            "description": r.description
        })
        
    return {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "total_revenue_at_risk": total_rev_at_risk,
        "high_risk_count": len(high_risk_custs),
        "high_risk_accounts": [
            {"name": c.name, "revenue": c.revenue, "revenue_at_risk": c.revenue_at_risk, "churn_prob": c.churn_probability}
            for c in high_risk_custs[:5]
        ],
        "churn_drivers": churn_drivers,
        "recovery_opportunities_count": len(recs),
        "expected_revenue_recovery": total_net_recovery,
        "total_execution_cost": total_execution_cost,
        "total_gross_impact": total_gross_impact,
        "recommended_actions": recommended_actions
    }

def generate_markdown_report(data: Dict[str, Any]) -> str:
    """Compiles report data into clean Markdown format."""
    if not data:
        return "# ReviveIQ Board Report\nNo data available."
        
    md = (
        f"# REVIVEIQ REVENUE INTELLIGENCE EXECUTIVE BOARD REPORT\n"
        f"**Generated at**: {data['generated_at']} UTC\n"
        f"**Classification**: STRICTLY CONFIDENTIAL - BOARD BRIEFING\n\n"
        f"## 1. Executive Summary\n"
        f"This report outlines the active portfolio revenue exposure and recovery plans. "
        f"Total active revenue at risk stands at **${data['total_revenue_at_risk']:,.2f}** "
        f"across **{data['high_risk_count']} high-risk** enterprise customer accounts. "
        f"Deployment of automated recovery campaigns is projected to restore up to **${data['expected_revenue_recovery']:,.2f}** "
        f"in net contract value.\n\n"
        f"## 2. Key Revenue Exposure Metrics\n"
        f"- **Total Portfolio Revenue at Risk**: ${data['total_revenue_at_risk']:,.2f}\n"
        f"- **Expected Revenue Recovery (Net)**: ${data['expected_revenue_recovery']:,.2f}\n"
        f"- **Estimated Recovery Campaign Execution Cost**: ${data['total_execution_cost']:,.2f}\n"
        f"- **Gross Protected Contract Value**: ${data['total_gross_impact']:,.2f}\n\n"
        f"## 3. Primary Churn Drivers Identified\n"
    )
    
    for driver in data['churn_drivers']:
        md += f"- {driver}\n"
        
    md += f"\n## 4. High Risk Customer Accounts\n"
    if not data['high_risk_accounts']:
        md += "No high-risk accounts requiring board escalation.\n"
    else:
        md += "| Company Name | Annual Contract Value | Churn Probability | Exposed Revenue |\n"
        md += "| :--- | :--- | :--- | :--- |\n"
        for acc in data['high_risk_accounts']:
            md += f"| {acc['name']} | ${acc['revenue']:,.2f} | {int(acc['churn_prob']*100)}% | ${acc['revenue_at_risk']:,.2f} |\n"
            
    md += (
        f"\n## 5. Prioritized Executive Recovery Actions\n"
        f"The following actions offer the highest net recovery rates and ROI this quarter:\n\n"
    )
    
    for idx, act in enumerate(data['recommended_actions']):
        md += (
            f"### Action {idx+1}: {act['action']} for **{act['client']}**\n"
            f"- **Net Revenue Recovered**: ${act['net_recovery']:,.2f}\n"
            f"- **Description**: {act['description']}\n\n"
        )
        
    return md

def generate_pdf_report(data: Dict[str, Any]) -> io.BytesIO:
    """Compiles report data into a professional PDF stream using ReportLab."""
    pdf_buffer = io.BytesIO()
    
    # Try importing ReportLab. If not found, attempt install
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except Exception:
            # Fallback simple PDF writer if install fails
            pdf_buffer.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 120 >>\nstream\nBT\n/F1 14 Tf\n50 700 Td\n(ReviveIQ Board Report Fallback - ReportLab missing) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000280 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n450\n%%EOF\n")
            pdf_buffer.seek(0)
            return pdf_buffer
            
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0078d4'),
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#201f1e'),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#323130'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # 1. Header Banner
    story.append(Paragraph("REVIVEIQ BOARD REPORT - CONFIDENTIAL", ParagraphStyle('Sub', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#e81123'), spaceAfter=5)))
    story.append(Paragraph("Executive Revenue Recovery Briefing", title_style))
    story.append(Paragraph(f"<b>Generated on:</b> {data['generated_at']} UTC | <b>Scope:</b> Organization Active Portfolios", body_style))
    story.append(Spacer(1, 15))
    
    # 2. Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    story.append(Paragraph(
        f"This briefing provides the executive board with visibility into current contract renewals, collections backlogs, "
        f"and simulated customer health forecasts. Total exposed portfolio revenue stands at <b>${data['total_revenue_at_risk']:,.2f}</b> "
        f"associated with <b>{data['high_risk_count']} high-risk</b> customer profiles. "
        f"Prioritized recovery campaigns are projected to yield up to <b>${data['expected_revenue_recovery']:,.2f}</b> in net recovered revenue.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    # 3. Revenue Metrics Table
    story.append(Paragraph("2. Financial Impact Overview", h2_style))
    metrics_table_data = [
        [Paragraph("<b>Key Risk Indicator</b>", bold_body_style), Paragraph("<b>Estimated Impact Value</b>", bold_body_style)],
        [Paragraph("Total Portfolio Revenue at Risk", body_style), Paragraph(f"${data['total_revenue_at_risk']:,.2f}", bold_body_style)],
        [Paragraph("Expected Revenue Recovery (Net)", body_style), Paragraph(f"${data['expected_revenue_recovery']:,.2f}", bold_body_style)],
        [Paragraph("Outreach Campaigns Execution Cost", body_style), Paragraph(f"${data['total_execution_cost']:,.2f}", body_style)],
        [Paragraph("Gross Protected Contract Value", body_style), Paragraph(f"${data['total_gross_impact']:,.2f}", body_style)]
    ]
    t1 = Table(metrics_table_data, colWidths=[250, 200])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#faf9f8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#201f1e')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#edebe9')),
        ('LINEBELOW', (0,1), (1,1), 1.5, colors.HexColor('#d2d0ce'))
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))
    
    # 4. Churn Drivers
    story.append(Paragraph("3. Primary Risk & Churn Drivers", h2_style))
    for d in data['churn_drivers']:
        story.append(Paragraph(f"• {d}", bullet_style))
    story.append(Spacer(1, 12))
    
    # 5. High Risk Customers Table
    story.append(Paragraph("4. Top High-Risk Customer Escalations", h2_style))
    if not data['high_risk_accounts']:
        story.append(Paragraph("No active high-risk customer accounts identified.", body_style))
    else:
        accounts_table_data = [
            [Paragraph("<b>Client Name</b>", bold_body_style), Paragraph("<b>Contract ACV</b>", bold_body_style), Paragraph("<b>Churn Prob</b>", bold_body_style), Paragraph("<b>Revenue Exposure</b>", bold_body_style)]
        ]
        for acc in data['high_risk_accounts']:
            accounts_table_data.append([
                Paragraph(acc['name'], body_style),
                Paragraph(f"${acc['revenue']:,.2f}", body_style),
                Paragraph(f"{int(acc['churn_prob']*100)}%", body_style),
                Paragraph(f"${acc['revenue_at_risk']:,.2f}", bold_body_style)
            ])
        t2 = Table(accounts_table_data, colWidths=[180, 100, 80, 100])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#faf9f8')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#edebe9')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t2)
    story.append(Spacer(1, 12))
    
    # 6. Prioritized Outreach Actions
    story.append(Paragraph("5. Recommended Recovery outreach Actions", h2_style))
    for idx, act in enumerate(data['recommended_actions']):
        story.append(Paragraph(f"<b>Action {idx+1}: {act['action']} for {act['client']}</b>", ParagraphStyle('BoldAct', parent=body_style, fontName='Helvetica-Bold')))
        story.append(Paragraph(f"Projected Net Recovery: <b>${act['net_recovery']:,.2f}</b>", body_style))
        story.append(Paragraph(f"Outreach Description: {act['description']}", ParagraphStyle('ItalicDesc', parent=body_style, fontName='Helvetica-Oblique', textColor=colors.HexColor('#605e5c'))))
        story.append(Spacer(1, 6))
        
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

@router.get("/board")
def get_board_report(
    format: str = Query("markdown", regex="^(markdown|pdf)$"),
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Generates the Executive Board Report for the organization portfolio."""
    org_id = current_user.organization_id
    report_data = get_report_data(db, org_id)
    
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization customer data found to generate report."
        )
        
    if format == "pdf":
        pdf_stream = generate_pdf_report(report_data)
        headers = {
            "Content-Disposition": "attachment; filename=reviveiq_executive_board_report.pdf",
            "Content-Type": "application/pdf"
        }
        return StreamingResponse(pdf_stream, headers=headers)
    else:
        # Default to markdown download/stream
        md_text = generate_markdown_report(report_data)
        headers = {
            "Content-Disposition": "attachment; filename=reviveiq_executive_board_report.md",
            "Content-Type": "text/markdown"
        }
        return StreamingResponse(io.BytesIO(md_text.encode("utf-8")), headers=headers)
