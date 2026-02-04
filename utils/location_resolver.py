from data.locations import LOCATIONS


def resolve_contract_by_object(object_name: str) -> str:
    for settlement in LOCATIONS.values():
        for obj in settlement.get("objects", {}).values():
            if obj.get("name") == object_name:
                return obj.get("contract", "")
    return ""
