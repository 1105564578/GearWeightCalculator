from __future__ import annotations

import csv

from app.core import EquipRecord


SCHEME_HEADER = ["attr_name", "weight_name", "weight"]
FIXED_EXPORT_SUFFIX = ["score", "pass_threshold", "created_at"]


def save_scheme_csv(
    file_path: str,
    attr_names: list[str],
    weight_names: list[str],
    weights: list[float],
) -> None:
    row_count = max(len(attr_names), len(weight_names), len(weights), 1)
    fixed_attr_names = _normalize_text_list(attr_names, row_count)
    fixed_weight_names = _normalize_text_list(weight_names, row_count)
    fixed_weights = _normalize_float_list(weights, row_count)

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(SCHEME_HEADER)
        for idx in range(row_count):
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

    for idx, row in enumerate(rows, start=1):
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

    if not attr_names:
        attr_names = [""]
        weight_names = [""]
        weights = [0.0]

    return attr_names, weight_names, weights, warnings


def export_equips_csv(file_path: str, records: list[EquipRecord]) -> None:
    field_count = max((max(len(record.attrs), len(record.weights)) for record in records), default=1)
    header = _build_equip_header(field_count)

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for record in records:
            writer.writerow(record.to_export_row(field_count))


def import_equips_csv(file_path: str) -> tuple[list[EquipRecord], list[str]]:
    records: list[EquipRecord] = []
    warnings: list[str] = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头。")
        normalized = [name.strip() for name in reader.fieldnames]

        has_category = normalized[:2] == ["category", "name"]
        if not has_category and (not normalized or normalized[0] != "name"):
            raise ValueError("装备 CSV 表头必须以 category,name 或 name 开头。")

        field_count = _detect_field_count(normalized, has_category)
        expected = _build_equip_header(field_count, include_category=has_category)
        if normalized != expected:
            raise ValueError("装备 CSV 表头不匹配，请检查 a1..an / w1..wn 列是否成对且顺序正确。")

        for line_no, row in enumerate(reader, start=2):
            category = (row.get("category") or "").strip() if has_category else ""
            category = category or "通用"
            name = (row.get("name") or "").strip()
            attrs = [_safe_float(row.get(f"a{i}"), f"a{i}", line_no, warnings) for i in range(1, field_count + 1)]
            weights = [_safe_float(row.get(f"w{i}"), f"w{i}", line_no, warnings) for i in range(1, field_count + 1)]
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


def _build_equip_header(field_count: int, include_category: bool = True) -> list[str]:
    header = ["name"]
    if include_category:
        header = ["category", "name"]
    header.extend([f"a{i}" for i in range(1, field_count + 1)])
    header.extend([f"w{i}" for i in range(1, field_count + 1)])
    header.extend(FIXED_EXPORT_SUFFIX)
    return header


def _detect_field_count(headers: list[str], include_category: bool) -> int:
    start_idx = 2 if include_category else 1
    suffix_start = len(headers) - len(FIXED_EXPORT_SUFFIX)
    variable_headers = headers[start_idx:suffix_start]
    if len(variable_headers) % 2 != 0 or not variable_headers:
        raise ValueError("装备 CSV 属性列数量不正确。")
    field_count = len(variable_headers) // 2
    expected_attrs = [f"a{i}" for i in range(1, field_count + 1)]
    expected_weights = [f"w{i}" for i in range(1, field_count + 1)]
    if variable_headers[:field_count] != expected_attrs or variable_headers[field_count:] != expected_weights:
        raise ValueError("装备 CSV 属性列命名不正确。")
    return field_count


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
    return text in {"true", "1", "yes", "y", "是"}
