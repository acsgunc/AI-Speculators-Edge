from dataclasses import dataclass


@dataclass
class ThresholdRow:
    pct_label: str
    change: float
    target: float


def compute_thresholds(base_price: float, percentages: list[float]) -> tuple[list[ThresholdRow], list[ThresholdRow]]:
    buy_targets = []
    sell_targets = []

    for pct in percentages:
        change = round(base_price * pct / 100, 2)

        buy_targets.append(ThresholdRow(
            pct_label=f"-{pct}%",
            change=-change,
            target=round(base_price - change, 2),
        ))

        sell_targets.append(ThresholdRow(
            pct_label=f"+{pct}%",
            change=change,
            target=round(base_price + change, 2),
        ))

    return buy_targets, sell_targets


def parse_percentages(raw: str) -> list[float]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    values = sorted({abs(float(p)) for p in parts})
    if not values:
        raise ValueError("No valid percentages provided.")
    return values
