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

    # сохраняем стиль первого run
    first_run = paragraph.runs[0]

    # очищаем все runs
    for run in paragraph.runs:
        run.text = ""

    # записываем текст в первый run
    first_run.text = full_text


def render_docx(template_name: str, data: dict) -> Path:
    template_path = TEMPLATES_DIR / template_name
    doc = Document(template_path)

    replacements = {
        "{{employee_name}}": data.get("employee_name", ""),
        "{{employee_short}}": data.get("employee_short", ""),
        "{{position}}": data.get("position", ""),
        "{{city}}": f"{data.get('settlement_prefix', '')} {data.get('city', '')}".strip(),
        "{{object}}": data.get("object_name", ""),
        "{{contract}}": data.get("contract", ""),
        "{{date_from}}": data.get("date_from", ""),
        "{{date_to}}": data.get("date_to", ""),
        "{{total}}": str(data.get("total", "")),
        "{{purpose}}": data.get("service", ""),
        "{{advance_amount}}": str(data.get("advance_amount", "")),
        "{{apply_date}}": datetime.now().strftime("%d.%m.%Y"),
    }

    # ===== ПАРАГРАФЫ =====
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, replacements)

    # ===== ТАБЛИЦЫ =====
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, replacements)

    # ===== ИМЯ ФАЙЛА =====
    doc_type = FILE_TITLES.get(template_name, "документ")
    surname = data.get("employee_name", "").split()[0]
    date_from = data.get("date_from", "")
    date_to = data.get("date_to", "")

    filename = f"ИМ_{doc_type}_{surname}_{date_from}–{date_to}.docx"

    output_path = OUTPUT_DIR / filename
    doc.save(output_path)

    return output_path
