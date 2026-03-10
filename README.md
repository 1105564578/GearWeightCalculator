# GearWeightCalculator

基于 `PySide6` 的猎魔村物语装备辅助桌面工具。

当前版本重点是：
- 装备评分与记录管理
- 攻速计算
- 暴击/闪避总和计算
- 配装词条推荐
- 角色装备统计与历史配对占位流程

## 功能清单

### 1) 装备评分与记录管理
- 评分公式：`score = a1*w1 + a2*w2 + a3*w3 + a4*w4 + a5*w5`
- 阈值判定：`score >= threshold`
- 属性名、系数名、系数值可维护并保存到本地方案文件
- 支持按种类保存记录、筛选记录、排序记录
- 支持装备 CSV 导入/导出

### 2) 攻速计算
- 输入项：武器攻速、特性系数、目标攻速、装备加成、猎人品质、秘法、公会、宠物装备、性格、实测面板
- 输出项：当前攻速、差值、是否达标、还需补充百分比
- 固定下限：目标攻速最低按 `0.25` 判定

### 3) 暴击/闪避模块
- 模板切换：近战 / 远程
- 品质修正默认橙色（`+0`）
- 公会/秘法为固定值且只读：
  - 暴击：公会 `5`、秘法 `10`
  - 闪避：公会 `0`、秘法 `10`
- 自身满暴击/闪避按模板固定并只读：
  - 近战：`8 / 8`
  - 远程：`11 / 11`
- 图鉴由用户手填，并自动保存到设置文件
- 暴击和闪避分别有独立按钮：
  - `判断暴击达标`
  - `判断闪避达标`
- 当前界面只保留 `总和暴击` / `总和闪避`，不显示文本结果行

### 4) 配装推荐
- 组合维度：职业 + 目标玩法（输出/生存/平衡）
- 输出词条优先级与建议文案

### 5) 角色装备统计与历史配对（占位）
- 在左侧导航新增独立“角色装备”页面
- 支持 `22` 个角色切换（`角色01` ~ `角色22`），每个角色单独维护一套装备表
- 每个角色可录入 `8` 个部位（武器/头盔/护甲/护手/鞋子/腰带/项链/戒指）
- 支持选择占位模式（单部位/整套）与目标（达标优先/总分优先）
- 点击“开始历史配对（占位）”后会生成占位预览表
- 当前为占位流程，尚未接入真实历史装备库匹配算法
- 当前 `22` 角色装备表会自动保存并在下次启动恢复

### 6) 养成成本表
- 内置手工记录表（资源/用途/当前数量/目标数量/备注）
- 仅记录，不自动计算

### 7) 设置
- 可切换保存目录
- 切换后自动重载该目录下的配置文件

## 运行环境
- Python `3.10+`（建议 `3.11`）
- 依赖见 `requirements.txt`

## 快速开始（Conda）

```powershell
cd E:\tools\GearWeightCalculator
conda create -n gwc python=3.11 -y
conda activate gwc
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.main
```

如果你使用的是 `pwc` 环境，也可以替换环境名后直接运行。

## 数据存储与持久化

默认保存目录：
- `%USERPROFILE%\.gear_weight_calculator`

目录文件：
- `global_scheme.csv`：评分方案（属性名、系数名、系数值）
- `categories.json`：装备种类
- `settings.json`：界面设置（当前种类、阈值、图鉴暴击、图鉴闪避、当前角色、22角色装备表）

固定引导文件：
- `%USERPROFILE%\.gear_weight_calculator\bootstrap.json`
- 用于记录“当前保存目录”

注意：
- 装备记录列表是内存数据，不会在退出时自动落盘。
- 角色装备页面中的 `22` 角色统计表会写入 `settings.json` 并在下次启动恢复。
- 如需持久保存记录，请手动导出装备 CSV。

## CSV 格式

### 方案 CSV（严格表头）

```csv
attr_name,weight_name,weight
力量,权重1,1.2
敏捷,权重2,0.8
体力,权重3,1.0
命中,权重4,0.9
暴击,权重5,1.5
```

### 装备 CSV（导出格式）

```csv
category,name,a1,a2,a3,a4,a5,w1,w2,w3,w4,w5,score,pass_threshold,created_at
武器,雷神,12,34,5,6,7,2,1.5,1,1,0.8,89.000,true,2026-02-12 12:34:56
```

导入兼容：
- `V2`：包含 `category`
- `V1`：不包含 `category`，会自动归到“通用”

## 项目结构

```text
app/
  main.py            # 程序入口
  ui_mainwindow.py   # 主界面与交互逻辑
  core.py            # 计算、排序、数据模型
  csv_io.py          # CSV 导入导出
requirements.txt
README.md
```

## 打包 EXE（Windows）

```powershell
cd E:\tools\GearWeightCalculator
conda activate gwc
pyinstaller --onefile --noconsole --name GearWeightCalculator app/main.py
```

如需图标：

```powershell
pyinstaller --onefile --noconsole --name GearWeightCalculator --icon app/resources/icon.ico app/main.py
```

产物：
- `dist\GearWeightCalculator.exe`

## 常见问题

### 1) Qt 绑定冲突

```powershell
pip uninstall -y PyQt5 PyQt6 PySide2
pip install --force-reinstall PySide6
```

建议不要在同一环境混装多个 Qt 绑定。

### 2) `--onefile` 首次启动慢
- 正常现象，首次运行会有临时解压过程。

## 后续计划（开发中）
- 接入“历史装备库”真实匹配算法（替换当前占位流程）
- 增加角色当前面板与替换前后差值对比
- 增加方案存档与一键切换
