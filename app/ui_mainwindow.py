from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import core as models
from app import csv_io
from app.core import EquipRecord, MAX_SORT_RULES, TIME_FORMAT, sort_records


ERROR_STYLE = "border: 1px solid #d93025;"
DEFAULT_ATTR_NAMES = [f"属性{i}" for i in range(1, 6)]
DEFAULT_COEFF_NAMES = [f"系数{i}" for i in range(1, 6)]
DEFAULT_CATEGORIES = ["通用", "武器", "头盔", "护甲", "鞋子"]
APP_DIRNAME = ".gear_weight_calculator"
ATTACK_SPEED_FLOOR = 0.25
DEFAULT_ATTACK_SPEED_TARGET = 0.25
DEFAULT_CRIT_TARGET = 50.0
DEFAULT_DODGE_TARGET = 40.0
SPEED_LABEL_WIDTH = 112
SPEED_INPUT_WIDTH = 200
SCORE_BASE_LABEL_WIDTH = 74
SCORE_BASE_INPUT_WIDTH = 190
SCORE_NAME_INPUT_WIDTH = 260
FORMULA_HEAD_WIDTH = 38
FORMULA_INPUT_WIDTH = 100
FORMULA_SYMBOL_WIDTH = 14
FORMULA_RESULT_WIDTH = 90
PERSONALITY_SPEED_OPTIONS: list[tuple[str, float]] = [
    ("普通（无效果）", 0.0),
    ("快手（攻速 +10%）", 10.0),
    ("英雄心态（攻速 +7%）", 7.0),
    ("迟钝（攻速 -10%）", -10.0),
]
PET_GEAR_SPEED_OPTIONS: list[tuple[str, float]] = [
    ("没有宠物装备（0%）", 0.0),
    ("蓝色宠物装备（+6%）", 6.0),
    ("紫色宠物装备（+9%）", 9.0),
    ("橙色宠物装备（+12%）", 12.0),
]
HUNTER_SPEED_QUALITY_OPTIONS: list[tuple[str, float]] = [
    ("蓝色（+10%）", 10.0),
    ("橙色（+20%）", 20.0),
    ("紫色（+30%）", 30.0),
]
CRIT_DODGE_QUALITY_OPTIONS: list[tuple[str, float]] = [
    ("紫色（+2）", 2.0),
    ("橙色（+0）", 0.0),
    ("蓝色（-2）", -2.0),
    ("白色（-4）", -4.0),
]
CAP_PET_GEAR_OPTIONS: list[tuple[str, float]] = [
    ("无（+0）", 0.0),
    ("蓝色（+6）", 6.0),
    ("紫色（+9）", 9.0),
    ("橙色（+12）", 12.0),
]
CRIT_DODGE_PRESETS: dict[str, dict[str, float]] = {
    "melee": {
        "crit_equip": 43.0,
        "crit_rune": 6.0,
        "crit_atlas": 17.0,
        "crit_self_full": 8.0,
        "crit_guild": 5.0,
        "crit_mystic": 10.0,
        "dodge_equip": 36.0,
        "dodge_rune": 6.0,
        "dodge_atlas": 0.0,
        "dodge_self_full": 8.0,
        "dodge_guild": 0.0,
        "dodge_mystic": 10.0,
        "quality": 2.0,
    },
    "ranged": {
        "crit_equip": 42.0,
        "crit_rune": 6.0,
        "crit_atlas": 17.0,
        "crit_self_full": 11.0,
        "crit_guild": 5.0,
        "crit_mystic": 10.0,
        "dodge_equip": 0.0,
        "dodge_rune": 0.0,
        "dodge_atlas": 0.0,
        "dodge_self_full": 11.0,
        "dodge_guild": 0.0,
        "dodge_mystic": 10.0,
        "quality": 2.0,
    },
}
RECOMMEND_STATS = ["攻速", "暴击", "命中", "闪避", "体力", "防御", "减伤"]
RECOMMEND_ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "common": {"攻速": 1.0, "暴击": 1.0, "命中": 1.0, "闪避": 1.0, "体力": 1.0, "防御": 1.0, "减伤": 1.0},
    "berserker": {"攻速": 1.4, "暴击": 1.3, "命中": 1.0, "闪避": 0.8, "体力": 1.1, "防御": 0.9, "减伤": 0.9},
    "paladin": {"攻速": 0.8, "暴击": 0.7, "命中": 0.9, "闪避": 1.0, "体力": 1.4, "防御": 1.4, "减伤": 1.3},
    "archer": {"攻速": 1.5, "暴击": 1.4, "命中": 1.2, "闪避": 1.0, "体力": 0.8, "防御": 0.7, "减伤": 0.7},
    "mage": {"攻速": 1.2, "暴击": 1.2, "命中": 1.3, "闪避": 1.0, "体力": 0.9, "防御": 0.8, "减伤": 0.8},
    "hunter": {"攻速": 1.4, "暴击": 1.3, "命中": 1.2, "闪避": 1.1, "体力": 0.9, "防御": 0.8, "减伤": 0.8},
}
RECOMMEND_GOAL_MULTIPLIERS: dict[str, dict[str, float]] = {
    "output": {"攻速": 1.25, "暴击": 1.25, "命中": 1.10, "闪避": 1.00, "体力": 0.90, "防御": 0.80, "减伤": 0.80},
    "survival": {"攻速": 0.85, "暴击": 0.80, "命中": 0.90, "闪避": 1.15, "体力": 1.30, "防御": 1.25, "减伤": 1.20},
    "balanced": {"攻速": 1.00, "暴击": 1.00, "命中": 1.00, "闪避": 1.00, "体力": 1.00, "防御": 1.00, "减伤": 1.00},
}
GROWTH_TABLE_ROWS = [
    ("技能书", "三转/四转技能升级", "", "", "按资料表手动填写"),
    ("黑暗灵魂", "黑暗灵魂养成", "", "", "按资料表手动填写"),
    ("金币", "升级与重铸通用消耗", "", "", "按资料表手动填写"),
    ("成长石", "装备养成", "", "", "按资料表手动填写"),
    ("符文碎片", "符文培养", "", "", "按资料表手动填写"),
]
ROLE_GEAR_SLOTS = ["武器", "头盔", "护甲", "护手", "鞋子", "腰带", "项链", "戒指"]
ROLE_CHARACTER_NAMES = [f"角色{i:02d}" for i in range(1, 23)]

THEME = """
QWidget#RootContainer {
    background-color: #f9fafb;
}
QMainWindow, QWidget {
    background-color: transparent;
    color: #111827;
    font-family: 'Segoe UI', 'Microsoft YaHei UI';
    font-size: 13px;
}
QFrame#NavBar {
    background-color: #1f2937;
    border-right: 1px solid #111827;
}
QLabel#NavTitle {
    color: #f9fafb;
    font-size: 14px;
    font-weight: 700;
    padding: 6px 10px;
}
QPushButton[navItem='true'] {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #e5e7eb;
    text-align: left;
    padding: 10px 12px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton[navItem='true']:hover {
    background-color: #2f3b4a;
}
QPushButton[navItem='true']:checked {
    background-color: #374151;
    color: #ffffff;
}
QPushButton#NavLogoButton {
    background: transparent;
    border: none;
    text-align: left;
    color: #f9fafb;
    font-size: 14px;
    font-weight: 700;
    padding: 6px 10px;
}
QPushButton#NavLogoButton:hover {
    background-color: #2f3b4a;
    border-radius: 6px;
}
QFrame#TopToolbar {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QLabel#AppTitle {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
}
QLabel#ToolbarChip {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    color: #374151;
    border-radius: 6px;
    padding: 4px 8px;
}
QLabel#ToolbarPath {
    color: #374151;
    padding: 0 2px;
}
QFrame#CardFrame {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QFrame#LaunchPadRoot {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QFrame#IntroSection {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QLabel#IntroTitle {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
}
QLabel#IntroSub {
    color: #4b5563;
    font-size: 13px;
}
QLabel#IntroItem {
    color: #111827;
    font-size: 13px;
    padding: 6px 0;
}
QLabel#IntroHint {
    color: #6b7280;
    font-size: 12px;
}
QPushButton#LaunchEntry {
    text-align: left;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    background-color: #ffffff;
    color: #111827;
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#LaunchEntry:hover {
    background-color: #f3f4f6;
}
QPushButton#LaunchPrimary {
    text-align: left;
    border-radius: 8px;
    border: 1px solid #1d4ed8;
    background-color: #2563eb;
    color: #ffffff;
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#LaunchPrimary:hover {
    background-color: #1d4ed8;
}
QSplitter#MainSplitter::handle:horizontal {
    background-color: #e5e7eb;
    width: 4px;
}
QSplitter#MainSplitter::handle:vertical {
    background-color: #e5e7eb;
    height: 4px;
}
QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}
QLabel#FieldHeader {
    color: #6b7280;
    font-size: 12px;
    font-weight: 600;
}
QLineEdit, QComboBox, QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    color: #111827;
    border-radius: 6px;
    padding: 7px 10px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}
QLineEdit[readOnly='true'] {
    background-color: #f9fafb;
    color: #374151;
}
QComboBox {
    padding-right: 24px;
}
QComboBox::drop-down {
    width: 24px;
    border-left: 1px solid #e5e7eb;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background: #f9fafb;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #111827;
    border: 1px solid #d1d5db;
    selection-background-color: #dbeafe;
    selection-color: #111827;
    outline: 0;
}
QPushButton {
    border-radius: 6px;
    padding: 8px 14px;
    border: 1px solid #d1d5db;
    background-color: #ffffff;
    color: #111827;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #f9fafb;
}
QPushButton#PrimaryButton {
    background-color: #2563eb;
    border: 1px solid #1d4ed8;
    color: #ffffff;
}
QPushButton#SuccessButton {
    background-color: #2563eb;
    border: 1px solid #1d4ed8;
    color: #ffffff;
}
QPushButton#DangerButton {
    background-color: #dc2626;
    border: 1px solid #b91c1c;
    color: #ffffff;
}
QPushButton#GhostButton {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    color: #111827;
}
QLabel#TitleLabel {
    font-size: 13px;
    color: #374151;
}
QLabel#ScoreValue {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}
QLabel#FormulaLine {
    color: #4b5563;
    font-size: 13px;
}
QLabel#StatChip {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 4px 10px;
    color: #374151;
}
QLabel#StatusPass {
    background-color: #dcfce7;
    border: 1px solid #86efac;
    border-radius: 6px;
    color: #166534;
    font-weight: 700;
    padding: 5px 8px;
}
QLabel#StatusFail {
    background-color: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    color: #991b1b;
    font-weight: 700;
    padding: 5px 8px;
}
QLabel#ErrorLabel {
    color: #991b1b;
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 6px 8px;
}
QTableWidget {
    gridline-color: #e5e7eb;
    alternate-background-color: #f9fafb;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}
QHeaderView::section {
    background-color: #f3f4f6;
    border: 1px solid #e5e7eb;
    color: #374151;
    font-weight: 700;
    padding: 8px;
}
"""


def _safe_category_name(raw: str) -> str:
    name = (raw or "").strip()
    return name if name else "通用"


class ClickInputLineEdit(QLineEdit):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        super().mousePressEvent(event)
        self.clicked.emit()


