"""
Report Generator Agent
Generates formatted reports in PDF and Excel formats with beautiful charts and visualizations
"""
import os
import re
import json
from .report_config import REPORTS_DIR # <-- Imports your new config file
from datetime import datetime

# ReportLab Imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Pandas & Matplotlib Imports
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt


class ReportGeneratorAgent:
    """Agent for generating formatted reports"""
    
    def __init__(self):
        self.name = "Report Generator Agent"
        self.reports_dir = REPORTS_DIR
    
    def _create_chart_from_data(self, data_dict: dict, chart_type: str = 'bar') -> str:
        """Create a chart from data and return the filepath"""
        temp_dir = os.path.join(self.reports_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        chart_path = os.path.join(temp_dir, f'chart_{timestamp}.png')
        
        plt.figure(figsize=(8, 5))
        
        # Use vibrant colors
        colors_list = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', 
                       '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788']
        
        if chart_type == 'bar':
            bars = plt.bar(data_dict.keys(), data_dict.values(), color=colors_list[:len(data_dict)])
            plt.xticks(rotation=45, ha='right')
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                         f'{height:.1f}',
                         ha='center', va='bottom', fontweight='bold')
        elif chart_type == 'pie':
            plt.pie(data_dict.values(), labels=data_dict.keys(), autopct='%1.1f%%',
                    colors=colors_list[:len(data_dict)], startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
        elif chart_type == 'line':
            plt.plot(list(data_dict.keys()), list(data_dict.values()), 
                     marker='o', linewidth=3, markersize=8, color='#FF6B6B')
            plt.fill_between(range(len(data_dict)), list(data_dict.values()), alpha=0.3, color='#FF6B6B')
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return chart_path
    
    def _extract_numeric_data(self, text: str) -> dict:
        """Extract numeric data from text for visualization"""
        data = {}
        
        # Look for common patterns like "X: $Y million" or "X: Y%"
        patterns = [
            r'([A-Za-z\s\-]+):\s*\$?([\d,\.]+)\s*(?:million|billion|%)?',
            r'([A-Za-z\s\-]+)\s*\(?\$?([\d,\.]+)\s*(?:million|billion|%)?\)?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    key = match[0].strip()
                    value = float(match[1].replace(',', ''))
                    if len(key) > 3 and len(key) < 50: # Valid label length
                        data[key] = value
                except:
                    pass
        
        return data if len(data) >= 2 else None
    
    def generate_pdf_report(self, query: str, agent_responses: list, summary: str) -> str:
        """Generate a comprehensive PDF report with charts, graphs, and vibrant colors"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pharma_innovation_report_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=60, leftMargin=60,
                                topMargin=60, bottomMargin=30)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles with bigger, more colorful headings
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=36, # Much bigger!
            textColor=colors.HexColor('#1a237e'), # Deep blue
            spaceAfter=40,
            spaceBefore=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=24, # Bigger headings
            textColor=colors.HexColor('#0277bd'), # Bright blue
            spaceAfter=16,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#4fc3f7'),
            borderWidth=2,
            borderPadding=8,
            backColor=colors.HexColor('#e1f5fe')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=18,
            textColor=colors.HexColor('#00695c'), # Teal
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        highlight_style = ParagraphStyle(
            'Highlight',
            parent=styles['Normal'],
            fontSize=12,
            backColor=colors.HexColor('#fff9c4'), # Light yellow
            borderColor=colors.HexColor('#fbc02d'),
            borderWidth=1,
            borderPadding=10,
            spaceAfter=12
        )
        
        # Add colorful header box
        header_data = [[Paragraph("🔬 Pharmaceutical Innovation Intelligence Report", title_style)]]
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8eaf6')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LINEABOVE', (0, 0), (-1, 0), 4, colors.HexColor('#1a237e')),
            ('LINEBELOW', (0, 0), (-1, -1), 4, colors.HexColor('#1a237e'))
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Colorful metadata table
        metadata = [
            ['📅 Report Generated:', datetime.now().strftime("%B %d, %Y at %H:%M:%S")],
            ['❓ Query:', query],
            ['🤖 AI Agents Consulted:', str(len(agent_responses))],
        ]
        
        metadata_table = Table(metadata, colWidths=[2.2*inch, 4.8*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4fc3f7')), # Bright cyan
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#e1f5fe')), # Light blue
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#0277bd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 30))
        
        # Table of Contents
        elements.append(Paragraph("📑 TABLE OF CONTENTS", heading_style))
        elements.append(Spacer(1, 12))
        
        toc_items = [
            "1. Executive Summary",
            "2. Research Objective",
            "3. Methodology & Data Sources",
            "4. Detailed Analysis by Domain",
            "5. Key Findings & Insights",
            "6. Strategic Recommendations",
            "7. Conclusion"
        ]
        
        toc_style = ParagraphStyle(
            'TOC',
            parent=styles['Normal'],
            fontSize=12,
            leftIndent=20,
            spaceAfter=6,
            textColor=colors.HexColor('#1a237e')
        )
        
        for item in toc_items:
            elements.append(Paragraph(f"<b>{item}</b>", toc_style))
        
        elements.append(Spacer(1, 30))
        elements.append(PageBreak())
        
        # Executive Summary with colorful box
        elements.append(Paragraph("📊 1. EXECUTIVE SUMMARY", heading_style))
        elements.append(Spacer(1, 12))
        
        summary_para = Paragraph(summary.replace('\n', '<br/>'), highlight_style)
        elements.append(summary_para)
        elements.append(Spacer(1, 20))
        
        # Try to create a summary visualization if numeric data found
        summary_data = self._extract_numeric_data(summary)
        if summary_data:
            try:
                chart_path = self._create_chart_from_data(summary_data, 'bar')
                img = Image(chart_path, width=6*inch, height=3.5*inch)
                elements.append(img)
                elements.append(Spacer(1, 12))
            except Exception as e:
                print(f"Could not create summary chart: {e}")
        
        elements.append(Spacer(1, 30))
        
        # Research Objective Section
        elements.append(Paragraph("🎯 2. RESEARCH OBJECTIVE", heading_style))
        elements.append(Spacer(1, 12))
        
        objective_text = f"""
        <b>Primary Research Question:</b><br/>
        {query}<br/><br/>
        
        <b>Purpose of Analysis:</b><br/>
        This comprehensive intelligence report was generated to provide actionable insights for pharmaceutical 
        innovation and strategic decision-making. The analysis leverages multiple data sources including market 
        intelligence, patent databases, clinical trial registries, trade data, and internal knowledge repositories 
        to deliver a 360-degree view of the opportunity landscape.<br/><br/>
        
        <b>Scope of Investigation:</b><br/>
        • Market size and growth potential analysis<br/>
        • Competitive landscape assessment<br/>
        • Intellectual property and patent intelligence<br/>
        • Clinical development landscape<br/>
        • Regulatory and trade considerations<br/>
        • Strategic opportunities and white spaces<br/>
        """
        
        objective_para = Paragraph(objective_text, styles['Normal'])
        elements.append(objective_para)
        elements.append(Spacer(1, 30))
        
        # Methodology Section
        elements.append(Paragraph("🔬 3. METHODOLOGY & DATA SOURCES", heading_style))
        elements.append(Spacer(1, 12))
        
        methodology_text = """
        <b>AI-Powered Multi-Agent Analysis:</b><br/>
        This report utilizes an advanced multi-agent AI system that orchestrates specialized intelligence agents, 
        each focusing on specific domains of pharmaceutical intelligence. The Master Agent coordinates these 
        specialized workers to provide comprehensive, synthesized insights.<br/><br/>
        """
        
        elements.append(Paragraph(methodology_text, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Data Sources Table
        data_sources = [
            ['Data Source', 'Coverage', 'Primary Use'],
            ['IQVIA Market Intelligence', 'Global pharmaceutical markets, sales data, forecasts', 'Market sizing, trends, competition'],
            ['USPTO & Patent Databases', 'Global patent filings and grants', 'IP landscape, patent expiry'],
            ['ClinicalTrials.gov', 'Clinical trial registries worldwide', 'Pipeline analysis, trial designs'],
            ['EXIM Trade Data', 'Import/export pharmaceutical data', 'Trade flows, market access'],
            ['Internal Knowledge Base', 'Company strategy, research archives', 'Historical context, precedents'],
            ['Web Intelligence', 'Current guidelines, publications', 'Latest developments, regulations']
        ]
        
        sources_table = Table(data_sources, colWidths=[1.8*inch, 2.5*inch, 2.2*inch])
        sources_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#0277bd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(sources_table)
        elements.append(Spacer(1, 30))
        elements.append(PageBreak())
        
        # Agent Responses with charts
        elements.append(Paragraph("🔍 4. DETAILED ANALYSIS BY DOMAIN", heading_style))
        elements.append(Spacer(1, 16))
        
        # Color scheme for different agents
        agent_colors = {
            'iqvia': '#FF6B6B',
            'exim': '#4ECDC4', 
            'patent': '#45B7D1',
            'clinical': '#FFA07A',
            'internal': '#98D8C8',
            'web': '#F7DC6F'
        }
        
        for idx, response in enumerate(agent_responses):
            agent_name = response.get('agent', 'Unknown Agent')
            analysis = response.get('analysis', 'No analysis available')
            sources = response.get('sources', [])
            
            # Determine agent color
            agent_color = colors.HexColor('#00695c')
            for key, color in agent_colors.items():
                if key.lower() in agent_name.lower():
                    agent_color = colors.HexColor(color)
                    break
            
            # Agent section with colored header
            agent_header_data = [[Paragraph(f"<b>4.{idx+1} {agent_name}</b>", subheading_style)]]
            agent_header_table = Table(agent_header_data, colWidths=[7*inch])
            agent_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), agent_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, 0), (-1, -1), 3, colors.white)
            ]))
            elements.append(agent_header_table)
            elements.append(Spacer(1, 12))
            
            # Analysis content with better formatting
            analysis_styled = ParagraphStyle(
                'AnalysisText',
                parent=styles['Normal'],
                fontSize=11,
                leading=16,
                spaceAfter=8
            )
            analysis_para = Paragraph(analysis.replace('\n', '<br/>'), analysis_styled)
            elements.append(analysis_para)
            elements.append(Spacer(1, 12))
            
            # Try to create visualization from analysis
            analysis_data = self._extract_numeric_data(analysis)
            if analysis_data:
                try:
                    # Choose chart type based on data
                    chart_type = 'pie' if len(analysis_data) <= 5 else 'bar'
                    chart_path = self._create_chart_from_data(analysis_data, chart_type)
                    
                    # Add chart title
                    chart_title = Paragraph(f"<b>Visual Analysis from {agent_name}</b>", 
                                          ParagraphStyle('ChartTitle', parent=styles['Normal'], 
                                                         fontSize=10, textColor=colors.HexColor('#555555')))
                    elements.append(chart_title)
                    elements.append(Spacer(1, 6))
                    
                    img = Image(chart_path, width=5.5*inch, height=3.2*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                except Exception as e:
                    print(f"Could not create chart for {agent_name}: {e}")
            
            # Sources in a colored box
            if sources:
                sources_text = "<b>📚 Data Sources:</b> " + ", ".join(sources)
                sources_style = ParagraphStyle(
                    'Sources',
                    parent=styles['Normal'],
                    fontSize=9,
                    backColor=colors.HexColor('#f5f5f5'),
                    borderColor=agent_color,
                    borderWidth=1,
                    borderPadding=6,
                    leftIndent=10
                )
                sources_para = Paragraph(sources_text, sources_style)
                elements.append(sources_para)
            
            elements.append(Spacer(1, 24))
        
        elements.append(PageBreak())
        
        # Key Findings Section
        elements.append(Paragraph("💡 5. KEY FINDINGS & INSIGHTS", heading_style))
        elements.append(Spacer(1, 12))
        
        findings_intro = """
        Based on the comprehensive analysis conducted by our AI agents across multiple data sources, 
        the following key findings have been identified as critical to strategic decision-making:
        """
        elements.append(Paragraph(findings_intro, styles['Normal']))
        elements.append(Spacer(1, 16))
        
        # Extract key points from each agent
        key_findings = []
        for idx, response in enumerate(agent_responses):
            agent_name = response.get('agent', 'Unknown Agent')
            analysis = response.get('analysis', '')
            
            # Extract first few sentences as key finding
            sentences = analysis.split('.')[:2]
            if sentences:
                finding = '. '.join(sentences) + '.'
                key_findings.append([f"<b>{agent_name}</b>", finding])
        
        if key_findings:
            findings_table = Table(key_findings, colWidths=[1.5*inch, 5.5*inch])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#0277bd')),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
            ]))
            elements.append(findings_table)
        
        elements.append(Spacer(1, 30))
        
        # Strategic Recommendations Section
        elements.append(Paragraph("🎯 6. STRATEGIC RECOMMENDATIONS", heading_style))
        elements.append(Spacer(1, 12))
        
        recommendations = [
            {
                'title': 'Immediate Actions (0-3 months)',
                'items': [
                    'Conduct detailed competitive intelligence on identified opportunity areas',
                    'Initiate preliminary feasibility studies for promising therapeutic areas',
                    'Establish cross-functional team to evaluate market entry strategies',
                    'Begin regulatory pathway assessment for target markets'
                ],
                'color': '#FF6B6B'
            },
            {
                'title': 'Short-term Initiatives (3-6 months)',
                'items': [
                    'Develop comprehensive business case for top 2-3 opportunities',
                    'Initiate partnership discussions with key stakeholders',
                    'Conduct deep-dive patent landscape analysis',
                    'Design clinical development strategy aligned with regulatory requirements'
                ],
                'color': '#4ECDC4'
            },
            {
                'title': 'Long-term Strategy (6-12 months)',
                'items': [
                    'Execute full-scale market entry plan for selected opportunities',
                    'Establish strategic partnerships or licensing agreements',
                    'Initiate Phase I/II clinical trials for prioritized candidates',
                    'Build commercial infrastructure for target markets'
                ],
                'color': '#45B7D1'
            }
        ]
        
        for rec in recommendations:
            # Recommendation header
            rec_header = Paragraph(f"<b>{rec['title']}</b>", subheading_style)
            elements.append(rec_header)
            elements.append(Spacer(1, 8))
            
            # Recommendation items
            for item in rec['items']:
                bullet_style = ParagraphStyle(
                    'Bullet',
                    parent=styles['Normal'],
                    fontSize=11,
                    leftIndent=20,
                    bulletIndent=10,
                    spaceAfter=6
                )
                elements.append(Paragraph(f"• {item}", bullet_style))
            
            elements.append(Spacer(1, 16))
        
        elements.append(Spacer(1, 20))
        elements.append(PageBreak())
        
        # Conclusion Section
        elements.append(Paragraph("📌 7. CONCLUSION", heading_style))
        elements.append(Spacer(1, 12))
        
        conclusion_text = f"""
        This comprehensive intelligence report, generated through our AI-powered multi-agent analysis system, 
        provides actionable insights to accelerate pharmaceutical innovation discovery from months to minutes.
        <br/><br/>
        <b>Key Takeaways:</b><br/>
        • The analysis leveraged {len(agent_responses)} specialized intelligence domains to provide a 360-degree view<br/>
        • Multiple data sources were synthesized to identify high-potential opportunities<br/>
        • Strategic recommendations are prioritized based on feasibility and impact<br/>
        • The identified opportunities align with market needs and competitive dynamics<br/>
        <br/>
        <b>Next Steps:</b><br/>
        We recommend immediate action on the short-term recommendations while building capability for 
        long-term strategic initiatives. The pharmaceutical innovation landscape is dynamic, and early 
        action on identified opportunities can provide significant competitive advantage.
        <br/><br/>
        <b>Report Validity:</b><br/>
        This report is based on data current as of {datetime.now().strftime("%B %Y")}. Market conditions, 
        competitive dynamics, and regulatory landscapes may change. We recommend quarterly updates to 
        maintain strategic relevance.
        """
        
        conclusion_box = ParagraphStyle(
            'Conclusion',
            parent=styles['Normal'],
            fontSize=11,
            backColor=colors.HexColor('#e8eaf6'),
            borderColor=colors.HexColor('#1a237e'),
            borderWidth=2,
            borderPadding=15,
            spaceAfter=12,
            leading=16
        )
        
        elements.append(Paragraph(conclusion_text, conclusion_box))
        elements.append(Spacer(1, 30))
        
        # Colorful footer
        footer_data = [[Paragraph("✨ This report was generated by the Pharmaceutical Innovation AI Agent System ✨", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, 
                                               textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))]]
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(Spacer(1, 30))
        elements.append(footer_table)
        
        # Build PDF
        doc.build(elements)
        
        # Clean up temp charts
        try:
            temp_dir = os.path.join(self.reports_dir, 'temp')
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    if file.startswith('chart_'):
                        os.remove(os.path.join(temp_dir, file))
        except:
            pass
        
        return filepath
    
    def generate_excel_report(self, query: str, agent_responses: list) -> str:
        """Generate an Excel report with structured data"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pharma_innovation_data_{timestamp}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Report Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'Query': [query],
                'Number of Agents': [len(agent_responses)]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create sheets for each agent with structured data
            for i, response in enumerate(agent_responses):
                agent_name = response.get('agent', f'Agent_{i}').replace(' ', '_')
                raw_data = response.get('raw_data', {})
                
                # Convert raw data to DataFrame format if possible
                if raw_data:
                    try:
                        # Flatten nested data
                        flattened_data = self._flatten_dict(raw_data)
                        df = pd.DataFrame([flattened_data])
                    except:
                        # If flattening fails, create simple key-value pairs
                        df = pd.DataFrame(list(raw_data.items()), columns=['Key', 'Value'])
                    
                    # Limit sheet name to 31 characters (Excel limit)
                    sheet_name = agent_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return filepath
    
    def _flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def generate_report(self, query: str, agent_responses: list, summary: str, format: str = "pdf") -> dict:
        """Generate report in specified format"""
        
        try:
            if format.lower() == "pdf":
                filepath = self.generate_pdf_report(query, agent_responses, summary)
                return {
                    "agent": self.name,
                    "status": "success",
                    "format": "PDF",
                    "filepath": filepath,
                    "message": f"PDF report generated successfully: {os.path.basename(filepath)}"
                }
            elif format.lower() == "excel":
                filepath = self.generate_excel_report(query, agent_responses)
                return {
                    "agent": self.name,
                    "status": "success",
                    "format": "Excel",
                    "filepath": filepath,
                    "message": f"Excel report generated successfully: {os.path.basename(filepath)}"
                }
            else:
                # Generate both
                pdf_path = self.generate_pdf_report(query, agent_responses, summary)
                excel_path = self.generate_excel_report(query, agent_responses)
                return {
                    "agent": self.name,
                    "status": "success",
                    "format": "PDF & Excel",
                    "pdf_filepath": pdf_path,
                    "excel_filepath": excel_path,
                    "message": f"Reports generated: {os.path.basename(pdf_path)} and {os.path.basename(excel_path)}"
                }
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "message": f"Error generating report: {str(e)}"
            }