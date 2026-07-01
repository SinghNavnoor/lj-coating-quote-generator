def calculate_quote(materials: list, num_workers: int, hourly_rate: float, hours: float) -> dict:
    materials_total = round(sum(item.get("cost", 0.0) for item in materials), 2)
    labor_total = round(num_workers * hourly_rate * hours, 2)
    grand_total = round(materials_total + labor_total, 2)
    return {
        "materials": materials,
        "materials_total": materials_total,
        "labor": {
            "num_workers": num_workers,
            "hourly_rate": hourly_rate,
            "hours": hours,
        },
        "labor_total": labor_total,
        "grand_total": grand_total,
    }
