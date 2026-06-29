# modules/report_gen.py
# ReportLab se professional PDF interview report banata hai

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from config import REPORTS_DIR

# Colors
PRIMARY = HexColor("#1a1a2e")
SECONDARY = HexColor("#16213e")
ACCENT = HexColor("#0f3460")
HIGHLIGHT = HexColor("#e94560")
SUCCESS = HexColor("#4caf50")
WARNING = HexColor("#ff9800")
DANGER = HexColor("#f44336")
LIGHT_BG = HexColor("#f8f9fa")
CARD_BG = HexColor("#ffffff")
TEXT_DARK = HexColor("#2d3436")
TEXT_LIGHT = HexColor("#636e72")


def get_score_color(score):
    if score >= 8:
        return SUCCESS
    elif score >= 6:
        return WARNING
    elif score >= 4:
        return HexColor("#ff6b35")
    else:
        return DANGER


def get_verdict_color(verdict):
    verdicts = {
        "Highly Recommended": SUCCESS,
        "Recommended": HexColor("#8bc34a"),
        "Consider": WARNING,
        "Not Recommended": DANGER
    }
    return verdicts.get(verdict, WARNING)


def create_score_bar(score, max_score=10, width=200, height=16):
    """Score bar drawing banao"""
    d = Drawing(width, height)
    
    # Background bar
    bg = Rect(0, 2, width, height - 4, fillColor=HexColor("#e0e0e0"), strokeColor=None)
    d.add(bg)
    
    # Score bar
    fill_width = (score / max_score) * width
    color = get_score_color(score)
    bar = Rect(0, 2, fill_width, height - 4, fillColor=color, strokeColor=None)
    d.add(bar)
    
    return d


