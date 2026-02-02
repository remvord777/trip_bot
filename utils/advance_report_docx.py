from docx import Document
from datetime import date
import os


def generate_advance_report_docx(data: dict) -> str:
    template_path = "templates/advance_report.docx"
    doc = Document(template_path)

    for p in doc.paragraphs:
        for key, value in data.items():
            p.text = p.text.replace(f"{{{{{key}}}}}", str(value))

    out_dir = "storage/advance_reports/generated"
    os.makedirs(out_dir, exist_ok=True)

    filename = f"advance_report_{date.today().strftime('%Y%m%d')}.docx"
    path = os.path.join(out_dir, filename)

    doc.save(path)
    return path
