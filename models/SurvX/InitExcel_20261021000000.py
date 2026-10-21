# -*- coding: utf-8 -*-
"""
InitExcel.py

中文：生成 SensorSim 初始化 Excel 模板，每个表一个 sheet，列名为字段。
English: Generate SensorSim init Excel template, one sheet per table.

版本: 20261021000000
作者: quruyi
时间: 20261021000000

用法:
    python InitExcel.py
"""

from openpyxl import Workbook


# 表名 -> 字段列表
SHEETS = {
    # ---- SQLite: Matter ----
    "Matter": ["key", "value", "version"],

    # ---- DuckDB: Energy ----
    "_parameter": ["id0", "id1", "value", "idx", "version"],
    "_constraint": ["id0", "id1", "value", "idx", "version"],
    "_relation": ["id0", "id1", "value", "idx", "version"],
    "_sequence": ["_tick", "key", "value"],
    "_experience": ["_from", "_tick", "_type", "_value"],
    "_intent": ["_from", "_tick", "key", "value"],
    "_feedback": ["_from", "_tick", "value"],
    "_language": ["key", "value"],
    "_train": ["_target", "_tick", "key", "value"],
    "_report": ["_type", "_tick", "key", "value"],
    "_llm": ["id", "version", "prompt", "reason"],
    "_register": ["key", "value"],

    # ---- SQLite: 质量控制 ----
    "_forge": ["id", "_tick", "_module", "_action", "_target", "_result", "_reason"],
}


def main():
    wb = Workbook()
    # 删除默认 sheet
    wb.remove(wb.active)

    for sheet_name, columns in SHEETS.items():
        ws = wb.create_sheet(title=sheet_name)
        # 字段列 + note 列（note 仅手工备注，灌库时跳过）
        ws.append(columns + ["note"])

    wb.save("Init.xlsx")
    print("已生成 Init.xlsx")
    print(f"共 {len(SHEETS)} 个 sheet：")
    for name in SHEETS:
        print(f"  - {name}")


if __name__ == "__main__":
    main()