def generate_pdf_report(report_data: dict, output_path: str = None) -> str:
    """Main function - Generate PDF report"""
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = report_data["candidate_info"].get("name", "Candidate").replace(" ", "_")
        output_path = os.path.join(REPORTS_DIR, f"Interview_Report_{name}_{timestamp}.pdf")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # ===== CUSTOM STYLES =====
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=26,
        textColor=white,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=12,
        textColor=HexColor("#b2bec3"),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontSize=14,
        textColor=white,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    body_style = ParagraphStyle(
        'Body',
        fontSize=10,
        textColor=TEXT_DARK,
        fontName='Helvetica',
        spaceAfter=4,
        leading=14
    )
    
    label_style = ParagraphStyle(
        'Label',
        fontSize=9,
        textColor=TEXT_LIGHT,
        fontName='Helvetica'
    )
    
    value_style = ParagraphStyle(
        'Value',
        fontSize=10,
        textColor=TEXT_DARK,
        fontName='Helvetica-Bold'
    )
    
    # ===== HEADER SECTION =====
    candidate = report_data["candidate_info"]
    summary = report_data["summary"]
    analysis = report_data["final_analysis"]
    qa_pairs = report_data["qa_pairs"]
    
    header_data = [[
        Paragraph("🎯 AI INTERVIEW ASSESSMENT REPORT", title_style),
        Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style)
    ]]
    
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 20),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('SPAN', (0, 0), (-1, 0)),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [PRIMARY]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))
    
    # ===== CANDIDATE INFO + SCORE CARD =====
    avg_score = summary["average_score"]
    verdict = analysis.get("overall_verdict", "Consider")
    verdict_color = get_verdict_color(verdict)
    
    # Candidate details
    info_items = [
        ("👤 Name", candidate.get("name", "N/A")),
        ("📧 Email", candidate.get("email", "N/A")),
        ("📞 Phone", candidate.get("phone", "N/A")),
        ("💼 Current Role", candidate.get("current_role", "N/A")),
        ("⏳ Experience", candidate.get("total_experience", "N/A")),
        ("🎓 Education", candidate.get("education", "N/A")),
    ]
    
    info_table_data = []
    for label, val in info_items:
        info_table_data.append([
            Paragraph(label, label_style),
            Paragraph(str(val), value_style)
        ])
    
    info_table = Table(info_table_data, colWidths=[3.5 * cm, 8 * cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CARD_BG, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Score card
    score_color = get_score_color(avg_score)
    score_card_data = [
        [Paragraph("OVERALL SCORE", ParagraphStyle('sc', fontSize=11, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER))],
        [Paragraph(f"{avg_score}/10", ParagraphStyle('score', fontSize=36, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER))],
        [Paragraph(verdict, ParagraphStyle('verdict', fontSize=11, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER))],
        [Paragraph(f"{summary['total_questions']} Questions Asked", ParagraphStyle('q', fontSize=9, textColor=HexColor("#b2bec3"), alignment=TA_CENTER))],
    ]
    
    score_table = Table(score_card_data, colWidths=[5 * cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), score_color),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Side by side
    combined = Table(
        [[info_table, score_table]],
        colWidths=[12 * cm, 5.5 * cm]
    )
    combined.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
    ]))
    story.append(combined)
    story.append(Spacer(1, 0.4 * cm))
    
    # ===== SKILLS SECTION =====
    tech_skills = candidate.get("technical_skills", [])
    prog_langs = candidate.get("programming_languages", [])
    frameworks = candidate.get("frameworks", [])
    
    skills_header = Table(
        [[Paragraph("  💡 TECHNICAL SKILLS", section_header_style)]],
        colWidths=[doc.width]
    )
    skills_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(skills_header)
    story.append(Spacer(1, 0.2 * cm))
    
    def skill_chips(skills_list):
        chips = ", ".join([f"• {s}" for s in skills_list[:12]])
        return Paragraph(chips, ParagraphStyle('chips', fontSize=9, textColor=TEXT_DARK, leading=14))
    
    skills_data = [
        [Paragraph("Languages:", label_style), skill_chips(prog_langs)],
        [Paragraph("Frameworks:", label_style), skill_chips(frameworks)],
        [Paragraph("Technical:", label_style), skill_chips(tech_skills)],
    ]
    skills_table = Table(skills_data, colWidths=[2.5 * cm, 15 * cm])
    skills_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CARD_BG, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor("#dee2e6")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(skills_table)
    story.append(Spacer(1, 0.4 * cm))
    
    # ===== CATEGORY PERFORMANCE =====
    cat_perf = summary.get("category_performance", {})
    if cat_perf:
        cat_header = Table(
            [[Paragraph("  📊 PERFORMANCE BY CATEGORY", section_header_style)]],
            colWidths=[doc.width]
        )
        cat_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ACCENT),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(cat_header)
        story.append(Spacer(1, 0.2 * cm))
        
        cat_data = [["Category", "Score", "Performance Bar", "Rating"]]
        for cat, score in cat_perf.items():
            rating = "Excellent" if score >= 8 else "Good" if score >= 6 else "Average" if score >= 4 else "Poor"
            cat_data.append([
                Paragraph(cat, body_style),
                Paragraph(f"{score}/10", ParagraphStyle('cs', fontSize=11, fontName='Helvetica-Bold', textColor=get_score_color(score))),
                create_score_bar(score, width=150, height=14),
                Paragraph(rating, ParagraphStyle('r', fontSize=9, textColor=get_score_color(score), fontName='Helvetica-Bold'))
            ])
        
        cat_table = Table(cat_data, colWidths=[4 * cm, 2 * cm, 5 * cm, 2.5 * cm])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 0.4 * cm))
    
    # ===== Q&A DETAILED SECTION =====
    story.append(PageBreak())
    
    qa_header = Table(
        [[Paragraph("  📝 DETAILED Q&A ANALYSIS", section_header_style)]],
        colWidths=[doc.width]
    )
    qa_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(qa_header)
    story.append(Spacer(1, 0.3 * cm))
    
    for i, qa in enumerate(qa_pairs, 1):
        q = qa["question"]
        answer = qa.get("answer", "No answer provided")
        eval_data = qa.get("evaluation", {})
        score = eval_data.get("score", 0)
        
        # Question header
        q_score_color = get_score_color(score)
        q_header_data = [[
            Paragraph(f"Q{i}. {q.get('question', '')}", 
                     ParagraphStyle('qh', fontSize=10, textColor=white, fontName='Helvetica-Bold', leading=14)),
            Paragraph(f"{score}/10", 
                     ParagraphStyle('qs', fontSize=14, textColor=white, fontName='Helvetica-Bold', alignment=TA_RIGHT))
        ]]
        q_header = Table(q_header_data, colWidths=[14 * cm, 3.5 * cm])
        q_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), q_score_color),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(q_header)
        
        # Meta info
        meta = f"Category: {q.get('category', 'N/A')}  |  Skill: {q.get('skill_tested', 'N/A')}  |  Difficulty: {q.get('difficulty', 'N/A')}  |  Rating: {eval_data.get('rating', 'N/A')}"
        meta_table = Table(
            [[Paragraph(meta, ParagraphStyle('meta', fontSize=8, textColor=white))]],
            colWidths=[doc.width]
        )
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SECONDARY),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        
        # Answer
        answer_table = Table(
            [
                [Paragraph("Candidate's Answer:", label_style)],
                [Paragraph(answer[:500] + ("..." if len(answer) > 500 else ""), body_style)]
            ],
            colWidths=[doc.width]
        )
        answer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(answer_table)
        
        # Strengths & Improvements
        strengths = eval_data.get("strengths", [])
        improvements = eval_data.get("improvements", [])
        feedback = eval_data.get("detailed_feedback", "")
        
        si_data = [
            [
                Paragraph("✅ Strengths:\n" + "\n".join([f"• {s}" for s in strengths]) if strengths else "• None noted",
                          ParagraphStyle('str', fontSize=9, textColor=HexColor("#2d6a4f"), leading=13)),
                Paragraph("⚠️ To Improve:\n" + "\n".join([f"• {imp}" for imp in improvements]) if improvements else "• None",
                          ParagraphStyle('imp', fontSize=9, textColor=HexColor("#7b2d00"), leading=13))
            ]
        ]
        si_table = Table(si_data, colWidths=[8.75 * cm, 8.75 * cm])
        si_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor("#d8f3dc")),
            ('BACKGROUND', (1, 0), (1, 0), HexColor("#ffe8d6")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
        ]))
        story.append(si_table)
        
        if feedback:
            fb_table = Table(
                [[Paragraph(f"💬 Feedback: {feedback}", ParagraphStyle('fb', fontSize=9, textColor=TEXT_DARK, leading=13, fontName='Helvetica-Oblique'))]],
                colWidths=[doc.width]
            )
            fb_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor("#fff3cd")),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(fb_table)
        
        story.append(Spacer(1, 0.4 * cm))
    
    # ===== FINAL VERDICT =====
    story.append(PageBreak())
    
    verdict_header = Table(
        [[Paragraph("  🏆 FINAL VERDICT & RECOMMENDATION", section_header_style)]],
        colWidths=[doc.width]
    )
    verdict_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(verdict_header)
    story.append(Spacer(1, 0.3 * cm))
    
    # Verdict card
    verdict_val = analysis.get("overall_verdict", "Consider")
    verdict_data = [
        [
            Paragraph(f"VERDICT: {verdict_val}", 
                     ParagraphStyle('v', fontSize=20, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
            Paragraph(f"Suggested Level: {analysis.get('suggested_role_level', 'N/A')}", 
                     ParagraphStyle('vl', fontSize=14, textColor=white, alignment=TA_CENTER))
        ]
    ]
    verdict_table = Table(verdict_data, colWidths=[9 * cm, 8.5 * cm])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), get_verdict_color(verdict_val)),
        ('BACKGROUND', (1, 0), (1, 0), ACCENT),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 0.3 * cm))
    
    # Top strengths & improvements
    top_strengths = analysis.get("top_strengths", [])
    key_improvements = analysis.get("key_improvements", [])
    
    final_si_data = [[
        Paragraph("🌟 TOP STRENGTHS\n\n" + "\n".join([f"✓ {s}" for s in top_strengths]),
                 ParagraphStyle('ts', fontSize=10, textColor=HexColor("#1b4332"), leading=16)),
        Paragraph("🔧 KEY IMPROVEMENTS\n\n" + "\n".join([f"→ {imp}" for imp in key_improvements]),
                 ParagraphStyle('ki', fontSize=10, textColor=HexColor("#7b2d00"), leading=16))
    ]]
    final_si = Table(final_si_data, colWidths=[8.75 * cm, 8.75 * cm])
    final_si.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), HexColor("#d8f3dc")),
        ('BACKGROUND', (1, 0), (1, 0), HexColor("#ffe8d6")),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
    ]))
    story.append(final_si)
    story.append(Spacer(1, 0.3 * cm))
    
    # Hiring recommendation
    hiring_rec = analysis.get("hiring_recommendation", "")
    perf_summary = analysis.get("interview_performance_summary", "")
    
    rec_table = Table(
        [
            [Paragraph("📋 HIRING RECOMMENDATION", ParagraphStyle('rh', fontSize=11, textColor=white, fontName='Helvetica-Bold'))],
            [Paragraph(hiring_rec, ParagraphStyle('rb', fontSize=10, textColor=TEXT_DARK, leading=14))],
            [Paragraph("📈 PERFORMANCE SUMMARY", ParagraphStyle('ph', fontSize=11, textColor=white, fontName='Helvetica-Bold'))],
            [Paragraph(perf_summary, ParagraphStyle('pb', fontSize=10, textColor=TEXT_DARK, leading=14))],
        ],
        colWidths=[doc.width]
    )
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('BACKGROUND', (0, 2), (-1, 2), SECONDARY),
        ('BACKGROUND', (0, 1), (-1, 1), CARD_BG),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BG),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 0.5 * cm))
    
    # Footer
    footer_data = [[
        Paragraph(
            f"Report generated by AI Interview Assistant  |  {datetime.now().strftime('%d %B %Y')}  |  Confidential",
            ParagraphStyle('footer', fontSize=8, textColor=HexColor("#b2bec3"), alignment=TA_CENTER)
        )
    ]]
    footer = Table(footer_data, colWidths=[doc.width])
    footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(footer)
    
    # PDF build karo
    doc.build(story)
    print(f"[Report] PDF ban gayi: {output_path}")
    return output_path
