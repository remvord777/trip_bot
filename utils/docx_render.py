from docx import Document
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "generated"

OUTPUT_DIR.mkdir(exist_ok=True)


def render_docx(template_name: str, data: dict) -> Path:
    template_path = TEMPLATES_DIR / template_name
    doc = Document(template_path)

    replacements = {
        "{{employee_name}}": data.get("employee_name", ""),
        "{{position}}": data.get("position", ""),
        "{{city}}": f"{data.get('settlement_prefix', '')} {data.get('city', '')}",
        "{{object}}": data.get("object_name", ""),
        "{{organization}}": data.get("organization", ""),
        "{{contract}}": data.get("contract", ""),
        "{{date_from}}": data.get("date_from", ""),
        "{{date_to}}": data.get("date_to", ""),
        "{{total}}": str(data.get("total", "")),
        "{{purpose}}": data.get("service", ""),
        "{{advance_amount}}": str(data.get("advance_amount", "")),
        "{{apply_date}}": data.get("apply_date", ""),
    }

    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, value)

    filename = f"{template_name.replace('.docx', '')}_{datetime.now():%Y-%m-%d_%H-%M-%S}.docx"
    output_path = OUTPUT_DIR / filename
    doc.save(output_path)

    return output_path
