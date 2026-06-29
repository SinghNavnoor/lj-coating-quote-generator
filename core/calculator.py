import yaml
from pathlib import Path


def load_sop():
    sop_path = Path(__file__).parent.parent / "config" / "sop.yaml"
    with open(sop_path, "r") as f:
        return yaml.safe_load(f)


def calculate_quote(sqft: float, tier: int, sop: dict) -> dict:
    tier_config = sop["tiers"][tier]
    rate = tier_config["rate_per_sqft"]
    total = round(sqft * rate, 2)

    return {
        "sqft": sqft,
        "tier": tier,
        "tier_label": tier_config["label"],
        "tier_description": tier_config["description"],
        "rate_per_sqft": rate,
        "total": total,
    }
