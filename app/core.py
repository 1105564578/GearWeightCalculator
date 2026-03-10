from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


FIELD_COUNT = 5
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_SORT_RULES = 3
TEXT_SORT_FIELDS = {"category", "name"}


@dataclass
class CalculationSnapshot:
    attrs: list[float]
    weights: list[float]
    threshold: float
    contributions: list[float]
    score: float
    passed: bool


@dataclass
class EquipRecord:
    category: str
    name: str
    attrs: list[float]
    weights: list[float]
    score: float
    pass_threshold: bool
    created_at: str

    def to_export_row(self) -> list[str]:
        return [
            self.category,
            self.name,
            *[_fmt_number(v) for v in self.attrs[:FIELD_COUNT]],
            *[_fmt_number(v) for v in self.weights[:FIELD_COUNT]],
            f"{self.score:.3f}",
            "true" if self.pass_threshold else "false",
            self.created_at,
        ]


def parse_float(text: str, field_label: str) -> tuple[float, bool, str | None]:
    cleaned = text.strip()
    if cleaned == "":
        return 0.0, True, None
    try:
        return float(cleaned), True, None
    except ValueError:
        label = field_label or "数值"
        return 0.0, False, f"{label} 不是合法数字，已按 0 处理。"


def safe_numeric_list(
    texts: Iterable[str],
    field_prefix: str,
) -> tuple[list[float], list[str], list[int]]:
    values: list[float] = []
    errors: list[str] = []
    invalid_indexes: list[int] = []

    for idx, text in enumerate(texts, start=1):
        value, ok, err = parse_float(text, f"{field_prefix}{idx}")
        values.append(value)
        if not ok and err:
            errors.append(err)
            invalid_indexes.append(idx - 1)

    return values, errors, invalid_indexes


def compute_contributions(attrs: list[float], weights: list[float]) -> list[float]:
    return [a * w for a, w in zip(attrs[:FIELD_COUNT], weights[:FIELD_COUNT])]


def evaluate_threshold(score: float, threshold: float) -> bool:
    return score >= threshold


def calculate(attrs: list[float], weights: list[float], threshold: float) -> CalculationSnapshot:
    contributions = compute_contributions(attrs, weights)
    score = sum(contributions)
    passed = evaluate_threshold(score, threshold)
    return CalculationSnapshot(
        attrs=attrs[:FIELD_COUNT],
        weights=weights[:FIELD_COUNT],
        threshold=threshold,
        contributions=contributions,
        score=score,
        passed=passed,
    )


def sort_records(
    records: list[EquipRecord],
    rules: list[tuple[str, bool]],
) -> tuple[list[EquipRecord], list[str]]:
    trimmed_rules = (rules or [("score", False)])[:MAX_SORT_RULES]
    result = list(records)
    warnings: list[str] = []

    for field, asc in reversed(trimmed_rules):
        if field == "created_at":
            result = sorted(
                result,
                key=lambda record: _to_datetime(record.created_at, warnings),
                reverse=not asc,
            )
            continue

        if field in TEXT_SORT_FIELDS:
            result = sorted(
                result,
                key=lambda record: _to_text(_extract_text_field(record, field)),
                reverse=not asc,
            )
            continue

        result = sorted(
            result,
            key=lambda record: _to_float(_extract_numeric_field(record, field), field, warnings),
            reverse=not asc,
        )

    return result, sorted(set(warnings))


def _extract_numeric_field(record: EquipRecord, field: str) -> Any:
    if field == "score":
        return record.score
    if field.startswith("a"):
        try:
            idx = int(field[1:]) - 1
            return record.attrs[idx]
        except (ValueError, IndexError):
            return 0.0
    return 0.0


def _extract_text_field(record: EquipRecord, field: str) -> str:
    if field == "category":
        return record.category
    if field == "name":
        return record.name
    return ""


def _to_float(value: Any, field: str, warnings: list[str]) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = "" if value is None else str(value).strip()
    if text == "":
        warnings.append(f"排序字段 {field} 存在空值，已按 0 处理。")
        return 0.0
    try:
        return float(text)
    except ValueError:
        warnings.append(f"排序字段 {field} 存在非法值 {text!r}，已按 0 处理。")
        return 0.0


def _to_datetime(value: Any, warnings: list[str]) -> datetime:
    if isinstance(value, datetime):
        return value
    text = "" if value is None else str(value).strip()
    if text == "":
        warnings.append("排序字段 created_at 存在空值，已按最早时间处理。")
        return datetime.min
    try:
        return datetime.strptime(text, TIME_FORMAT)
    except ValueError:
        warnings.append(f"排序字段 created_at 存在非法时间 {text!r}，已按最早时间处理。")
        return datetime.min


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _fmt_number(value: float) -> str:
    return f"{value:g}"
