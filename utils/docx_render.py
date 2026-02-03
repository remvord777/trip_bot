from docx import Document
from pathlib import Path
from datetime import datetime


def render_docx(template_name: str, data: dict) -> Path:
    templates_dir = Path("templates")
    out_dir = Path("data/out")

    out_dir.mkdir(parents=True, exist_ok=True)

    template_path = templates_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Шаблон не найден: {template_path}")

    doc = Document(template_path)

    for p in doc.paragraphs:
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in p.text:
                p.text = p.text.replace(placeholder, str(value))

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = out_dir / f"service_task_{ts}.docx"

    doc.save(out_path)

    if not out_path.exists():
        raise RuntimeError("DOCX файл не был создан")

    return out_path
