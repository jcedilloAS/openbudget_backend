from io import BytesIO
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

from app.core.config import settings


# ── Color palette ────────────────────────────────────────────────────────────
PRIMARY      = colors.HexColor("#1e3a5f")   # dark navy
ACCENT       = colors.HexColor("#2563eb")   # blue
ALT_ROW      = colors.HexColor("#f1f5f9")   # light grey for alternating rows
HEADER_TEXT  = colors.white

STATUS_COLORS = {
    "draft":      colors.HexColor("#94a3b8"),  # slate-400
    "submitted":  colors.HexColor("#f59e0b"),  # amber-500
    "approved":   colors.HexColor("#16a34a"),  # green-600
    "rejected":   colors.HexColor("#dc2626"),  # red-600
    "cancelled":  colors.HexColor("#475569"),  # slate-600
    "pending":    colors.HexColor("#94a3b8"),
}

STATUS_LABELS = {
    "draft":      "BORRADOR",
    "submitted":  "ENVIADA",
    "approved":   "APROBADA",
    "rejected":   "RECHAZADA",
    "cancelled":  "CANCELADA",
    "pending":    "PENDIENTE",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt_currency(value, currency: str = "MXN") -> str:
    if value is None:
        return f"$0.00 {currency}"
    try:
        return f"${Decimal(str(value)):,.2f} {currency}"
    except Exception:
        return str(value)


def _fmt_date(dt) -> str:
    if dt is None:
        return "—"
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y %H:%M")
    return str(dt)


def _safe(value, fallback: str = "—") -> str:
    return str(value) if value is not None else fallback


# ── Main generator ────────────────────────────────────────────────────────────

def _build_logo_flowable(logo_url: str, max_height: float = 1.8 * cm):
    """Return an Image or RLG drawing for the given logo URL, or None on failure."""
    try:
        rel = logo_url.lstrip("/")
        # logo_url is like /uploads/logos/file.ext; UPLOAD_DIR is /app/uploads
        file_path = Path(settings.UPLOAD_DIR) / Path(rel).relative_to("uploads")
        if not file_path.exists():
            return None
        ext = file_path.suffix.lower()
        if ext == ".svg":
            from svglib.svglib import svg2rlg
            drawing = svg2rlg(str(file_path))
            if drawing is None:
                return None
            scale = max_height / drawing.height
            drawing.width *= scale
            drawing.height = max_height
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            return drawing
        else:
            img = Image(str(file_path))
            aspect = img.imageWidth / img.imageHeight
            img.drawHeight = max_height
            img.drawWidth = max_height * aspect
            return img
    except Exception:
        return None


def generate_requisition_pdf(req, sys_config: Optional[object] = None) -> bytes:
    """
    Generate a PDF for the given Requisition ORM object.
    Expects relationships already loaded: project, supplier, requester, items, retention.
    Returns the PDF content as bytes.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── 1. Header row: logo left / requisition info right ─────────────────
    info_right_style = ParagraphStyle(
        "InfoRight",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_RIGHT,
        leading=14,
    )

    status_color = STATUS_COLORS.get(req.status, colors.grey)
    status_label = STATUS_LABELS.get(req.status, req.status.upper())

    logo_cell: list = []
    if sys_config and sys_config.logo_url:
        logo_flowable = _build_logo_flowable(sys_config.logo_url)
        if logo_flowable:
            logo_cell.append(logo_flowable)

    header_data = [[
        logo_cell,
        [
            Paragraph("<b>REQUISICIÓN</b>", info_right_style),
            Paragraph(f"No. <b>{_safe(req.requisition_number)}</b>", info_right_style),
            Paragraph(f"Fecha: <b>{_fmt_date(req.created_at)}</b>", info_right_style),
        ],
    ]]

    header_table = Table(header_data, colWidths=["55%", "45%"])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.4 * cm))

    # ── 2. Status badge ───────────────────────────────────────────────────
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    badge_data = [[Paragraph(status_label, badge_style)]]
    badge_table = Table(badge_data, colWidths=[4 * cm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_color),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── 3. Info section: project | supplier | requester ───────────────────
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#64748b"),
        spaceAfter=2,
    )
    field_label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
    )
    field_value_style = ParagraphStyle(
        "FieldValue",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )

    def info_cell(label: str, value: str):
        return [
            Paragraph(label, field_label_style),
            Paragraph(value, field_value_style),
        ]

    # Project
    project = req.project
    project_name = _safe(project.name if project else None)
    project_code = _safe(project.project_code if project else None)

    # Supplier
    supplier = req.supplier
    supplier_name  = _safe(supplier.name if supplier else None, "Sin proveedor")
    supplier_rfc   = _safe(supplier.rfc if supplier else None)
    supplier_city  = _safe(supplier.city if supplier else None)

    # Requester
    requester = req.requester
    requester_name  = _safe(requester.name if requester else None)
    requester_email = _safe(requester.email if requester else None)

    currency = _safe(req.currency, "MXN")
    exchange_rate = _safe(req.exchange_rate, "1.0000")

    info_data = [[
        # Column 1 — project
        [
            Paragraph("PROYECTO", section_header_style),
            *info_cell("Nombre", project_name),
            *info_cell("Código", project_code),
        ],
        # Column 2 — supplier
        [
            Paragraph("PROVEEDOR", section_header_style),
            *info_cell("Nombre", supplier_name),
            *info_cell("RFC", supplier_rfc),
            *info_cell("Ciudad", supplier_city),
        ],
        # Column 3 — requester + currency
        [
            Paragraph("SOLICITANTE", section_header_style),
            *info_cell("Nombre", requester_name),
            *info_cell("Email", requester_email),
            *info_cell("Moneda", f"{currency}  (T/C: {exchange_rate})"),
        ],
    ]]

    info_table = Table(info_data, colWidths=["33%", "33%", "34%"])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEAFTER", (0, 0), (1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── 4. Items table ────────────────────────────────────────────────────
    story.append(Paragraph("PARTIDAS", section_header_style))
    story.append(Spacer(1, 0.2 * cm))

    col_header_style = ParagraphStyle(
        "ColHeader",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=HEADER_TEXT,
        alignment=TA_CENTER,
    )
    cell_center_style = ParagraphStyle(
        "CellCenter", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER
    )
    cell_right_style = ParagraphStyle(
        "CellRight", parent=styles["Normal"], fontSize=8, alignment=TA_RIGHT
    )
    cell_left_style = ParagraphStyle(
        "CellLeft", parent=styles["Normal"], fontSize=8, alignment=TA_LEFT, leading=10
    )

    items_header = [
        Paragraph("#", col_header_style),
        Paragraph("Artículo", col_header_style),
        Paragraph("Descripción", col_header_style),
        Paragraph("Cant.", col_header_style),
        Paragraph("U.Med.", col_header_style),
        Paragraph("Precio Unit.", col_header_style),
        Paragraph("Total", col_header_style),
    ]

    col_widths = [0.8 * cm, 3.5 * cm, 5.5 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm]
    items_rows = [items_header]

    items = req.items or []
    for idx, item in enumerate(items, start=1):
        try:
            qty = f"{Decimal(str(item.quantity)):,.4f}".rstrip("0").rstrip(".")
        except Exception:
            qty = str(item.quantity)

        desc_text = _safe(item.description)
        if item.account_id and item.account:
            acc = item.account
            acc_info = _safe(acc.account_number)
            if acc.description:
                acc_info += f" - {acc.description}"
            desc_text += f'<br/><font size="7" color="#64748b"><b>Cuenta:</b> {acc_info}</font>'

        row = [
            Paragraph(str(idx), cell_center_style),
            Paragraph(_safe(item.item_name), cell_left_style),
            Paragraph(desc_text, cell_left_style),
            Paragraph(qty, cell_center_style),
            Paragraph(_safe(item.unit), cell_center_style),
            Paragraph(_fmt_currency(item.unit_price, ""), cell_right_style),
            Paragraph(_fmt_currency(item.total_amount, ""), cell_right_style),
        ]
        items_rows.append(row)

    if not items:
        items_rows.append([
            Paragraph("", cell_center_style),
            Paragraph("Sin partidas registradas", cell_left_style),
            Paragraph("", cell_left_style),
            Paragraph("", cell_center_style),
            Paragraph("", cell_center_style),
            Paragraph("", cell_right_style),
            Paragraph("", cell_right_style),
        ])

    items_table = Table(items_rows, colWidths=col_widths, repeatRows=1)

    item_style_cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_TEXT),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # All cells
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
    ]
    items_table.setStyle(TableStyle(item_style_cmds))
    story.append(items_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── 5. Totals block ───────────────────────────────────────────────────
    label_style = ParagraphStyle(
        "TotalLabel", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT
    )
    value_style = ParagraphStyle(
        "TotalValue",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        alignment=TA_RIGHT,
    )
    grand_label_style = ParagraphStyle(
        "GrandLabel",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=HEADER_TEXT,
        alignment=TA_RIGHT,
    )
    grand_value_style = ParagraphStyle(
        "GrandValue",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=HEADER_TEXT,
        alignment=TA_RIGHT,
    )

    iva_pct = _safe(req.iva_percentage, "0")

    totals_data = [
        [Paragraph("Subtotal", label_style),       Paragraph(_fmt_currency(req.subtotal, currency), value_style)],
        [Paragraph(f"IVA ({iva_pct}%)", label_style), Paragraph(_fmt_currency(req.iva_amount, currency), value_style)],
    ]

    for req_ret in (req.retentions or []):
        ret = req_ret.retention
        if ret is None:
            continue
        ret_label = f"Retención ({ret.code} – {_safe(ret.percentage)}%)"
        if ret.description:
            ret_label += f" {ret.description}"
        if req_ret.retention_amount and Decimal(str(req_ret.retention_amount)) != 0:
            totals_data.append([
                Paragraph(ret_label, label_style),
                Paragraph(f"- {_fmt_currency(req_ret.retention_amount, currency)}", value_style),
            ])

    totals_data.append([
        Paragraph("TOTAL", grand_label_style),
        Paragraph(_fmt_currency(req.total_amount, currency), grand_value_style),
    ])

    totals_table = Table(totals_data, colWidths=[None, 5 * cm], hAlign="RIGHT")
    last_row = len(totals_data) - 1
    totals_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1, PRIMARY),
        ("BACKGROUND", (0, last_row), (-1, last_row), PRIMARY),
        ("ROWBACKGROUNDS", (0, 0), (-1, last_row - 1), [colors.white, ALT_ROW]),
        ("GRID", (0, 0), (-1, last_row - 1), 0.25, colors.HexColor("#e2e8f0")),
    ]))
    story.append(totals_table)

    # ── 6. Authorization info ─────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("AUTORIZACIÓN", section_header_style))
    story.append(Spacer(1, 0.2 * cm))

    approved_header_style = ParagraphStyle(
        "ApprovedHeader",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#16a34a"),
        spaceAfter=2,
    )
    rejected_header_style = ParagraphStyle(
        "RejectedHeader",
        parent=styles["Normal"],
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#dc2626"),
        spaceAfter=2,
    )

    # Column 1 — who requested
    req_col = [
        Paragraph("SOLICITADO POR", section_header_style),
        *info_cell("Nombre", requester_name),
        *info_cell("Email", requester_email),
        *info_cell("Fecha de solicitud", _fmt_date(req.created_at)),
    ]

    # Column 2 — who approved or rejected (conditional)
    action_col = None
    if req.status == "approved" and req.approver:
        approver = req.approver
        action_col = [
            Paragraph("APROBADO POR", approved_header_style),
            *info_cell("Nombre", _safe(approver.name)),
            *info_cell("Email", _safe(approver.email)),
            *info_cell("Fecha de aprobación", _fmt_date(req.approved_at)),
        ]
    elif req.status == "rejected" and req.rejector:
        rejector = req.rejector
        action_col = [
            Paragraph("RECHAZADO POR", rejected_header_style),
            *info_cell("Nombre", _safe(rejector.name)),
            *info_cell("Email", _safe(rejector.email)),
            *info_cell("Fecha de rechazo", _fmt_date(req.rejected_at)),
        ]

    if action_col:
        auth_data = [[req_col, action_col]]
        auth_table = Table(auth_data, colWidths=["50%", "50%"])
        auth_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
    else:
        auth_data = [[req_col]]
        auth_table = Table(auth_data, colWidths=["50%"])
        auth_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))

    story.append(auth_table)

    # ── 7. Rejection reason (conditional) ────────────────────────────────
    if req.status == "rejected" and req.rejection_reason:
        story.append(Spacer(1, 0.6 * cm))
        rejection_box_data = [[
            Paragraph(
                f"<b>Motivo de rechazo:</b> {req.rejection_reason}",
                ParagraphStyle(
                    "Rejection",
                    parent=styles["Normal"],
                    fontSize=9,
                    textColor=colors.HexColor("#7f1d1d"),
                ),
            )
        ]]
        rejection_table = Table(rejection_box_data, colWidths=["100%"])
        rejection_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#dc2626")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(rejection_table)

    # ── 8. Footer ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.2 * cm))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
    )
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    company = sys_config.company_name if sys_config and sys_config.company_name else ""
    footer_parts = [f"Documento generado el {generated_at}", req.requisition_number]
    if company:
        footer_parts.insert(1, company)
    story.append(Paragraph(" · ".join(footer_parts), footer_style))

    doc.build(story)
    return buffer.getvalue()
