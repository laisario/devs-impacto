"""
PDF Generator for Projeto de Venda.

Uses ReportLab to generate a printable PDF document following
the PNAE Projeto de Venda format.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.modules.sales_projects.schemas import SalesProjectWithDetails


def generate_sales_project_pdf(data: SalesProjectWithDetails) -> bytes:
    """
    Generate PDF for Projeto de Venda.

    Args:
        data: Sales project with all related data

    Returns:
        PDF file content as bytes
    """
    buffer = io.BytesIO()

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=14,
        alignment=1,  # Center
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.darkblue,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=5,
    )

    # Build content
    elements: list[Paragraph | Spacer | Table] = []

    # Title
    elements.append(
        Paragraph(
            "PROJETO DE VENDA - AGRICULTURA FAMILIAR (PNAE)",
            title_style,
        )
    )
    elements.append(Spacer(1, 10))

    # Section 1: Identificação da Proposta
    elements.append(Paragraph("1. IDENTIFICAÇÃO DA PROPOSTA", section_style))
    elements.append(
        Paragraph(
            f"<b>Chamada Pública Nº:</b> {data.call_number}",
            normal_style,
        )
    )
    elements.append(Spacer(1, 5))

    # Section 2: Identificação da Entidade Executora
    elements.append(Paragraph("2. IDENTIFICAÇÃO DA ENTIDADE EXECUTORA", section_style))
    elements.append(Paragraph(f"<b>Nome:</b> {data.call_entity_name}", normal_style))
    elements.append(Paragraph(f"<b>CNPJ:</b> {_format_cnpj(data.call_entity_cnpj)}", normal_style))
    elements.append(Spacer(1, 5))

    # Section 3: Identificação do Fornecedor
    elements.append(Paragraph("3. IDENTIFICAÇÃO DO FORNECEDOR", section_style))
    elements.append(Paragraph(f"<b>Nome/Razão Social:</b> {data.producer_name}", normal_style))
    producer_type_str = _format_producer_type(data.producer_type)
    elements.append(Paragraph(f"<b>Tipo:</b> {producer_type_str}", normal_style))

    doc_label = "CNPJ" if len(data.producer_document) == 14 else "CPF"
    doc_formatted = (
        _format_cnpj(data.producer_document)
        if len(data.producer_document) == 14
        else _format_cpf(data.producer_document)
    )
    elements.append(Paragraph(f"<b>{doc_label}:</b> {doc_formatted}", normal_style))
    elements.append(Paragraph(f"<b>DAP/CAF:</b> {data.producer_dap_caf}", normal_style))
    elements.append(Paragraph(f"<b>Endereço:</b> {data.producer_address}", normal_style))
    elements.append(
        Paragraph(
            f"<b>Cidade/UF:</b> {data.producer_city} - {data.producer_state}",
            normal_style,
        )
    )
    elements.append(Spacer(1, 10))

    # Section 4: Relação de Produtos
    elements.append(Paragraph("4. RELAÇÃO DE PRODUTOS", section_style))

    # Products table
    table_data = [["Produto", "Unidade", "Quantidade", "Preço Unit.", "Total", "Cronograma"]]

    for item in data.project.items:
        table_data.append(
            [
                item.product_name,
                item.unit,
                f"{item.quantity:.2f}",
                f"R$ {item.unit_price:.2f}",
                f"R$ {item.total:.2f}",
                item.delivery_schedule,
            ]
        )

    # Add total row
    table_data.append(
        [
            "",
            "",
            "",
            "",
            f"R$ {data.project.total_value:.2f}",
            "TOTAL",
        ]
    )

    table = Table(table_data, colWidths=[4 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm])
    table.setStyle(
        TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                # Body
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ALIGN", (2, 1), (-2, -1), "RIGHT"),  # Numbers right-aligned
                # Total row
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Section 5: Total do Projeto
    elements.append(Paragraph("5. VALOR TOTAL DO PROJETO", section_style))
    elements.append(
        Paragraph(
            f"<b>Valor Total: R$ {data.project.total_value:.2f}</b>",
            normal_style,
        )
    )
    elements.append(Spacer(1, 30))

    # Footer with date and signature
    elements.append(Paragraph("6. DECLARAÇÃO E ASSINATURA", section_style))
    elements.append(
        Paragraph(
            "Declaro estar ciente das condições estabelecidas na Chamada Pública "
            "e me comprometo a fornecer os produtos nas condições especificadas.",
            normal_style,
        )
    )
    elements.append(Spacer(1, 20))

    # Date
    today = datetime.now().strftime("%d/%m/%Y")
    elements.append(
        Paragraph(
            f"Data: {today}",
            normal_style,
        )
    )
    elements.append(Spacer(1, 30))

    # Signature line
    elements.append(
        Paragraph(
            "_" * 50,
            ParagraphStyle("Signature", parent=normal_style, alignment=1),
        )
    )
    elements.append(
        Paragraph(
            f"{data.producer_name}",
            ParagraphStyle("SignatureName", parent=normal_style, alignment=1),
        )
    )
    elements.append(
        Paragraph(
            "Assinatura do Fornecedor",
            ParagraphStyle("SignatureLabel", parent=normal_style, alignment=1, fontSize=8),
        )
    )

    # Build PDF
    doc.build(elements)

    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


def _format_cnpj(cnpj: str) -> str:
    """Format CNPJ with punctuation."""
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def _format_cpf(cpf: str) -> str:
    """Format CPF with punctuation."""
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def _format_producer_type(producer_type: str) -> str:
    """Format producer type for display."""
    types = {
        "formal": "Grupo Formal (Cooperativa/Associação)",
        "informal": "Grupo Informal",
        "individual": "Fornecedor Individual",
    }
    return types.get(producer_type, producer_type)

