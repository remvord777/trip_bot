def build_subject(data: dict) -> str:
    return (
        f"Командировка {data['object_name']} "
        f"№{data['contract']}"
    )


def build_body(data: dict) -> str:
    return f"""
Добрый день.

Прошу оформить командировку на {data['object_name']}
с {data['date_from']} по {data['date_to']}.

Договор №{data['contract']}
«{data['object_name']}. {data['service']}»

Документы во вложении.

{data['signature']}
""".strip()
