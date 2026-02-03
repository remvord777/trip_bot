from pathlib import Path
from docx import Document
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUT_DIR = BASE_DIR / "data" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def render_docx(template_name: str, data: dict) -> Path:
    template_path = TEMPLATES_DIR / template_name
    doc = Document(template_path)

    for p in doc.paragraphs:
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in p.text:
                p.text = p.text.replace(placeholder, str(value))

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = OUT_DIR / f"service_task_{ts}.docx"
    doc.save(out_path)

    return out_path
