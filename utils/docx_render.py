from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from pathlib import Path
from datetime import datetime


FONT_NAME = "Times New Roman"
FONT_SIZE = 9


def apply_font(run):
    run.font.name = FONT_NAME
    run.font.size = Pt(FONT_SIZE)

    # важно для Word (иначе может остаться Calibri)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)


def replace_in_paragraph(paragraph, data: dict):
    full_text = "".join(run.text for run in paragraph.runs)

    replaced = False
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder in full_text:
            full_text = full_text.replace(placeholder, str(value))
            replaced = True

    if replaced:
        paragraph.clear()
        run = paragraph.add_run(full_text)
        apply_font(run)


def replace_in_table(table, data: dict):
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                replace_in_paragraph(paragraph, data)


def render_docx(template_name: str, data: dict) -> Path:
    base_dir = Path(__file__).resolve().parents[1]
    template_path = base_dir / "templates" / template_name

    out_dir = base_dir / "data" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = out_dir / f"service_task_{timestamp}.docx"

    doc = Document(template_path)

    # обычный текст
    for paragraph in doc.paragraphs:
        replace_in_paragraph(paragraph, data)

    # таблицы
    for table in doc.tables:
        replace_in_table(table, data)

    doc.save(out_file)
    return out_file
