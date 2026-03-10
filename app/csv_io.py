from __future__ import annotations

import csv

from app.core import EquipRecord


SCHEME_HEADER = ["attr_name", "weight_name", "weight"]
SCHEME_ROW_COUNT = 5

EQUIP_HEADER_V2 = [
    "category",
    "name",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "w1",
    "w2",
    "w3",
    "w4",
    "w5",
    "score",
    "pass_threshold",
    "created_at",
]

EQUIP_HEADER_V1 = [
    "name",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "w1",
    "w2",
    "w3",
    "w4",
    "w5",
    "score",
    "pass_threshold",
    "created_at",
]


def save_scheme_csv(
    file_path: str,
    attr_names: list[str],
    weight_names: list[str],
    weights: list[float],
) -> None:
    fixed_attr_names = _normalize_text_list(attr_names, SCHEME_ROW_COUNT)
    fixed_weight_names = _normalize_text_list(weight_names, SCHEME_ROW_COUNT)
    fixed_weights = _normalize_float_list(weights, SCHEME_ROW_COUNT)

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SCHEME_HEADER)
        for idx in range(SCHEME_ROW_COUNT):
            writer.writerow([fixed_attr_names[idx], fixed_weight_names[idx], f"{fixed_weights[idx]:g}"])


def load_scheme_csv(file_path: str) -> tuple[list[str], list[str], list[float], list[str]]:
    attr_names: list[str] = []
    weight_names: list[str] = []
    weights: list[float] = []
    warnings: list[str] = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头。")
        if [name.strip() for name in reader.fieldnames] != SCHEME_HEADER:
            raise ValueError("方案 CSV 表头必须是 attr_name,weight_name,weight")
        rows = list(reader)

    for idx, row in enumerate(rows[:SCHEME_ROW_COUNT], start=1):
        attr_names.append((row.get("attr_name") or "").strip())
        weight_names.append((row.get("weight_name") or "").strip())

        raw_weight = (row.get("weight") or "").strip()
        if raw_weight == "":
            weights.append(0.0)
            continue
        try:
            weights.append(float(raw_weight))
        except ValueError:
            weights.append(0.0)
            warnings.append(f"第 {idx} 行 weight 非法，已按 0 处理。")

    while len(attr_names) < SCHEME_ROW_COUNT:
        attr_names.append("")
        weight_names.append("")
        weights.append(0.0)

    return attr_names, weight_names, weights, warnings


def export_equips_csv(file_path: str, records: list[EquipRecord]) -> None:
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(EQUIP_HEADER_V2)
        for record in records:
            writer.writerow(record.to_export_row())


def import_equips_csv(file_path: str) -> tuple[list[EquipRecord], list[str]]:
    records: list[EquipRecord] = []
    warnings: list[str] = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头。")
        normalized = [name.strip() for name in reader.fieldnames]
        if normalized != EQUIP_HEADER_V1 and normalized != EQUIP_HEADER_V2:
            raise ValueError(
                "装备 CSV 表头必须是 category,name,a1,a2,a3,a4,a5,w1,w2,w3,w4,w5,score,pass_threshold,created_at"
            )

        for line_no, row in enumerate(reader, start=2):
            category = (row.get("category") or "").strip() or "通用"
            name = (row.get("name") or "").strip()
            attrs = [_safe_float(row.get(f"a{i}"), f"a{i}", line_no, warnings) for i in range(1, 6)]
            weights = [_safe_float(row.get(f"w{i}"), f"w{i}", line_no, warnings) for i in range(1, 6)]
            score = _safe_float(row.get("score"), "score", line_no, warnings)
            pass_threshold = _safe_bool(row.get("pass_threshold"))
            created_at = (row.get("created_at") or "").strip()

            records.append(
                EquipRecord(
                    category=category,
                    name=name,
                    attrs=attrs,
                    weights=weights,
                    score=score,
                    pass_threshold=pass_threshold,
                    created_at=created_at,
                )
            )

    return records, sorted(set(warnings))


def _normalize_text_list(values: list[str], size: int) -> list[str]:
    fixed = [(v or "").strip() for v in values[:size]]
    while len(fixed) < size:
        fixed.append("")
    return fixed


def _normalize_float_list(values: list[float], size: int) -> list[float]:
    fixed = [float(v) for v in values[:size]]
    while len(fixed) < size:
        fixed.append(0.0)
    return fixed


def _safe_float(raw: str | None, field: str, line_no: int, warnings: list[str]) -> float:
    text = "" if raw is None else str(raw).strip()
    if text == "":
        return 0.0
    try:
        return float(text)
    except ValueError:
        warnings.append(f"第 {line_no} 行字段 {field} 非法，已按 0 处理。")
        return 0.0


def _safe_bool(raw: str | None) -> bool:
    text = "" if raw is None else str(raw).strip().lower()
    return text in {"true", "1", "yes", "y", "✅"}
