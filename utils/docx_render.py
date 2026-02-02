from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUT_DIR = BASE_DIR / "data" / "out"


def replace_placeholders(text: str, data: dict) -> str:
    for key, value in data.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def apply_font(run):
    """
    Жёстко задаёт Times New Roman 9
    для ВСЕХ типов шрифтов Word (ascii, hAnsi, eastAsia, cs)
    """
    run.font.size = Pt(9)

    rPr = run._element.get_or_add_rPr()

    # удаляем старые rFonts, если были
    for el in rPr.findall(qn("w:rFonts")):
        rPr.remove(el)

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:eastAsia"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")

    rPr.append(rFonts)


def process_paragraph(paragraph, data: dict):
    if "{{" not in paragraph.text:
        return

    new_text = replace_placeholders(paragraph.text, data)

    paragraph.clear()
    run = paragraph.add_run(new_text)
    apply_font(run)


def render_docx(template_name: str, data: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    template_path = TEMPLATES_DIR / template_name
    doc = Document(template_path)

    # ===== обычный текст =====
    for paragraph in doc.paragraphs:
        process_paragraph(paragraph, data)

    # ===== таблицы =====
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    process_paragraph(paragraph, data)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = OUT_DIR / f"service_task_{ts}.docx"
    doc.save(out_path)

    return out_path
