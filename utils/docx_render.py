from docx import Document
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "generated"

OUTPUT_DIR.mkdir(exist_ok=True)

FILE_TITLES = {
    "service_task.docx": "служебное_задание",
    "money_avans.docx": "заявление_командировка",
    "advance_report.docx": "авансовый_отчет",
}


def _replace_in_paragraph(paragraph, replacements: dict):
    full_text = paragraph.text
    replaced = False

    for key, value in replacements.items():
        if key in full_text:
            full_text = full_text.replace(key, value)
            replaced = True

    if not replaced:
        return

    first_run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()

    for run in paragraph.runs:
        run.text = ""

    first_run.text = full_text


def render_docx(template_name: str, data: dict) -> Path:
    template_path = TEMPLATES_DIR / template_name
    doc = Document(template_path)

    replacements = {
        # ===== СОТРУДНИК =====
        "{{employee_name}}": data.get("employee_name", ""),
        "{{employee_short}}": data.get("employee_short", ""),
        "{{position}}": data.get("position", ""),

        # ===== ОРГАНИЗАЦИЯ / ПОДРАЗДЕЛЕНИЕ =====
        "{{department}}": data.get("department", ""),

        # ===== ЛОКАЦИЯ =====
        "{{city}}": f"{data.get('settlement_prefix', '')} {data.get('city', '')}".strip(),
        "{{object}}": data.get("object_name", ""),
        "{{object_name}}": data.get("object_name", ""),


        # ===== ДОГОВОР / ОРГАНИЗАЦИЯ =====
        "{{contract}}": data.get("contract", ""),
        "{{organization}}": data.get("organization", ""),

        # ===== ДАТЫ =====
        "{{date_from}}": data.get("date_from", ""),
        "{{date_to}}": data.get("date_to", ""),
        "{{apply_date}}": data.get("apply_date", ""),
        "{{report_date}}": data.get("report_date", ""),

        # ===== АВАНС =====
        "{{advance_amount}}": str(data.get("advance_amount", "")),

        # ===== ПРОЧЕЕ =====
        "{{purpose}}": data.get("service", ""),
        "{{total}}": str(data.get("total", "")),
    }

    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, replacements)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, replacements)

    surname = data.get("employee_name", "").split()[0] if data.get("employee_name") else "без_фамилии"
    filename = f"ИМ_{FILE_TITLES.get(template_name)}_{surname}_{data.get('date_from')}–{data.get('date_to')}.docx"

    output_path = OUTPUT_DIR / filename
    doc.save(output_path)

    return output_path