class SortRuleRow(QWidget):
    def __init__(self, on_up, on_down, on_delete, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_up = on_up
        self._on_down = on_down
        self._on_delete = on_delete

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.priority_label = QLabel("1", self)
        self.priority_label.setFixedWidth(90)

        self.field_combo = QComboBox(self)
        for text, value in [
            ("装备种类", "category"),
            ("装备名", "name"),
            ("属性1(a1)", "a1"),
            ("属性2(a2)", "a2"),
            ("属性3(a3)", "a3"),
            ("属性4(a4)", "a4"),
            ("属性5(a5)", "a5"),
            ("总分", "score"),
            ("保存时间", "created_at"),
        ]:
            self.field_combo.addItem(text, value)

        self.direction_combo = QComboBox(self)
        self.direction_combo.addItem("降序", False)
        self.direction_combo.addItem("升序", True)

        btn_up = QPushButton("上移", self)
        btn_down = QPushButton("下移", self)
        btn_delete = QPushButton("删除规则", self)
        btn_up.setObjectName("GhostButton")
        btn_down.setObjectName("GhostButton")
        btn_delete.setObjectName("DangerButton")
        btn_up.clicked.connect(lambda: self._on_up(self))
        btn_down.clicked.connect(lambda: self._on_down(self))
        btn_delete.clicked.connect(lambda: self._on_delete(self))

        layout.addWidget(self.priority_label)
        layout.addWidget(self.field_combo)
        layout.addWidget(self.direction_combo)
        layout.addWidget(btn_up)
        layout.addWidget(btn_down)
        layout.addWidget(btn_delete)
        layout.addStretch()

    def set_priority(self, index: int) -> None:
        self.priority_label.setText(f"优先级 {index}")

    def set_rule(self, field: str, asc: bool) -> None:
        idx = self.field_combo.findData(field)
        if idx >= 0:
            self.field_combo.setCurrentIndex(idx)
        didx = self.direction_combo.findData(asc)
        if didx >= 0:
            self.direction_combo.setCurrentIndex(didx)

    def to_rule(self) -> tuple[str, bool]:
        return str(self.field_combo.currentData()), bool(self.direction_combo.currentData())


class LaunchPadPage(QWidget):
    open_score = Signal()
    open_placeholder_a = Signal()
    open_placeholder_b = Signal()
    open_role_gear = Signal()
    open_settings = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("项目介绍", self)
        title.setObjectName("IntroTitle")
        sub = QLabel("GearWeightCalculator：用于装备评分、攻速达标、配装推荐与养成管理。", self)
        sub.setObjectName("IntroSub")
        root.addWidget(title)
        root.addWidget(sub)

        intro_card = QFrame(self)
        intro_card.setObjectName("IntroSection")
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(14, 12, 14, 12)
        intro_layout.setSpacing(4)
        intro_title = QLabel("已接入接口", intro_card)
        intro_title.setObjectName("SectionTitle")
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(self._make_intro_item("评分公式：a1*b1 + a2*b2 + ... + a5*b5"))
        intro_layout.addWidget(self._make_intro_item("阈值判定：score >= threshold 为达标"))
        intro_layout.addWidget(self._make_intro_item("攻速计算：基础攻速 + 加成 -> 判断目标是否达标"))
        intro_layout.addWidget(self._make_intro_item("配装推荐：按职业 + 目标玩法给出词条优先级"))
        intro_layout.addWidget(self._make_intro_item("养成成本表：内置表格，支持手动填写与跟踪"))
        root.addWidget(intro_card)

        nav_card = QFrame(self)
        nav_card.setObjectName("IntroSection")
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(14, 12, 14, 12)
        nav_layout.setSpacing(4)
        nav_title = QLabel("导航说明", nav_card)
        nav_title.setObjectName("SectionTitle")
        nav_layout.addWidget(nav_title)
        nav_layout.addWidget(self._make_intro_item("装备评分：进入主功能页面。"))
        nav_layout.addWidget(self._make_intro_item("攻速与达标：计算攻速、暴击和闪避达标情况。"))
        nav_layout.addWidget(self._make_intro_item("配装推荐：生成词条优先级，附带养成成本表。"))
        nav_layout.addWidget(self._make_intro_item("角色装备：维护 22 个角色的装备统计与占位配对。"))
        nav_layout.addWidget(self._make_intro_item("设置：进入设置页修改保存目录。"))
        root.addWidget(nav_card)

        entry_card = QFrame(self)
        entry_card.setObjectName("IntroSection")
        entry_layout = QVBoxLayout(entry_card)
        entry_layout.setContentsMargins(14, 12, 14, 12)
        entry_layout.setSpacing(8)
        entry_title = QLabel("功能入口", entry_card)
        entry_title.setObjectName("SectionTitle")
        entry_layout.addWidget(entry_title)

        btn_score = QPushButton("进入装备评分", entry_card)
        btn_score.setObjectName("LaunchPrimary")
        btn_score.clicked.connect(self.open_score.emit)

        btn_a = QPushButton("进入攻速与达标", entry_card)
        btn_a.setObjectName("LaunchEntry")
        btn_a.clicked.connect(self.open_placeholder_a.emit)

        btn_b = QPushButton("进入配装推荐", entry_card)
        btn_b.setObjectName("LaunchEntry")
        btn_b.clicked.connect(self.open_placeholder_b.emit)

        btn_role = QPushButton("进入角色装备", entry_card)
        btn_role.setObjectName("LaunchEntry")
        btn_role.clicked.connect(self.open_role_gear.emit)

        btn_settings = QPushButton("进入设置", entry_card)
        btn_settings.setObjectName("LaunchEntry")
        btn_settings.clicked.connect(self.open_settings.emit)

        entry_layout.addWidget(btn_score)
        entry_layout.addWidget(btn_a)
        entry_layout.addWidget(btn_b)
        entry_layout.addWidget(btn_role)
        entry_layout.addWidget(btn_settings)
        root.addWidget(entry_card)
        root.addStretch()

    def _make_intro_item(self, text: str) -> QLabel:
        item = QLabel(text, self)
        item.setObjectName("IntroItem")
        return item


PAGE_LAUNCH = "launch"
PAGE_SCORE = "score"
PAGE_PLACEHOLDER_A = "placeholder_a"
PAGE_PLACEHOLDER_B = "placeholder_b"
PAGE_ROLE_GEAR = "role_gear"
PAGE_SETTINGS = "settings"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GearWeightCalculator")
        self.resize(1760, 1020)
        self.setStyleSheet(THEME)

        self.records: list[EquipRecord] = []
        self.visible_record_indexes: list[int] = []
        self.sort_rule_rows: list[SortRuleRow] = []
        self.active_sort_rules: list[tuple[str, bool]] = [("score", False)]

        self.attr_name_edits: list[QLineEdit] = []
        self.weight_name_edits: list[QLineEdit] = []
        self.attr_value_edits: list[QLineEdit] = []
        self.weight_value_edits: list[QLineEdit] = []

        self.bootstrap_dir = Path.home() / APP_DIRNAME
        self.bootstrap_path = self.bootstrap_dir / "bootstrap.json"
        self.config_dir = self._resolve_storage_dir()
        self._rebind_storage_paths()
        self._suspend_auto_save = False

        self._ensure_storage()
        self.categories = self._load_categories()
        settings = self._load_settings()
        self.current_category = _safe_category_name(settings.get("current_category", self.categories[0]))
        self.global_threshold = float(settings.get("threshold", 0.0))
        self.saved_crit_atlas = str(settings.get("cap_crit_atlas", "0"))
        self.saved_dodge_atlas = str(settings.get("cap_dodge_atlas", "0"))
        self.role_gear_store = self._normalize_role_gear_store(settings.get("role_gear_store", {}))
        saved_role_name = str(settings.get("current_role_name", ROLE_CHARACTER_NAMES[0]))
        self.current_role_name = saved_role_name if saved_role_name in ROLE_CHARACTER_NAMES else ROLE_CHARACTER_NAMES[0]
        self._role_gear_loading = False

        self._build_ui()
        self._reset_sort_rules()
        self._load_global_scheme()
        self.threshold_edit.setText(f"{self.global_threshold:g}")
        self._sync_category_combo()
        self._update_storage_tag()
        self._save_bootstrap()
        self.calculate_score()

    def _ensure_storage(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_storage_dir(self) -> Path:
        self.bootstrap_dir.mkdir(parents=True, exist_ok=True)
        if self.bootstrap_path.exists():
            try:
                with open(self.bootstrap_path, "r", encoding="utf-8") as f:
                    data = dict(json.load(f))
                raw_path = str(data.get("storage_dir", "")).strip()
                if raw_path:
                    return Path(raw_path).expanduser()
            except Exception:
                pass
        return self.bootstrap_dir

    def _rebind_storage_paths(self) -> None:
        self.global_scheme_path = self.config_dir / "global_scheme.csv"
        self.categories_path = self.config_dir / "categories.json"
        self.settings_path = self.config_dir / "settings.json"

    def _save_bootstrap(self) -> None:
        self.bootstrap_dir.mkdir(parents=True, exist_ok=True)
        data = {"storage_dir": str(self.config_dir)}
        with open(self.bootstrap_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_categories(self) -> list[str]:
        if self.categories_path.exists():
            try:
                with open(self.categories_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                values = [_safe_category_name(str(x)) for x in raw if str(x).strip()]
                if values:
                    return list(dict.fromkeys(values))
            except Exception:
                pass
        return DEFAULT_CATEGORIES[:]

    def _save_categories(self) -> None:
        values = list(dict.fromkeys([_safe_category_name(x) for x in self.categories]))
        with open(self.categories_path, "w", encoding="utf-8") as f:
            json.dump(values, f, ensure_ascii=False, indent=2)

    def _load_settings(self) -> dict:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return dict(json.load(f))
            except Exception:
                return {}
        return {}

    def _save_settings(self) -> None:
        if hasattr(self, "role_stat_table"):
            self._save_current_role_gear()
        data = {
            "current_category": self.current_category,
            "threshold": models.parse_float(self.threshold_edit.text(), "")[0],
            "current_role_name": self.current_role_name,
            "role_gear_store": self.role_gear_store,
        }
        if hasattr(self, "crit_atlas_edit"):
            data["cap_crit_atlas"] = self.crit_atlas_edit.text().strip()
        if hasattr(self, "dodge_atlas_edit"):
            data["cap_dodge_atlas"] = self.dodge_atlas_edit.text().strip()
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _normalize_role_gear_store(self, raw: object) -> dict[str, list[list[str]]]:
        normalized: dict[str, list[list[str]]] = {
            role_name: [["", "", "", ""] for _ in ROLE_GEAR_SLOTS] for role_name in ROLE_CHARACTER_NAMES
        }
        if not isinstance(raw, dict):
            return normalized

        for role_name in ROLE_CHARACTER_NAMES:
            role_rows = raw.get(role_name)
            if not isinstance(role_rows, list):
                continue
            for row_idx in range(min(len(ROLE_GEAR_SLOTS), len(role_rows))):
                row_values = role_rows[row_idx]
                if not isinstance(row_values, list):
                    continue
                for col_idx in range(4):
                    if col_idx < len(row_values):
                        normalized[role_name][row_idx][col_idx] = str(row_values[col_idx]).strip()
        return normalized

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("RootContainer")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        nav_bar = QFrame(root)
        nav_bar.setObjectName("NavBar")
        nav_bar.setFixedWidth(180)
        nav_layout = QVBoxLayout(nav_bar)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(8)

        self.nav_logo_btn = QPushButton("GearWeightCalculator", nav_bar)
        self.nav_logo_btn.setObjectName("NavLogoButton")
        self.nav_logo_btn.clicked.connect(self._on_nav_launch_clicked)
        nav_layout.addWidget(self.nav_logo_btn)

        self.nav_score_btn = self._create_nav_button("装备评分", nav_bar)
        self.nav_placeholder_a_btn = self._create_nav_button("攻速与达标", nav_bar)
        self.nav_placeholder_b_btn = self._create_nav_button("配装推荐", nav_bar)
        self.nav_role_gear_btn = self._create_nav_button("角色装备", nav_bar)
        self.nav_settings_btn = self._create_nav_button("设置", nav_bar)

        self.nav_score_btn.clicked.connect(self._on_nav_score_clicked)
        self.nav_placeholder_a_btn.clicked.connect(self._on_nav_placeholder_a_clicked)
        self.nav_placeholder_b_btn.clicked.connect(self._on_nav_placeholder_b_clicked)
        self.nav_role_gear_btn.clicked.connect(self._on_nav_role_gear_clicked)
        self.nav_settings_btn.clicked.connect(self._on_nav_settings_clicked)

        nav_layout.addWidget(self.nav_score_btn)
        nav_layout.addWidget(self.nav_placeholder_a_btn)
        nav_layout.addWidget(self.nav_placeholder_b_btn)
        nav_layout.addWidget(self.nav_role_gear_btn)
        nav_layout.addWidget(self.nav_settings_btn)
        nav_layout.addStretch()
        root_layout.addWidget(nav_bar)

        content = QWidget(root)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(12)

        toolbar = QFrame(content)
        toolbar.setObjectName("TopToolbar")
        toolbar.setFixedHeight(60)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(8)

        title = QLabel("GearWeightCalculator", toolbar)
        title.setObjectName("AppTitle")
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        self.hero_category_tag = QLabel("当前种类: -", toolbar)
        self.hero_record_tag = QLabel("记录总数: 0", toolbar)
        self.hero_auto_save_tag = QLabel("", toolbar)
        self.hero_category_tag.setObjectName("ToolbarChip")
        self.hero_record_tag.setObjectName("ToolbarChip")
        self.hero_auto_save_tag.setObjectName("ToolbarPath")
        self.hero_auto_save_tag.setMinimumWidth(380)

        btn_launch = QPushButton("返回启动面板", toolbar)
        btn_launch.setObjectName("GhostButton")
        btn_launch.clicked.connect(lambda: self.switch_page(PAGE_LAUNCH))

        btn_change_storage = QPushButton("修改目录", toolbar)
        btn_change_storage.setObjectName("GhostButton")
        btn_change_storage.clicked.connect(self.change_storage_directory)

        toolbar_layout.addWidget(self.hero_category_tag)
        toolbar_layout.addWidget(self.hero_record_tag)
        toolbar_layout.addWidget(self.hero_auto_save_tag, 1)
        toolbar_layout.addWidget(btn_launch)
        toolbar_layout.addWidget(btn_change_storage)
        content_layout.addWidget(toolbar)

        self.content_stack = QStackedWidget(content)
        self.page_launch = LaunchPadPage(self.content_stack)
        self.page_launch.setObjectName("LaunchPadRoot")
        self.page_score = QFrame(self.content_stack)
        self.page_score.setObjectName("CardFrame")
        self.page_placeholder_a = QFrame(self.content_stack)
        self.page_placeholder_a.setObjectName("CardFrame")
        self.page_placeholder_b = QFrame(self.content_stack)
        self.page_placeholder_b.setObjectName("CardFrame")
        self.page_role_gear = QFrame(self.content_stack)
        self.page_role_gear.setObjectName("CardFrame")
        self.page_settings = QFrame(self.content_stack)
        self.page_settings.setObjectName("CardFrame")
        self.content_stack.addWidget(self.page_launch)
        self.content_stack.addWidget(self.page_score)
        self.content_stack.addWidget(self.page_placeholder_a)
        self.content_stack.addWidget(self.page_placeholder_b)
        self.content_stack.addWidget(self.page_role_gear)
        self.content_stack.addWidget(self.page_settings)
        content_layout.addWidget(self.content_stack, 1)

        self.page_launch.open_score.connect(lambda: self.switch_page(PAGE_SCORE))
        self.page_launch.open_placeholder_a.connect(lambda: self.switch_page(PAGE_PLACEHOLDER_A))
        self.page_launch.open_placeholder_b.connect(lambda: self.switch_page(PAGE_PLACEHOLDER_B))
        self.page_launch.open_role_gear.connect(lambda: self.switch_page(PAGE_ROLE_GEAR))
        self.page_launch.open_settings.connect(lambda: self.switch_page(PAGE_SETTINGS))

        self._build_score_page(self.page_score)
        self._build_speed_and_cap_page(self.page_placeholder_a)
        self._build_recommendation_page(self.page_placeholder_b)
        self._build_role_gear_page(self.page_role_gear)
        self._build_settings_page(self.page_settings)
        root_layout.addWidget(content, 1)

        self.page_registry = {
            PAGE_LAUNCH: self.page_launch,
            PAGE_SCORE: self.page_score,
            PAGE_PLACEHOLDER_A: self.page_placeholder_a,
            PAGE_PLACEHOLDER_B: self.page_placeholder_b,
            PAGE_ROLE_GEAR: self.page_role_gear,
            PAGE_SETTINGS: self.page_settings,
        }
        self.switch_page(PAGE_LAUNCH)

    def _create_nav_button(self, text: str, parent: QWidget, checkable: bool = True) -> QPushButton:
        btn = QPushButton(text, parent)
        btn.setProperty("navItem", True)
        btn.setFlat(True)
        btn.setCheckable(checkable)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setAutoDefault(False)
        return btn

    def _on_nav_launch_clicked(self) -> None:
        self.switch_page(PAGE_LAUNCH)

    def _on_nav_score_clicked(self) -> None:
        self.switch_page(PAGE_SCORE)

    def _on_nav_placeholder_a_clicked(self) -> None:
        self.switch_page(PAGE_PLACEHOLDER_A)

    def _on_nav_placeholder_b_clicked(self) -> None:
        self.switch_page(PAGE_PLACEHOLDER_B)

    def _on_nav_role_gear_clicked(self) -> None:
        self.switch_page(PAGE_ROLE_GEAR)

    def _on_nav_settings_clicked(self) -> None:
        self.switch_page(PAGE_SETTINGS)

    def _set_nav_active(self, page_key: str) -> None:
        mapping = {
            PAGE_SCORE: self.nav_score_btn,
            PAGE_PLACEHOLDER_A: self.nav_placeholder_a_btn,
            PAGE_PLACEHOLDER_B: self.nav_placeholder_b_btn,
            PAGE_ROLE_GEAR: self.nav_role_gear_btn,
            PAGE_SETTINGS: self.nav_settings_btn,
        }
        for key, btn in mapping.items():
            btn.setChecked(key == page_key)

    def _update_toolbar_context(self, page_key: str) -> None:
        self.hero_category_tag.setVisible(False)
        self.hero_record_tag.setVisible(False)
        self.hero_auto_save_tag.setVisible(False)

    def switch_page(self, page_key: str) -> None:
        page = self.page_registry.get(page_key)
        if page is None:
            return
        self.content_stack.setCurrentWidget(page)
        self._set_nav_active(page_key)
        self._update_toolbar_context(page_key)

        if page_key == PAGE_SCORE:
            self.content_splitter.setSizes([390, 610])
            if self.attr_value_edits:
                self.attr_value_edits[0].setFocus()

    def _build_score_page(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.content_splitter = QSplitter(Qt.Vertical, panel)
        self.content_splitter.setObjectName("MainSplitter")

        top_panel = QFrame(self.content_splitter)
        top_panel.setObjectName("CardFrame")
        bottom_panel = QFrame(self.content_splitter)
        bottom_panel.setObjectName("CardFrame")

        self.content_splitter.addWidget(top_panel)
        self.content_splitter.addWidget(bottom_panel)
        self.content_splitter.setStretchFactor(0, 4)
        self.content_splitter.setStretchFactor(1, 6)
        self.content_splitter.setSizes([390, 610])
        layout.addWidget(self.content_splitter, 1)

        self._build_input_panel(top_panel)
        self._build_records_panel(bottom_panel)

    def _build_speed_and_cap_page(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("攻速与达标", panel)
        title.setObjectName("IntroTitle")
        desc = QLabel("功能 1 + 2：攻速计算、暴击/闪避达标判断。", panel)
        desc.setObjectName("IntroSub")
        layout.addWidget(title)
        layout.addWidget(desc)

        speed_card = QFrame(panel)
        speed_card.setObjectName("IntroSection")
        speed_layout = QVBoxLayout(speed_card)
        speed_layout.setContentsMargins(14, 12, 14, 12)
        speed_layout.setSpacing(8)
        speed_title = QLabel("攻速计算", speed_card)
        speed_title.setObjectName("SectionTitle")
        speed_layout.addWidget(speed_title)

        speed_grid = QGridLayout()
        speed_grid.setHorizontalSpacing(10)
        speed_grid.setVerticalSpacing(8)

        def _label(text: str) -> QLabel:
            lbl = QLabel(text, speed_card)
            lbl.setFixedWidth(SPEED_LABEL_WIDTH)
            return lbl

        self.as_base_edit = QLineEdit(speed_card)
        self.as_base_edit.setPlaceholderText("例如 2.2")
        self.as_base_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("武器攻速值"), 0, 0)
        speed_grid.addWidget(self.as_base_edit, 0, 1)

        self.as_trait_factor_edit = QLineEdit(speed_card)
        self.as_trait_factor_edit.setPlaceholderText("空值按 1")
        self.as_trait_factor_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("特性系数"), 0, 2)
        speed_grid.addWidget(self.as_trait_factor_edit, 0, 3)

        self.as_mystic_bonus_edit = QLineEdit(speed_card)
        self.as_mystic_bonus_edit.setText("10")
        self.as_mystic_bonus_edit.setReadOnly(True)
        self.as_mystic_bonus_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("秘法加成(%)"), 0, 4)
        speed_grid.addWidget(self.as_mystic_bonus_edit, 0, 5)

        self.as_guild_bonus_edit = QLineEdit(speed_card)
        self.as_guild_bonus_edit.setText("5")
        self.as_guild_bonus_edit.setReadOnly(True)
        self.as_guild_bonus_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("公会加成(%)"), 1, 0)
        speed_grid.addWidget(self.as_guild_bonus_edit, 1, 1)

        self.as_personality_combo = QComboBox(speed_card)
        for text, value in PERSONALITY_SPEED_OPTIONS:
            self.as_personality_combo.addItem(text, value)
        default_idx = self.as_personality_combo.findText("英雄心态（攻速 +7%）")
        self.as_personality_combo.setCurrentIndex(default_idx if default_idx >= 0 else 0)
        self.as_personality_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("性格"), 1, 2)
        speed_grid.addWidget(self.as_personality_combo, 1, 3)

        self.as_pet_bonus_combo = QComboBox(speed_card)
        for text, value in PET_GEAR_SPEED_OPTIONS:
            self.as_pet_bonus_combo.addItem(text, value)
        self.as_pet_bonus_combo.setCurrentIndex(0)
        self.as_pet_bonus_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("宠物装备"), 1, 4)
        speed_grid.addWidget(self.as_pet_bonus_combo, 1, 5)

        self.as_target_edit = QLineEdit(speed_card)
        self.as_target_edit.setPlaceholderText("空值按 0（最低按 0.25）")
        self.as_target_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("目标攻速"), 2, 0)
        speed_grid.addWidget(self.as_target_edit, 2, 1)

        self.as_equip_bonus_edit = QLineEdit(speed_card)
        self.as_equip_bonus_edit.setPlaceholderText("空值按 0")
        self.as_equip_bonus_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("装备加成(%)"), 2, 2)
        speed_grid.addWidget(self.as_equip_bonus_edit, 2, 3)

        self.as_hunter_quality_combo = QComboBox(speed_card)
        for text, value in HUNTER_SPEED_QUALITY_OPTIONS:
            self.as_hunter_quality_combo.addItem(text, value)
        self.as_hunter_quality_combo.setCurrentIndex(2)
        self.as_hunter_quality_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("猎人攻速品质"), 2, 4)
        speed_grid.addWidget(self.as_hunter_quality_combo, 2, 5)

        self.as_panel_actual_edit = QLineEdit(speed_card)
        self.as_panel_actual_edit.setPlaceholderText("可选，空值按 0")
        self.as_panel_actual_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        speed_grid.addWidget(_label("实测面板攻速"), 3, 4)
        speed_grid.addWidget(self.as_panel_actual_edit, 3, 5)

        btn_speed = QPushButton("计算攻速", speed_card)
        btn_speed.setObjectName("PrimaryButton")
        btn_speed.clicked.connect(self.calculate_attack_speed)
        speed_grid.addWidget(btn_speed, 4, 5)

        speed_layout.addLayout(speed_grid)

        self.as_result_label = QLabel("结果: -", speed_card)
        self.as_result_label.setObjectName("IntroItem")
        self.as_hint_label = QLabel(
            "说明: 按公式 (武器攻速*(1-加成总和/100))/特性系数 计算；包含猎人攻速品质，秘法固定10%，公会固定5%。",
            speed_card,
        )
        self.as_hint_label.setObjectName("IntroHint")
        self.as_error_label = QLabel("", speed_card)
        self.as_error_label.setObjectName("ErrorLabel")
        self.as_error_label.setVisible(False)
        speed_layout.addWidget(self.as_result_label)
        speed_layout.addWidget(self.as_hint_label)
        speed_layout.addWidget(self.as_error_label)
        layout.addWidget(speed_card)

        cap_card = QFrame(panel)
        cap_card.setObjectName("IntroSection")
        cap_layout = QVBoxLayout(cap_card)
        cap_layout.setContentsMargins(14, 12, 14, 12)
        cap_layout.setSpacing(8)
        cap_title = QLabel("暴击 / 闪避达标", cap_card)
        cap_title.setObjectName("SectionTitle")
        cap_layout.addWidget(cap_title)

        def _cap_label(text: str, parent: QWidget) -> QLabel:
            lbl = QLabel(text, parent)
            lbl.setFixedWidth(SPEED_LABEL_WIDTH)
            return lbl

        switch_row = QHBoxLayout()
        switch_row.addWidget(QLabel("模板切换", cap_card))
        self.cap_mode_combo = QComboBox(cap_card)
        self.cap_mode_combo.addItem("近战", "melee")
        self.cap_mode_combo.addItem("远程", "ranged")
        self.cap_mode_combo.setPlaceholderText("选择模板")
        self.cap_mode_combo.setCurrentIndex(0)
        self.cap_mode_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        self.cap_mode_combo.currentIndexChanged.connect(self._on_cap_mode_changed)
        switch_row.addWidget(self.cap_mode_combo)
        switch_row.addSpacing(10)
        switch_row.addWidget(QLabel("品质修正", cap_card))
        self.cap_quality_combo = QComboBox(cap_card)
        for text, value in CRIT_DODGE_QUALITY_OPTIONS:
            self.cap_quality_combo.addItem(text, value)
        quality_default_idx = self.cap_quality_combo.findData(0.0)
        self.cap_quality_combo.setCurrentIndex(quality_default_idx if quality_default_idx >= 0 else 0)
        self.cap_quality_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        switch_row.addWidget(self.cap_quality_combo)
        switch_row.addStretch()
        cap_layout.addLayout(switch_row)

        crit_card = QFrame(cap_card)
        crit_card.setObjectName("CardFrame")
        crit_layout = QVBoxLayout(crit_card)
        crit_layout.setContentsMargins(10, 10, 10, 10)
        crit_layout.setSpacing(8)
        crit_title = QLabel("暴击", crit_card)
        crit_title.setObjectName("SectionTitle")
        crit_layout.addWidget(crit_title)
        crit_grid = QGridLayout()
        crit_grid.setHorizontalSpacing(10)
        crit_grid.setVerticalSpacing(8)

        self.crit_current_edit = QLineEdit(crit_card)
        self.crit_current_edit.setPlaceholderText("无")
        self.crit_current_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("装备暴击", crit_card), 0, 0)
        crit_grid.addWidget(self.crit_current_edit, 0, 1)

        self.crit_rune_edit = QLineEdit(crit_card)
        self.crit_rune_edit.setPlaceholderText("无")
        self.crit_rune_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("符文暴击", crit_card), 0, 2)
        crit_grid.addWidget(self.crit_rune_edit, 0, 3)

        self.crit_atlas_edit = QLineEdit(crit_card)
        self.crit_atlas_edit.setText(self.saved_crit_atlas)
        self.crit_atlas_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        self.crit_atlas_edit.editingFinished.connect(self._save_settings)
        crit_grid.addWidget(_cap_label("图鉴暴击", crit_card), 0, 4)
        crit_grid.addWidget(self.crit_atlas_edit, 0, 5)

        self.crit_self_full_edit = QLineEdit(crit_card)
        self.crit_self_full_edit.setReadOnly(True)
        self.crit_self_full_edit.setText("8")
        self.crit_self_full_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("自身满暴击", crit_card), 1, 0)
        crit_grid.addWidget(self.crit_self_full_edit, 1, 1)

        self.crit_guild_edit = QLineEdit(crit_card)
        self.crit_guild_edit.setText("5")
        self.crit_guild_edit.setReadOnly(True)
        self.crit_guild_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("公会暴击", crit_card), 1, 2)
        crit_grid.addWidget(self.crit_guild_edit, 1, 3)

        self.crit_mystic_edit = QLineEdit(crit_card)
        self.crit_mystic_edit.setText("10")
        self.crit_mystic_edit.setReadOnly(True)
        self.crit_mystic_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("秘法暴击", crit_card), 1, 4)
        crit_grid.addWidget(self.crit_mystic_edit, 1, 5)

        self.crit_pet_gear_combo = QComboBox(crit_card)
        for text, value in CAP_PET_GEAR_OPTIONS:
            self.crit_pet_gear_combo.addItem(text, value)
        self.crit_pet_gear_combo.setCurrentIndex(0)
        self.crit_pet_gear_combo.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("宠物装备", crit_card), 2, 0)
        crit_grid.addWidget(self.crit_pet_gear_combo, 2, 1)

        self.crit_total_edit = QLineEdit(crit_card)
        self.crit_total_edit.setText("")
        self.crit_total_edit.setReadOnly(True)
        self.crit_total_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        crit_grid.addWidget(_cap_label("总和暴击", crit_card), 2, 4)
        crit_grid.addWidget(self.crit_total_edit, 2, 5)
        crit_layout.addLayout(crit_grid)
        crit_action_row = QHBoxLayout()
        crit_action_row.addStretch()
        btn_crit_cap = QPushButton("判断暴击达标", crit_card)
        btn_crit_cap.setObjectName("PrimaryButton")
        btn_crit_cap.clicked.connect(self.check_crit_cap)
        crit_action_row.addWidget(btn_crit_cap)
        crit_layout.addLayout(crit_action_row)
        cap_layout.addWidget(crit_card)

        dodge_card = QFrame(cap_card)
        dodge_card.setObjectName("CardFrame")
        dodge_layout = QVBoxLayout(dodge_card)
        dodge_layout.setContentsMargins(10, 10, 10, 10)
        dodge_layout.setSpacing(8)
        dodge_title = QLabel("闪避", dodge_card)
        dodge_title.setObjectName("SectionTitle")
        dodge_layout.addWidget(dodge_title)
        dodge_grid = QGridLayout()
        dodge_grid.setHorizontalSpacing(10)
        dodge_grid.setVerticalSpacing(8)

        self.dodge_current_edit = QLineEdit(dodge_card)
        self.dodge_current_edit.setPlaceholderText("例如 36")
        self.dodge_current_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("装备闪避", dodge_card), 0, 0)
        dodge_grid.addWidget(self.dodge_current_edit, 0, 1)

        self.dodge_rune_edit = QLineEdit(dodge_card)
        self.dodge_rune_edit.setPlaceholderText("无")
        self.dodge_rune_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("符文闪避", dodge_card), 0, 2)
        dodge_grid.addWidget(self.dodge_rune_edit, 0, 3)

        self.dodge_atlas_edit = QLineEdit(dodge_card)
        self.dodge_atlas_edit.setText(self.saved_dodge_atlas)
        self.dodge_atlas_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        self.dodge_atlas_edit.editingFinished.connect(self._save_settings)
        dodge_grid.addWidget(_cap_label("图鉴闪避", dodge_card), 0, 4)
        dodge_grid.addWidget(self.dodge_atlas_edit, 0, 5)

        self.dodge_self_full_edit = QLineEdit(dodge_card)
        self.dodge_self_full_edit.setReadOnly(True)
        self.dodge_self_full_edit.setText("8")
        self.dodge_self_full_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("自身满闪避", dodge_card), 1, 0)
        dodge_grid.addWidget(self.dodge_self_full_edit, 1, 1)

        self.dodge_guild_edit = QLineEdit(dodge_card)
        self.dodge_guild_edit.setText("0")
        self.dodge_guild_edit.setReadOnly(True)
        self.dodge_guild_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("公会闪避", dodge_card), 1, 2)
        dodge_grid.addWidget(self.dodge_guild_edit, 1, 3)

        self.dodge_mystic_edit = QLineEdit(dodge_card)
        self.dodge_mystic_edit.setText("10")
        self.dodge_mystic_edit.setReadOnly(True)
        self.dodge_mystic_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("秘法闪避", dodge_card), 1, 4)
        dodge_grid.addWidget(self.dodge_mystic_edit, 1, 5)

        self.dodge_total_edit = QLineEdit(dodge_card)
        self.dodge_total_edit.setText("")
        self.dodge_total_edit.setReadOnly(True)
        self.dodge_total_edit.setFixedWidth(SPEED_INPUT_WIDTH)
        dodge_grid.addWidget(_cap_label("总和闪避", dodge_card), 2, 4)
        dodge_grid.addWidget(self.dodge_total_edit, 2, 5)
        dodge_layout.addLayout(dodge_grid)
        dodge_action_row = QHBoxLayout()
        dodge_action_row.addStretch()
        btn_dodge_cap = QPushButton("判断闪避达标", dodge_card)
        btn_dodge_cap.setObjectName("PrimaryButton")
        btn_dodge_cap.clicked.connect(self.check_dodge_cap)
        dodge_action_row.addWidget(btn_dodge_cap)
        dodge_layout.addLayout(dodge_action_row)
        cap_layout.addWidget(dodge_card)

        self.cap_hint_label = QLabel(
            "说明: 参考“看闪避暴击满不满.xlsx”：先对装备+符文封顶；暴击叠加品质/宠物装备/图鉴/自身满/公会/秘法，闪避叠加品质/图鉴/自身满/公会/秘法；按固定目标暴击 50、闪避 40 判定。",
            cap_card,
        )
        self.cap_hint_label.setObjectName("IntroHint")
        cap_layout.addWidget(self.cap_hint_label)
        layout.addWidget(cap_card)
        layout.addStretch()

    def _build_recommendation_page(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("配装推荐", panel)
        title.setObjectName("IntroTitle")
        desc = QLabel("功能 3 + 4：生成词条优先级，并在程序内维护养成成本表。", panel)
        desc.setObjectName("IntroSub")
        layout.addWidget(title)
        layout.addWidget(desc)

        recommend_card = QFrame(panel)
        recommend_card.setObjectName("IntroSection")
        recommend_layout = QVBoxLayout(recommend_card)
        recommend_layout.setContentsMargins(14, 12, 14, 12)
        recommend_layout.setSpacing(8)

        row = QHBoxLayout()
        row.addWidget(QLabel("职业", recommend_card))
        self.recommend_role_combo = QComboBox(recommend_card)
        self.recommend_role_combo.addItem("通用", "common")
        self.recommend_role_combo.addItem("狂战士", "berserker")
        self.recommend_role_combo.addItem("圣骑士", "paladin")
        self.recommend_role_combo.addItem("射手", "archer")
        self.recommend_role_combo.addItem("法师", "mage")
        self.recommend_role_combo.addItem("猎人", "hunter")
        row.addWidget(self.recommend_role_combo)
        row.addSpacing(8)
        row.addWidget(QLabel("目标玩法", recommend_card))
        self.recommend_goal_combo = QComboBox(recommend_card)
        self.recommend_goal_combo.addItem("输出", "output")
        self.recommend_goal_combo.addItem("生存", "survival")
        self.recommend_goal_combo.addItem("平衡", "balanced")
        row.addWidget(self.recommend_goal_combo)
        btn_recommend = QPushButton("生成推荐", recommend_card)
        btn_recommend.setObjectName("PrimaryButton")
        btn_recommend.clicked.connect(self.generate_recommendation)
        row.addWidget(btn_recommend)
        row.addStretch()
        recommend_layout.addLayout(row)

        self.recommend_summary_label = QLabel("建议: 点击“生成推荐”查看词条优先级。", recommend_card)
        self.recommend_summary_label.setObjectName("IntroItem")
        recommend_layout.addWidget(self.recommend_summary_label)

        self.recommend_table = QTableWidget(0, 3, recommend_card)
        self.recommend_table.setHorizontalHeaderLabels(["优先级", "词条", "建议"])
        self.recommend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recommend_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recommend_table.verticalHeader().setVisible(False)
        self.recommend_table.verticalHeader().setDefaultSectionSize(34)
        recommend_layout.addWidget(self.recommend_table, 1)
        layout.addWidget(recommend_card, 2)

        growth_card = QFrame(panel)
        growth_card.setObjectName("IntroSection")
        growth_layout = QVBoxLayout(growth_card)
        growth_layout.setContentsMargins(14, 12, 14, 12)
        growth_layout.setSpacing(8)
        growth_title = QLabel("养成成本表（仅表格）", growth_card)
        growth_title.setObjectName("SectionTitle")
        growth_layout.addWidget(growth_title)

        self.growth_table = QTableWidget(len(GROWTH_TABLE_ROWS), 5, growth_card)
        self.growth_table.setHorizontalHeaderLabels(["资源", "用途", "当前数量", "目标数量", "备注"])
        self.growth_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.growth_table.verticalHeader().setVisible(False)
        self.growth_table.verticalHeader().setDefaultSectionSize(34)
        for row_idx, row_data in enumerate(GROWTH_TABLE_ROWS):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                if col_idx < 2:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter if col_idx < 4 else Qt.AlignLeft | Qt.AlignVCenter)
                self.growth_table.setItem(row_idx, col_idx, item)
        self.growth_table.resizeColumnsToContents()
        growth_layout.addWidget(self.growth_table)

        hint = QLabel("说明: 该表仅用于记录，不做自动计算。", growth_card)
        hint.setObjectName("IntroHint")
        growth_layout.addWidget(hint)
        layout.addWidget(growth_card, 2)

        self.generate_recommendation()

    def _parse_float_edit(self, edit: QLineEdit, label: str) -> tuple[float, str | None]:
        text = edit.text().strip()
        edit.setStyleSheet("")
        if text == "":
            return 0.0, None
        try:
            return float(text), None
        except ValueError:
            edit.setStyleSheet(ERROR_STYLE)
            return 0.0, f"{label} 不是合法数字。"

    def _parse_float_or_default(self, edit: QLineEdit, label: str, default: float) -> tuple[float, str | None]:
        _ = default
        text = edit.text().strip()
        edit.setStyleSheet("")
        if text == "":
            return 0.0, None
        try:
            return float(text), None
        except ValueError:
            edit.setStyleSheet(ERROR_STYLE)
            return 0.0, f"{label} 不是合法数字。"

    def calculate_attack_speed(self) -> None:
        base, err_base = self._parse_float_edit(self.as_base_edit, "武器攻速值")
        trait_factor, err_trait = self._parse_float_or_default(self.as_trait_factor_edit, "特性系数", 1.0)
        target, err_target = self._parse_float_or_default(self.as_target_edit, "目标攻速", DEFAULT_ATTACK_SPEED_TARGET)
        equip_bonus, err_equip = self._parse_float_or_default(self.as_equip_bonus_edit, "装备加成", 0.0)
        hunter_quality_bonus = float(self.as_hunter_quality_combo.currentData())
        mystic_bonus, err_mystic = self._parse_float_or_default(self.as_mystic_bonus_edit, "秘法加成", 10.0)
        pet_bonus = float(self.as_pet_bonus_combo.currentData())
        guild_bonus, err_guild = self._parse_float_or_default(self.as_guild_bonus_edit, "公会加成", 0.0)
        personality_bonus = float(self.as_personality_combo.currentData())
        panel_actual, err_panel = self._parse_float_or_default(self.as_panel_actual_edit, "实测面板攻速", 0.0)
        errors = [
            err
            for err in [
                err_base,
                err_trait,
                err_target,
                err_equip,
                err_mystic,
                err_guild,
                err_panel,
            ]
            if err
        ]

        if not errors and base <= 0:
            errors.append("武器攻速值必须大于 0。")
            self.as_base_edit.setStyleSheet(ERROR_STYLE)

        if errors:
            self.as_error_label.setText("；".join(errors))
            self.as_error_label.setVisible(True)
            self.as_result_label.setText("结果: -")
            return

        effective_trait_factor = trait_factor if trait_factor > 0 else 1.0
        total_bonus_percent = (
            equip_bonus
            + hunter_quality_bonus
            + mystic_bonus
            + pet_bonus
            + guild_bonus
            + personality_bonus
        )
        total_bonus_ratio = total_bonus_percent / 100.0

        effective_target = max(target, ATTACK_SPEED_FLOOR)
        trait_div_weapon = effective_trait_factor / base if base > 0 else 0.0
        # Formula (no berserker): 1 - target * (trait_factor / weapon_speed) - total_bonus_ratio
        difference_ratio = 1.0 - effective_target * trait_div_weapon - total_bonus_ratio
        need_bonus = max(difference_ratio * 100.0, 0.0)
        overflow_bonus = max(-difference_ratio * 100.0, 0.0)

        current = max((1.0 - total_bonus_ratio) * base / effective_trait_factor, ATTACK_SPEED_FLOOR)
        passed = difference_ratio <= 0
        gap = max(current - effective_target, 0.0)

        status = "达标" if passed else "未达标"
        target_note = ""
        if target < ATTACK_SPEED_FLOOR:
            target_note = f"（目标低于理论下限 {ATTACK_SPEED_FLOOR:.2f}，按 {ATTACK_SPEED_FLOOR:.2f} 判定）"
        panel_note = ""
        if panel_actual > 0:
            panel_note = f"；与实测面板差值 {abs(current - panel_actual):.3f}"
        if passed:
            action_text = f"已超出目标 {overflow_bonus:.2f}%（可视为溢出）"
        else:
            action_text = f"还需补充 {need_bonus:.2f}%"
        self.as_result_label.setText(
            f"结果: 当前攻速 {current:.3f}，目标 {effective_target:.3f}，状态 {status}，攻速差值 {gap:.3f}；"
            f"公式差值 {difference_ratio * 100:.2f}% ，{action_text}。{target_note}{panel_note}"
        )
        self.as_error_label.setText("")
        self.as_error_label.setVisible(False)

    def _on_cap_mode_changed(self) -> None:
        mode = str(self.cap_mode_combo.currentData())
        self._apply_crit_dodge_preset(mode)

    def _apply_crit_dodge_preset(self, mode: str) -> None:
        preset = CRIT_DODGE_PRESETS.get(mode)
        if not preset:
            return

        mode_idx = self.cap_mode_combo.findData(mode)
        if mode_idx >= 0 and mode_idx != self.cap_mode_combo.currentIndex():
            self.cap_mode_combo.blockSignals(True)
            self.cap_mode_combo.setCurrentIndex(mode_idx)
            self.cap_mode_combo.blockSignals(False)

        self.crit_self_full_edit.setText(f"{preset['crit_self_full']:g}")
        self.crit_guild_edit.setText(f"{preset['crit_guild']:g}")
        self.crit_mystic_edit.setText(f"{preset['crit_mystic']:g}")

        self.dodge_self_full_edit.setText(f"{preset['dodge_self_full']:g}")
        self.dodge_guild_edit.setText(f"{preset['dodge_guild']:g}")
        self.dodge_mystic_edit.setText(f"{preset['dodge_mystic']:g}")

        quality_idx = self.cap_quality_combo.findData(float(preset["quality"]))
        if quality_idx >= 0:
            self.cap_quality_combo.setCurrentIndex(quality_idx)
        self.crit_total_edit.setText("")
        self.dodge_total_edit.setText("")

    def check_crit_dodge_cap(self) -> None:
        self.check_crit_cap()
        self.check_dodge_cap()

    def check_crit_cap(self) -> None:
        crit_equip, err_crit_equip = self._parse_float_edit(self.crit_current_edit, "装备暴击")
        crit_rune, err_crit_rune = self._parse_float_or_default(self.crit_rune_edit, "符文暴击", 0.0)
        quality_bonus = float(self.cap_quality_combo.currentData())
        pet_gear_bonus = float(self.crit_pet_gear_combo.currentData())

        crit_atlas, err_crit_atlas = self._parse_float_or_default(self.crit_atlas_edit, "图鉴暴击", 0.0)
        crit_self_full, err_crit_self_full = self._parse_float_or_default(self.crit_self_full_edit, "自身满暴击", 0.0)
        crit_guild, err_crit_guild = self._parse_float_or_default(self.crit_guild_edit, "公会暴击", 0.0)
        crit_mystic, err_crit_mystic = self._parse_float_or_default(self.crit_mystic_edit, "秘法暴击", 0.0)

        errors = [
            err
            for err in [
                err_crit_equip,
                err_crit_rune,
                err_crit_atlas,
                err_crit_self_full,
                err_crit_guild,
                err_crit_mystic,
            ]
            if err
        ]

        if errors:
            self.crit_total_edit.setText("-")
            return

        crit_cap = DEFAULT_CRIT_TARGET
        base_crit_raw = crit_equip + crit_rune
        effective_crit = min(base_crit_raw, crit_cap)

        composite_crit = (
            crit_equip
            + crit_rune
            + quality_bonus
            + pet_gear_bonus
            + crit_atlas
            + crit_self_full
            + crit_guild
            + crit_mystic
        )
        self.crit_total_edit.setText(f"{composite_crit:.1f}")

        total_crit = (
            effective_crit
            + quality_bonus
            + pet_gear_bonus
            + crit_atlas
            + crit_self_full
            + crit_guild
            + crit_mystic
        )

    def check_dodge_cap(self) -> None:
        dodge_equip, err_dodge_equip = self._parse_float_edit(self.dodge_current_edit, "装备闪避")
        dodge_rune, err_dodge_rune = self._parse_float_or_default(self.dodge_rune_edit, "符文闪避", 0.0)
        quality_bonus = float(self.cap_quality_combo.currentData())

        dodge_atlas, err_dodge_atlas = self._parse_float_or_default(self.dodge_atlas_edit, "图鉴闪避", 0.0)
        dodge_self_full, err_dodge_self_full = self._parse_float_or_default(
            self.dodge_self_full_edit, "自身满闪避", 0.0
        )
        dodge_guild, err_dodge_guild = self._parse_float_or_default(self.dodge_guild_edit, "公会闪避", 0.0)
        dodge_mystic, err_dodge_mystic = self._parse_float_or_default(self.dodge_mystic_edit, "秘法闪避", 0.0)

        errors = [
            err
            for err in [
                err_dodge_equip,
                err_dodge_rune,
                err_dodge_atlas,
                err_dodge_self_full,
                err_dodge_guild,
                err_dodge_mystic,
            ]
            if err
        ]

        if errors:
            self.dodge_total_edit.setText("-")
            return

        dodge_cap = DEFAULT_DODGE_TARGET
        base_dodge_raw = dodge_equip + dodge_rune
        effective_dodge = min(base_dodge_raw, dodge_cap)

        composite_dodge = (
            dodge_equip
            + dodge_rune
            + quality_bonus
            + dodge_atlas
            + dodge_self_full
            + dodge_guild
            + dodge_mystic
        )
        self.dodge_total_edit.setText(f"{composite_dodge:.1f}")

        total_dodge = (
            effective_dodge
            + quality_bonus
            + dodge_atlas
            + dodge_self_full
            + dodge_guild
            + dodge_mystic
        )

    def generate_recommendation(self) -> None:
        role = str(self.recommend_role_combo.currentData())
        goal = str(self.recommend_goal_combo.currentData())
        role_weights = RECOMMEND_ROLE_WEIGHTS.get(role, RECOMMEND_ROLE_WEIGHTS["common"])
        goal_multipliers = RECOMMEND_GOAL_MULTIPLIERS.get(goal, RECOMMEND_GOAL_MULTIPLIERS["balanced"])

        ranked: list[tuple[str, float]] = []
        for stat in RECOMMEND_STATS:
            ranked.append((stat, role_weights.get(stat, 1.0) * goal_multipliers.get(stat, 1.0)))
        ranked.sort(key=lambda x: x[1], reverse=True)

        advice_map = {
            "攻速": "优先补到手感档位，再追求其他词条",
            "暴击": "与核心伤害词条联动，优先保持稳定触发",
            "命中": "命中不足时收益很高，建议先补到不偏科",
            "闪避": "偏生存向时优先，避免被连续命中",
            "体力": "提升容错，适合开荒和高压战斗",
            "防御": "稳定减伤，适合坦向与长线战斗",
            "减伤": "面对高爆发场景收益明显",
        }

        self.recommend_table.setRowCount(len(ranked))
        for idx, (stat, score) in enumerate(ranked, start=1):
            values = [str(idx), stat, f"{advice_map.get(stat, '-') }（权重 {score:.2f}）"]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter if col < 2 else Qt.AlignLeft | Qt.AlignVCenter)
                self.recommend_table.setItem(idx - 1, col, item)

        self.recommend_table.resizeColumnsToContents()
        top3 = " > ".join([name for name, _ in ranked[:3]])
        self.recommend_summary_label.setText(f"建议: 优先词条 {top3}")

    def _build_role_gear_page(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("角色装备", panel)
        title.setObjectName("IntroTitle")
        desc = QLabel("独立页面：维护 22 个角色的装备统计，并预留历史装备自动配对流程。", panel)
        desc.setObjectName("IntroSub")
        layout.addWidget(title)
        layout.addWidget(desc)

        role_card = QFrame(panel)
        role_card.setObjectName("IntroSection")
        role_layout = QVBoxLayout(role_card)
        role_layout.setContentsMargins(14, 12, 14, 12)
        role_layout.setSpacing(8)

        ctrl_row = QHBoxLayout()
        ctrl_row.addWidget(QLabel("角色", role_card))
        self.role_select_combo = QComboBox(role_card)
        for role_name in ROLE_CHARACTER_NAMES:
            self.role_select_combo.addItem(role_name, role_name)
        self.role_select_combo.setCurrentText(self.current_role_name)
        self.role_select_combo.currentIndexChanged.connect(self._on_role_changed)
        ctrl_row.addWidget(self.role_select_combo)
        ctrl_row.addSpacing(8)
        btn_clear_role = QPushButton("清空当前角色", role_card)
        btn_clear_role.setObjectName("GhostButton")
        btn_clear_role.clicked.connect(self._clear_current_role_gear)
        ctrl_row.addWidget(btn_clear_role)
        ctrl_row.addStretch()
        role_layout.addLayout(ctrl_row)

        match_row = QHBoxLayout()
        match_row.addWidget(QLabel("配对模式", role_card))
        self.match_mode_combo = QComboBox(role_card)
        self.match_mode_combo.addItem("单部位匹配（占位）", "single")
        self.match_mode_combo.addItem("整套匹配（占位）", "set")
        match_row.addWidget(self.match_mode_combo)
        match_row.addSpacing(8)
        match_row.addWidget(QLabel("目标优先", role_card))
        self.match_goal_combo = QComboBox(role_card)
        self.match_goal_combo.addItem("达标优先（占位）", "threshold")
        self.match_goal_combo.addItem("总分优先（占位）", "score")
        match_row.addWidget(self.match_goal_combo)
        match_row.addStretch()
        btn_match_placeholder = QPushButton("开始历史配对（占位）", role_card)
        btn_match_placeholder.setObjectName("PrimaryButton")
        btn_match_placeholder.clicked.connect(self.run_match_placeholder)
        match_row.addWidget(btn_match_placeholder)
        role_layout.addLayout(match_row)

        self.role_stat_summary_label = QLabel("统计进度: 0/8 个部位已填写。", role_card)
        self.role_stat_summary_label.setObjectName("IntroItem")
        role_layout.addWidget(self.role_stat_summary_label)

        self.role_stat_table = QTableWidget(len(ROLE_GEAR_SLOTS), 5, role_card)
        self.role_stat_table.setHorizontalHeaderLabels(["部位", "当前装备", "主属性", "副属性", "备注"])
        self.role_stat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.role_stat_table.verticalHeader().setVisible(False)
        self.role_stat_table.verticalHeader().setDefaultSectionSize(34)
        self.role_stat_table.blockSignals(True)
        for row_idx, slot in enumerate(ROLE_GEAR_SLOTS):
            slot_item = QTableWidgetItem(slot)
            slot_item.setFlags(slot_item.flags() & ~Qt.ItemIsEditable)
            slot_item.setTextAlignment(Qt.AlignCenter)
            self.role_stat_table.setItem(row_idx, 0, slot_item)
            for col_idx in range(1, 5):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter if col_idx < 4 else Qt.AlignLeft | Qt.AlignVCenter)
                self.role_stat_table.setItem(row_idx, col_idx, item)
        self.role_stat_table.blockSignals(False)
        self.role_stat_table.itemChanged.connect(self._on_role_stat_table_changed)
        self.role_stat_table.resizeColumnsToContents()
        role_layout.addWidget(self.role_stat_table)

        self.match_placeholder_label = QLabel("状态: 未开始。点击“开始历史配对（占位）”生成占位结果。", role_card)
        self.match_placeholder_label.setObjectName("IntroItem")
        role_layout.addWidget(self.match_placeholder_label)

        self.match_preview_table = QTableWidget(0, 4, role_card)
        self.match_preview_table.setHorizontalHeaderLabels(["部位", "当前装备", "候选装备", "说明"])
        self.match_preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.match_preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.match_preview_table.verticalHeader().setVisible(False)
        self.match_preview_table.verticalHeader().setDefaultSectionSize(34)
        role_layout.addWidget(self.match_preview_table)

        layout.addWidget(role_card, 1)
        self._load_role_gear_to_table(self.current_role_name)
        self._refresh_role_stat_overview()

    def _on_role_changed(self, _index: int) -> None:
        if not hasattr(self, "role_select_combo"):
            return
        selected_role = str(self.role_select_combo.currentData())
        if not selected_role or selected_role == self.current_role_name:
            return
        self._save_current_role_gear()
        self.current_role_name = selected_role
        self._load_role_gear_to_table(self.current_role_name)
        if hasattr(self, "match_placeholder_label"):
            self.match_placeholder_label.setText("状态: 未开始。点击“开始历史配对（占位）”生成占位结果。")
        if hasattr(self, "match_preview_table"):
            self.match_preview_table.setRowCount(0)
        self._save_settings()

    def _on_role_stat_table_changed(self, _item: QTableWidgetItem) -> None:
        if self._role_gear_loading:
            return
        self._save_current_role_gear()
        self._refresh_role_stat_overview()
        self._save_settings()

    def _save_current_role_gear(self) -> None:
        if not hasattr(self, "role_stat_table"):
            return
        rows: list[list[str]] = []
        for row_idx in range(len(ROLE_GEAR_SLOTS)):
            row_values: list[str] = []
            for col_idx in range(1, 5):
                item = self.role_stat_table.item(row_idx, col_idx)
                row_values.append("" if item is None else item.text().strip())
            rows.append(row_values)
        self.role_gear_store[self.current_role_name] = rows

    def _load_role_gear_to_table(self, role_name: str) -> None:
        if not hasattr(self, "role_stat_table"):
            return
        rows = self.role_gear_store.get(role_name, [["", "", "", ""] for _ in ROLE_GEAR_SLOTS])
        self._role_gear_loading = True
        self.role_stat_table.blockSignals(True)
        for row_idx in range(len(ROLE_GEAR_SLOTS)):
            row_values = rows[row_idx] if row_idx < len(rows) else ["", "", "", ""]
            for col_idx in range(1, 5):
                text_value = row_values[col_idx - 1] if col_idx - 1 < len(row_values) else ""
                item = self.role_stat_table.item(row_idx, col_idx)
                if item is None:
                    item = QTableWidgetItem("")
                    self.role_stat_table.setItem(row_idx, col_idx, item)
                item.setText(text_value)
        self.role_stat_table.blockSignals(False)
        self._role_gear_loading = False

    def _clear_current_role_gear(self) -> None:
        self.role_gear_store[self.current_role_name] = [["", "", "", ""] for _ in ROLE_GEAR_SLOTS]
        self._load_role_gear_to_table(self.current_role_name)
        self._refresh_role_stat_overview()
        if hasattr(self, "match_preview_table"):
            self.match_preview_table.setRowCount(0)
        if hasattr(self, "match_placeholder_label"):
            self.match_placeholder_label.setText("状态: 已清空当前角色装备。")
        self._save_settings()

    def _refresh_role_stat_overview(self) -> None:
        if not hasattr(self, "role_stat_table") or not hasattr(self, "role_stat_summary_label"):
            return
        filled = 0
        for row_idx in range(self.role_stat_table.rowCount()):
            equip_item = self.role_stat_table.item(row_idx, 1)
            if equip_item and equip_item.text().strip():
                filled += 1
        self.role_stat_summary_label.setText(
            f"{self.current_role_name} 统计进度: {filled}/{len(ROLE_GEAR_SLOTS)} 个部位已填写。"
        )

    def run_match_placeholder(self) -> None:
        self._save_current_role_gear()
        self._refresh_role_stat_overview()
        mode = str(self.match_mode_combo.currentData()) if hasattr(self, "match_mode_combo") else "single"
        goal = str(self.match_goal_combo.currentData()) if hasattr(self, "match_goal_combo") else "threshold"
        mode_text = "单部位匹配" if mode == "single" else "整套匹配"
        goal_text = "达标优先" if goal == "threshold" else "总分优先"
        self.match_placeholder_label.setText(
            f"状态: {self.current_role_name} 已触发占位流程（{mode_text} / {goal_text}）。后续版本将接入历史装备库自动配对。"
        )

        self.match_preview_table.setRowCount(len(ROLE_GEAR_SLOTS))
        for row_idx, slot in enumerate(ROLE_GEAR_SLOTS):
            current_item = self.role_stat_table.item(row_idx, 1) if hasattr(self, "role_stat_table") else None
            current_name = current_item.text().strip() if current_item else ""
            values = [
                slot,
                current_name or "-",
                "待计算",
                "占位结果：后续接入你的历史装备记录进行推荐",
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter if col_idx < 3 else Qt.AlignLeft | Qt.AlignVCenter)
                self.match_preview_table.setItem(row_idx, col_idx, item)
        self.match_preview_table.resizeColumnsToContents()

    def _build_settings_page(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("设置", panel)
        title.setObjectName("IntroTitle")
        desc = QLabel("这里用于管理应用存储路径与基础偏好。", panel)
        desc.setObjectName("IntroSub")
        layout.addWidget(title)
        layout.addWidget(desc)

        card = QFrame(panel)
        card.setObjectName("IntroSection")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)
        path_tip = QLabel("当前保存目录:", card)
        path_tip.setObjectName("IntroHint")
        self.settings_path_value_label = QLabel(str(self.config_dir), card)
        self.settings_path_value_label.setObjectName("IntroItem")
        self.settings_path_value_label.setWordWrap(True)
        btn_change = QPushButton("修改保存目录", card)
        btn_change.setObjectName("PrimaryButton")
        btn_change.clicked.connect(self.change_storage_directory)
        card_layout.addWidget(path_tip)
        card_layout.addWidget(self.settings_path_value_label)
        card_layout.addWidget(btn_change)
        layout.addWidget(card)
        layout.addStretch()

    def _build_input_panel(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("评分参数", panel)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        base_info_grid = QGridLayout()
        base_info_grid.setHorizontalSpacing(10)
        base_info_grid.setVerticalSpacing(8)

        def _base_label(text: str) -> QLabel:
            lbl = QLabel(text, panel)
            lbl.setFixedWidth(SCORE_BASE_LABEL_WIDTH)
            return lbl

        self.category_combo = QComboBox(panel)
        self.category_combo.setFixedWidth(SCORE_BASE_INPUT_WIDTH)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        base_info_grid.addWidget(_base_label("装备种类"), 0, 0)
        base_info_grid.addWidget(self.category_combo, 0, 1)

        btn_add_category = QPushButton("新增", panel)
        btn_add_category.setObjectName("GhostButton")
        btn_add_category.setFixedWidth(80)
        btn_add_category.clicked.connect(self._add_category)
        base_info_grid.addWidget(btn_add_category, 0, 2)

        self.equip_name_edit = QLineEdit(panel)
        self.equip_name_edit.setPlaceholderText("可选")
        self.equip_name_edit.setFixedWidth(SCORE_NAME_INPUT_WIDTH)
        base_info_grid.addWidget(_base_label("装备名称"), 0, 3)
        base_info_grid.addWidget(self.equip_name_edit, 0, 4)

        self.category_view = QLineEdit(panel)
        self.category_view.setReadOnly(True)
        self.category_view.setFixedWidth(SCORE_BASE_INPUT_WIDTH)
        self.category_view.setAlignment(Qt.AlignCenter)
        base_info_grid.addWidget(_base_label("当前种类"), 0, 5)
        base_info_grid.addWidget(self.category_view, 0, 6)
        base_info_grid.setColumnStretch(7, 1)
        layout.addLayout(base_info_grid)

        name_formula_row = QHBoxLayout()
        name_formula_row.setSpacing(6)
        head = QLabel("公式", panel)
        head.setObjectName("FieldHeader")
        head.setFixedWidth(FORMULA_HEAD_WIDTH)
        name_formula_row.addWidget(head)

        for i in range(models.FIELD_COUNT):
            attr_name_edit = QLineEdit(panel)
            attr_name_edit.setText(DEFAULT_ATTR_NAMES[i])
            attr_name_edit.setFixedWidth(FORMULA_INPUT_WIDTH)
            attr_name_edit.setAlignment(Qt.AlignCenter)
            attr_name_edit.editingFinished.connect(self._on_scheme_name_changed)
            self.attr_name_edits.append(attr_name_edit)
            name_formula_row.addWidget(attr_name_edit)

            mul = QLabel("*", panel)
            mul.setObjectName("FieldHeader")
            mul.setFixedWidth(FORMULA_SYMBOL_WIDTH)
            mul.setAlignment(Qt.AlignCenter)
            name_formula_row.addWidget(mul)

            coeff_name_edit = QLineEdit(panel)
            coeff_name_edit.setText(DEFAULT_COEFF_NAMES[i])
            coeff_name_edit.setFixedWidth(FORMULA_INPUT_WIDTH)
            coeff_name_edit.setAlignment(Qt.AlignCenter)
            coeff_name_edit.editingFinished.connect(self._on_scheme_name_changed)
            self.weight_name_edits.append(coeff_name_edit)
            name_formula_row.addWidget(coeff_name_edit)

            if i < models.FIELD_COUNT - 1:
                plus = QLabel("+", panel)
                plus.setObjectName("FieldHeader")
                plus.setFixedWidth(FORMULA_SYMBOL_WIDTH)
                plus.setAlignment(Qt.AlignCenter)
                name_formula_row.addWidget(plus)

        eq_name = QLabel("=", panel)
        eq_name.setObjectName("FieldHeader")
        eq_name.setFixedWidth(FORMULA_SYMBOL_WIDTH)
        eq_name.setAlignment(Qt.AlignCenter)
        name_formula_row.addWidget(eq_name)
        score_literal = QLabel("score", panel)
        score_literal.setFixedWidth(FORMULA_RESULT_WIDTH)
        score_literal.setAlignment(Qt.AlignCenter)
        name_formula_row.addWidget(score_literal)
        name_formula_row.addStretch()
        layout.addLayout(name_formula_row)

        value_formula_row = QHBoxLayout()
        value_formula_row.setSpacing(6)
        value_head = QLabel("数值", panel)
        value_head.setObjectName("FieldHeader")
        value_head.setFixedWidth(FORMULA_HEAD_WIDTH)
        value_formula_row.addWidget(value_head)

        for i in range(models.FIELD_COUNT):
            attr_edit = QLineEdit(panel)
            attr_edit.setPlaceholderText("0")
            attr_edit.setFixedWidth(FORMULA_INPUT_WIDTH)
            attr_edit.setAlignment(Qt.AlignCenter)
            attr_edit.returnPressed.connect(self.calculate_score)
            self.attr_value_edits.append(attr_edit)
            value_formula_row.addWidget(attr_edit)

            mul = QLabel("*", panel)
            mul.setObjectName("FieldHeader")
            mul.setFixedWidth(FORMULA_SYMBOL_WIDTH)
            mul.setAlignment(Qt.AlignCenter)
            value_formula_row.addWidget(mul)

            coeff_edit = ClickInputLineEdit(panel)
            coeff_edit.setText("0")
            coeff_edit.setFixedWidth(FORMULA_INPUT_WIDTH)
            coeff_edit.setReadOnly(True)
            coeff_edit.setAlignment(Qt.AlignCenter)
            coeff_edit.setToolTip("点击输入系数值")
            coeff_edit.clicked.connect(lambda _=None, idx=i: self._edit_coeff_value(idx))
            self.weight_value_edits.append(coeff_edit)
            value_formula_row.addWidget(coeff_edit)

            if i < models.FIELD_COUNT - 1:
                plus = QLabel("+", panel)
                plus.setObjectName("FieldHeader")
                plus.setFixedWidth(FORMULA_SYMBOL_WIDTH)
                plus.setAlignment(Qt.AlignCenter)
                value_formula_row.addWidget(plus)

        eq_value = QLabel("=", panel)
        eq_value.setObjectName("FieldHeader")
        eq_value.setFixedWidth(FORMULA_SYMBOL_WIDTH)
        eq_value.setAlignment(Qt.AlignCenter)
        value_formula_row.addWidget(eq_value)
        self.inline_score_value_label = QLabel("0.000", panel)
        self.inline_score_value_label.setObjectName("ScoreValue")
        self.inline_score_value_label.setFixedWidth(FORMULA_RESULT_WIDTH)
        self.inline_score_value_label.setAlignment(Qt.AlignCenter)
        value_formula_row.addWidget(self.inline_score_value_label)
        value_formula_row.addStretch()
        layout.addLayout(value_formula_row)

        threshold_row = QHBoxLayout()
        threshold_label = QLabel("阈值", panel)
        threshold_label.setFixedWidth(SCORE_BASE_LABEL_WIDTH)
        threshold_row.addWidget(threshold_label)
        self.threshold_edit = ClickInputLineEdit(panel)
        self.threshold_edit.setText("0")
        self.threshold_edit.setFixedWidth(SCORE_BASE_INPUT_WIDTH)
        self.threshold_edit.setAlignment(Qt.AlignCenter)
        self.threshold_edit.setReadOnly(True)
        self.threshold_edit.setToolTip("点击输入阈值")
        self.threshold_edit.clicked.connect(self._edit_threshold_value)
        threshold_row.addWidget(self.threshold_edit)
        threshold_row.addStretch()
        layout.addLayout(threshold_row)

        btn_row = QHBoxLayout()
        btn_calculate = QPushButton("计算", panel)
        btn_clear = QPushButton("清空属性值", panel)
        btn_save_scheme = QPushButton("保存方案(CSV)", panel)
        btn_load_scheme = QPushButton("加载方案(CSV)", panel)
        btn_calculate.setObjectName("PrimaryButton")
        btn_clear.setObjectName("GhostButton")
        btn_save_scheme.setObjectName("GhostButton")
        btn_load_scheme.setObjectName("GhostButton")
        btn_calculate.clicked.connect(self.calculate_score)
        btn_clear.clicked.connect(self.clear_numeric_inputs)
        btn_save_scheme.clicked.connect(self.save_scheme_csv)
        btn_load_scheme.clicked.connect(self.load_scheme_csv)
        btn_row.addWidget(btn_calculate)
        btn_row.addWidget(btn_clear)
        btn_row.addWidget(btn_save_scheme)
        btn_row.addWidget(btn_load_scheme)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        score_row = QHBoxLayout()
        self.score_label = QLabel("总分: 0.000", panel)
        self.score_label.setObjectName("TitleLabel")
        self.pass_label = QLabel("❌ 未达标", panel)
        self.pass_label.setObjectName("StatusFail")
        score_row.addWidget(self.score_label)
        score_row.addSpacing(12)
        score_row.addWidget(self.pass_label)
        score_row.addStretch()
        layout.addLayout(score_row)

        self.formula_value_label = QLabel("当前: 0*0 + 0*0 + 0*0 + 0*0 + 0*0 = 0.000", panel)
        self.formula_value_label.setObjectName("FormulaLine")
        self.contribution_line_label = QLabel("贡献: 项1=0.000 | 项2=0.000 | 项3=0.000 | 项4=0.000 | 项5=0.000", panel)
        self.contribution_line_label.setObjectName("FormulaLine")
        self.calc_error_label = QLabel("", panel)
        self.calc_error_label.setObjectName("ErrorLabel")
        self.calc_error_label.setWordWrap(True)
        self.calc_error_label.setVisible(False)

        layout.addWidget(self.formula_value_label)
        layout.addWidget(self.contribution_line_label)
        layout.addWidget(self.calc_error_label)
        layout.addStretch()

    def _build_records_panel(self, panel: QWidget) -> None:
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("记录列表", panel)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("搜索", panel))
        self.name_filter_edit = QLineEdit(panel)
        self.name_filter_edit.setPlaceholderText("输入装备名关键词")
        self.name_filter_edit.textChanged.connect(self.refresh_records_table)
        filter_row.addWidget(self.name_filter_edit, 1)
        filter_row.addSpacing(8)
        filter_row.addWidget(QLabel("范围", panel))
        self.record_scope_combo = QComboBox(panel)
        self.record_scope_combo.addItem("全部记录", "all")
        self.record_scope_combo.addItem("仅当前种类", "current")
        self.record_scope_combo.currentIndexChanged.connect(self.refresh_records_table)
        filter_row.addWidget(self.record_scope_combo)
        layout.addLayout(filter_row)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("保存", panel)
        btn_delete = QPushButton("删除", panel)
        btn_clear_all = QPushButton("清空", panel)
        btn_import = QPushButton("导入 CSV", panel)
        btn_export = QPushButton("导出 CSV", panel)
        btn_save.setObjectName("SuccessButton")
        btn_delete.setObjectName("DangerButton")
        btn_clear_all.setObjectName("DangerButton")
        btn_import.setObjectName("GhostButton")
        btn_export.setObjectName("GhostButton")
        btn_save.clicked.connect(self.save_current_equip)
        btn_delete.clicked.connect(self.delete_selected_records)
        btn_clear_all.clicked.connect(self.clear_all_records)
        btn_import.clicked.connect(self.import_records_csv)
        btn_export.clicked.connect(self.export_records_csv)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_delete)
        btn_row.addWidget(btn_clear_all)
        btn_row.addWidget(btn_import)
        btn_row.addWidget(btn_export)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        summary_row = QHBoxLayout()
        self.summary_total_label = QLabel("总记录: 0", panel)
        self.summary_pass_label = QLabel("达标数: 0", panel)
        self.summary_avg_label = QLabel("平均分: 0.000", panel)
        self.summary_total_label.setObjectName("StatChip")
        self.summary_pass_label.setObjectName("StatChip")
        self.summary_avg_label.setObjectName("StatChip")
        summary_row.addWidget(self.summary_total_label)
        summary_row.addWidget(self.summary_pass_label)
        summary_row.addWidget(self.summary_avg_label)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        sort_card = QFrame(panel)
        sort_card.setObjectName("CardFrame")
        sort_layout = QVBoxLayout(sort_card)
        sort_layout.setContentsMargins(10, 10, 10, 10)
        sort_layout.setSpacing(8)
        sort_title = QLabel("多字段排序（最多 3 条）", sort_card)
        sort_title.setObjectName("SectionTitle")
        sort_layout.addWidget(sort_title)
        self.sort_rules_layout = QVBoxLayout()
        sort_layout.addLayout(self.sort_rules_layout)

        sort_btns = QHBoxLayout()
        btn_add_sort = QPushButton("添加排序字段", sort_card)
        btn_apply_sort = QPushButton("应用排序", sort_card)
        btn_reset_sort = QPushButton("重置排序规则", sort_card)
        btn_add_sort.setObjectName("GhostButton")
        btn_apply_sort.setObjectName("PrimaryButton")
        btn_reset_sort.setObjectName("GhostButton")
        btn_add_sort.clicked.connect(self.add_sort_rule)
        btn_apply_sort.clicked.connect(self.apply_sort_rules)
        btn_reset_sort.clicked.connect(self._reset_sort_rules)
        sort_btns.addWidget(btn_add_sort)
        sort_btns.addWidget(btn_apply_sort)
        sort_btns.addWidget(btn_reset_sort)
        sort_btns.addStretch()
        sort_layout.addLayout(sort_btns)
        layout.addWidget(sort_card)

        self.records_table = QTableWidget(0, 10, panel)
        self.records_table.setHorizontalHeaderLabels(["种类", "装备名", "a1", "a2", "a3", "a4", "a5", "总分", "达标", "保存时间"])
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.records_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.records_table, 1)

    def _sync_category_combo(self) -> None:
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        for category in self.categories:
            self.category_combo.addItem(category)
        if self.current_category not in self.categories:
            self.current_category = self.categories[0]
        self.category_combo.setCurrentText(self.current_category)
        self.category_combo.blockSignals(False)
        self.category_view.setText(self.current_category)
        self.hero_category_tag.setText(f"当前种类: {self.current_category}")

    def _update_storage_tag(self) -> None:
        self.hero_auto_save_tag.setText(f"保存目录: {self.config_dir}")
        self.hero_auto_save_tag.setToolTip(str(self.config_dir))
        if hasattr(self, "settings_path_value_label"):
            self.settings_path_value_label.setText(str(self.config_dir))

    def change_storage_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择保存目录", str(self.config_dir))
        if not selected:
            return

        new_dir = Path(selected).expanduser()
        if new_dir == self.config_dir:
            return

        old_dir = self.config_dir
        old_category = self.current_category
        old_threshold = self.threshold_edit.text()

        try:
            self.config_dir = new_dir
            self._rebind_storage_paths()
            self._ensure_storage()

            self.categories = self._load_categories()
            settings = self._load_settings()
            fallback_category = settings.get("current_category", old_category)
            self.current_category = _safe_category_name(fallback_category)
            self.global_threshold = models.parse_float(str(settings.get("threshold", old_threshold)), "")[0]
            self.saved_crit_atlas = str(settings.get("cap_crit_atlas", self.saved_crit_atlas))
            self.saved_dodge_atlas = str(settings.get("cap_dodge_atlas", self.saved_dodge_atlas))
            self.role_gear_store = self._normalize_role_gear_store(settings.get("role_gear_store", {}))
            saved_role_name = str(settings.get("current_role_name", self.current_role_name))
            self.current_role_name = saved_role_name if saved_role_name in ROLE_CHARACTER_NAMES else ROLE_CHARACTER_NAMES[0]
            self.crit_atlas_edit.setText(self.saved_crit_atlas)
            self.dodge_atlas_edit.setText(self.saved_dodge_atlas)
            if hasattr(self, "role_select_combo"):
                self.role_select_combo.blockSignals(True)
                self.role_select_combo.setCurrentText(self.current_role_name)
                self.role_select_combo.blockSignals(False)
            if hasattr(self, "role_stat_table"):
                self._load_role_gear_to_table(self.current_role_name)
                self._refresh_role_stat_overview()
            if hasattr(self, "match_preview_table"):
                self.match_preview_table.setRowCount(0)
            if hasattr(self, "match_placeholder_label"):
                self.match_placeholder_label.setText("状态: 未开始。点击“开始历史配对（占位）”生成占位结果。")

            self._load_global_scheme()
            self.threshold_edit.setText(f"{self.global_threshold:g}")
            self._sync_category_combo()
            self._update_storage_tag()
            self._save_bootstrap()
            self._save_settings()
            self.calculate_score()
            QMessageBox.information(self, "完成", f"保存目录已切换到:\n{self.config_dir}")
        except Exception as exc:
            self.config_dir = old_dir
            self._rebind_storage_paths()
            self._update_storage_tag()
            QMessageBox.critical(self, "切换失败", f"无法切换保存目录:\n{exc}")

    def _load_global_scheme(self) -> None:
        self._suspend_auto_save = True
        if self.global_scheme_path.exists():
            try:
                attr_names, coeff_names, coeff_values, _warnings = csv_io.load_scheme_csv(str(self.global_scheme_path))
                for i in range(models.FIELD_COUNT):
                    self.attr_name_edits[i].setText(attr_names[i] or DEFAULT_ATTR_NAMES[i])
                    self.weight_name_edits[i].setText(coeff_names[i] or DEFAULT_COEFF_NAMES[i])
                    self.weight_value_edits[i].setText(f"{coeff_values[i]:g}")
            except Exception:
                for i in range(models.FIELD_COUNT):
                    self.attr_name_edits[i].setText(DEFAULT_ATTR_NAMES[i])
                    self.weight_name_edits[i].setText(DEFAULT_COEFF_NAMES[i])
                    self.weight_value_edits[i].setText("0")
        else:
            for i in range(models.FIELD_COUNT):
                self.attr_name_edits[i].setText(DEFAULT_ATTR_NAMES[i])
                self.weight_name_edits[i].setText(DEFAULT_COEFF_NAMES[i])
                self.weight_value_edits[i].setText("0")
        self._suspend_auto_save = False

    def _save_global_scheme(self) -> None:
        if self._suspend_auto_save:
            return
        coeff_values = [models.parse_float(edit.text(), "")[0] for edit in self.weight_value_edits]
        csv_io.save_scheme_csv(
            str(self.global_scheme_path),
            self._current_attr_names(),
            self._current_coeff_names(),
            coeff_values,
        )

    def _current_attr_names(self) -> list[str]:
        return [edit.text().strip() or DEFAULT_ATTR_NAMES[i] for i, edit in enumerate(self.attr_name_edits)]

    def _current_coeff_names(self) -> list[str]:
        return [edit.text().strip() or DEFAULT_COEFF_NAMES[i] for i, edit in enumerate(self.weight_name_edits)]

    def _on_scheme_name_changed(self) -> None:
        for i, edit in enumerate(self.attr_name_edits):
            if edit.text().strip() == "":
                edit.setText(DEFAULT_ATTR_NAMES[i])
        for i, edit in enumerate(self.weight_name_edits):
            if edit.text().strip() == "":
                edit.setText(DEFAULT_COEFF_NAMES[i])
        self._save_global_scheme()
        self.calculate_score()

    def _on_category_changed(self, text: str) -> None:
        self.current_category = _safe_category_name(text)
        self.category_view.setText(self.current_category)
        self.hero_category_tag.setText(f"当前种类: {self.current_category}")
        self._save_settings()
        self.refresh_records_table()

    def _add_category(self) -> None:
        text, ok = QInputDialog.getText(self, "新增装备种类", "请输入种类名称:")
        if not ok:
            return
        category = _safe_category_name(text)
        if category in self.categories:
            self.category_combo.setCurrentText(category)
            return
        self.categories.append(category)
        self._save_categories()
        self._sync_category_combo()
        self.category_combo.setCurrentText(category)

    def _edit_coeff_value(self, index: int) -> None:
        if not (0 <= index < len(self.weight_value_edits)):
            return
        current = models.parse_float(self.weight_value_edits[index].text(), "")[0]
        value, ok = QInputDialog.getDouble(
            self,
            f"设置系数{index + 1}",
            f"请输入 系数{index + 1} 的值:",
            current,
            -999999999.0,
            999999999.0,
            6,
        )
        if not ok:
            return
        self.weight_value_edits[index].setText(f"{value:g}")
        self._save_global_scheme()
        self.calculate_score()

    def _edit_threshold_value(self) -> None:
        current = models.parse_float(self.threshold_edit.text(), "")[0]
        value, ok = QInputDialog.getDouble(self, "设置阈值", "请输入阈值:", current, -999999999.0, 999999999.0, 6)
        if not ok:
            return
        self.threshold_edit.setText(f"{value:g}")
        self._save_settings()
        self.calculate_score()

    def _collect_current_values(self, strict_invalid: bool) -> tuple[models.CalculationSnapshot | None, list[str]]:
        for edit in self.attr_value_edits + self.weight_value_edits + [self.threshold_edit]:
            edit.setStyleSheet("")

        attr_values, attr_errors, attr_invalid = models.safe_numeric_list([edit.text() for edit in self.attr_value_edits], "属性值")
        coeff_values, coeff_errors, coeff_invalid = models.safe_numeric_list([edit.text() for edit in self.weight_value_edits], "系数值")
        threshold, threshold_ok, threshold_err = models.parse_float(self.threshold_edit.text(), "阈值")

        for idx in attr_invalid:
            self.attr_value_edits[idx].setStyleSheet(ERROR_STYLE)
        for idx in coeff_invalid:
            self.weight_value_edits[idx].setStyleSheet(ERROR_STYLE)
        if not threshold_ok:
            self.threshold_edit.setStyleSheet(ERROR_STYLE)

        errors = attr_errors + coeff_errors
        if threshold_err:
            errors.append(threshold_err)
        if strict_invalid and errors:
            return None, errors
        return models.calculate(attr_values, coeff_values, threshold), errors

    def calculate_score(self) -> models.CalculationSnapshot | None:
        snapshot, errors = self._collect_current_values(strict_invalid=False)
        if snapshot is None:
            return None

        self.score_label.setText(f"总分: {snapshot.score:.3f}")
        self.inline_score_value_label.setText(f"{snapshot.score:.3f}")
        if snapshot.passed:
            self.pass_label.setText("✅ 达标")
            self.pass_label.setObjectName("StatusPass")
        else:
            self.pass_label.setText("❌ 未达标")
            self.pass_label.setObjectName("StatusFail")
        self.pass_label.style().unpolish(self.pass_label)
        self.pass_label.style().polish(self.pass_label)

        terms = [f"{snapshot.attrs[i]:g}*{snapshot.weights[i]:g}" for i in range(models.FIELD_COUNT)]
        contributions = [f"项{i + 1}={snapshot.contributions[i]:.3f}" for i in range(models.FIELD_COUNT)]
        self.formula_value_label.setText("当前: " + " + ".join(terms) + f" = {snapshot.score:.3f}")
        self.contribution_line_label.setText("贡献: " + " | ".join(contributions))

        if errors:
            self.calc_error_label.setText("检测到非法输入，已按 0 处理: " + "；".join(errors))
            self.calc_error_label.setVisible(True)
        else:
            self.calc_error_label.setText("")
            self.calc_error_label.setVisible(False)
        return snapshot

    def clear_numeric_inputs(self) -> None:
        for edit in self.attr_value_edits:
            edit.clear()
            edit.setStyleSheet("")
        self.threshold_edit.setText("0")
        self.threshold_edit.setStyleSheet("")
        self._save_settings()
        self.calculate_score()

    def save_scheme_csv(self) -> None:
        default_path = str(self.config_dir / "方案.csv")
        file_path, _ = QFileDialog.getSaveFileName(self, "保存方案", default_path, "CSV Files (*.csv)")
        if not file_path:
            return
        _, errors = self._collect_current_values(strict_invalid=False)
        if errors:
            QMessageBox.warning(self, "输入提示", "保存时发现非法输入，相关数值已按 0 写入。")
        coeff_values, _, _ = models.safe_numeric_list([edit.text() for edit in self.weight_value_edits], "系数值")
        csv_io.save_scheme_csv(file_path, self._current_attr_names(), self._current_coeff_names(), coeff_values)
        QMessageBox.information(self, "完成", "方案已保存。")

    def load_scheme_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "加载方案", str(self.config_dir), "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            attr_names, coeff_names, coeff_values, warnings = csv_io.load_scheme_csv(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "加载失败", str(exc))
            return

        self._suspend_auto_save = True
        for i in range(models.FIELD_COUNT):
            self.attr_name_edits[i].setText(attr_names[i] or DEFAULT_ATTR_NAMES[i])
            self.weight_name_edits[i].setText(coeff_names[i] or DEFAULT_COEFF_NAMES[i])
            self.weight_value_edits[i].setText(f"{coeff_values[i]:g}")
        self._suspend_auto_save = False
        self._save_global_scheme()
        self.calculate_score()

        if warnings:
            QMessageBox.warning(self, "加载提示", "\n".join(warnings))
        else:
            QMessageBox.information(self, "完成", "方案已加载。")

    def _get_filtered_pairs(self) -> list[tuple[int, EquipRecord]]:
        keyword = self.name_filter_edit.text().strip().lower()
        scope = str(self.record_scope_combo.currentData())
        pairs: list[tuple[int, EquipRecord]] = []
        for idx, record in enumerate(self.records):
            if scope == "current" and record.category != self.current_category:
                continue
            if keyword and keyword not in record.name.lower():
                continue
            pairs.append((idx, record))
        return pairs

    def _sorted_pairs(self, pairs: list[tuple[int, EquipRecord]], show_warning: bool = False) -> list[tuple[int, EquipRecord]]:
        if not pairs:
            return []
        records_only = [record for _, record in pairs]
        sorted_records, warnings = sort_records(records_only, self.active_sort_rules)

        id_map: dict[int, list[int]] = {}
        for idx, record in pairs:
            id_map.setdefault(id(record), []).append(idx)

        output: list[tuple[int, EquipRecord]] = []
        for record in sorted_records:
            indexes = id_map.get(id(record), [])
            if not indexes:
                continue
            output.append((indexes.pop(0), record))

        if show_warning and warnings:
            QMessageBox.warning(self, "排序提示", "\n".join(warnings))
        return output

    def save_current_equip(self) -> None:
        snapshot, errors = self._collect_current_values(strict_invalid=True)
        if snapshot is None:
            QMessageBox.warning(self, "无法保存", "检测到非法数字，无法保存当前装备。\n" + "\n".join(errors))
            return

        self.calculate_score()
        self.records.append(
            EquipRecord(
                category=self.current_category,
                name=self.equip_name_edit.text().strip(),
                attrs=snapshot.attrs,
                weights=snapshot.weights,
                score=snapshot.score,
                pass_threshold=snapshot.passed,
                created_at=datetime.now().strftime(TIME_FORMAT),
            )
        )
        self.refresh_records_table()

    def delete_selected_records(self) -> None:
        selected = self.records_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择一条记录。")
            return

        to_delete: list[int] = []
        for item in selected:
            row = item.row()
            if 0 <= row < len(self.visible_record_indexes):
                to_delete.append(self.visible_record_indexes[row])

        for idx in sorted(set(to_delete), reverse=True):
            if 0 <= idx < len(self.records):
                self.records.pop(idx)
        self.refresh_records_table()

    def clear_all_records(self) -> None:
        if not self.records:
            return
        answer = QMessageBox.question(
            self,
            "二次确认",
            "确定要清空全部装备记录吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.records.clear()
            self.refresh_records_table()

    def export_records_csv(self) -> None:
        default_path = str(self.config_dir / "装备记录.csv")
        file_path, _ = QFileDialog.getSaveFileName(self, "导出装备CSV", default_path, "CSV Files (*.csv)")
        if not file_path:
            return
        csv_io.export_equips_csv(file_path, self.records)
        QMessageBox.information(self, "完成", f"已导出 {len(self.records)} 条记录。")

    def import_records_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "导入装备CSV", str(self.config_dir), "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            imported_records, warnings = csv_io.import_equips_csv(file_path)
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", str(exc))
            return

        self.records.extend(imported_records)
        for record in imported_records:
            if record.category not in self.categories:
                self.categories.append(record.category)
        self._save_categories()
        self._sync_category_combo()
        self.refresh_records_table()

        if warnings:
            QMessageBox.warning(self, "导入提示", "\n".join(warnings))
        else:
            QMessageBox.information(self, "完成", f"已导入 {len(imported_records)} 条记录。")

    def refresh_records_table(self) -> None:
        filtered_pairs = self._get_filtered_pairs()
        sorted_pairs = self._sorted_pairs(filtered_pairs, show_warning=False)
        self.visible_record_indexes = [idx for idx, _ in sorted_pairs]

        self.records_table.setRowCount(len(sorted_pairs))
        visible_records: list[EquipRecord] = []
        for row_idx, (_idx, record) in enumerate(sorted_pairs):
            visible_records.append(record)
            values = [
                record.category,
                record.name,
                *[f"{v:g}" for v in record.attrs[:5]],
                f"{record.score:.3f}",
                "✅" if record.pass_threshold else "❌",
                record.created_at,
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.records_table.setItem(row_idx, col_idx, item)
        self.records_table.resizeColumnsToContents()
        self._update_summary_labels(visible_records)

    def _update_summary_labels(self, visible_records: list[EquipRecord]) -> None:
        total = len(self.records)
        visible = len(visible_records)
        pass_count = sum(1 for item in visible_records if item.pass_threshold)
        avg_score = sum(item.score for item in visible_records) / visible if visible else 0.0

        self.summary_total_label.setText(f"总记录: {total} / 显示: {visible}")
        self.summary_pass_label.setText(f"当前达标: {pass_count}")
        self.summary_avg_label.setText(f"当前平均分: {avg_score:.3f}")
        self.hero_record_tag.setText(f"记录总数: {total}")
        self.hero_category_tag.setText(f"当前种类: {self.current_category}")

    def add_sort_rule(self) -> None:
        if len(self.sort_rule_rows) >= MAX_SORT_RULES:
            QMessageBox.information(self, "提示", f"最多支持 {MAX_SORT_RULES} 条排序规则。")
            return
        self._create_sort_rule("score", False)
        self._refresh_sort_rule_rows()

    def apply_sort_rules(self) -> None:
        self.active_sort_rules = [row.to_rule() for row in self.sort_rule_rows]
        pairs = self._sorted_pairs(self._get_filtered_pairs(), show_warning=True)
        self.visible_record_indexes = [idx for idx, _ in pairs]
        self.refresh_records_table()

    def _create_sort_rule(self, field: str, asc: bool) -> None:
        row = SortRuleRow(self._move_rule_up, self._move_rule_down, self._delete_rule, self)
        row.set_rule(field, asc)
        self.sort_rule_rows.append(row)

    def _refresh_sort_rule_rows(self) -> None:
        while self.sort_rules_layout.count():
            item = self.sort_rules_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        for idx, row in enumerate(self.sort_rule_rows, start=1):
            row.set_priority(idx)
            self.sort_rules_layout.addWidget(row)

    def _move_rule_up(self, row: SortRuleRow) -> None:
        idx = self.sort_rule_rows.index(row)
        if idx <= 0:
            return
        self.sort_rule_rows[idx - 1], self.sort_rule_rows[idx] = self.sort_rule_rows[idx], self.sort_rule_rows[idx - 1]
        self._refresh_sort_rule_rows()

    def _move_rule_down(self, row: SortRuleRow) -> None:
        idx = self.sort_rule_rows.index(row)
        if idx >= len(self.sort_rule_rows) - 1:
            return
        self.sort_rule_rows[idx + 1], self.sort_rule_rows[idx] = self.sort_rule_rows[idx], self.sort_rule_rows[idx + 1]
        self._refresh_sort_rule_rows()

    def _delete_rule(self, row: SortRuleRow) -> None:
        if len(self.sort_rule_rows) <= 1:
            QMessageBox.information(self, "提示", "至少保留一条排序规则。")
            return
        self.sort_rule_rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self._refresh_sort_rule_rows()

    def _reset_sort_rules(self) -> None:
        for row in self.sort_rule_rows:
            row.setParent(None)
            row.deleteLater()
        self.sort_rule_rows.clear()
        self._create_sort_rule("score", False)
        self.active_sort_rules = [("score", False)]
        self._refresh_sort_rule_rows()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_global_scheme()
        self._save_settings()
        self._save_categories()
        self._save_bootstrap()
        super().closeEvent(event)
