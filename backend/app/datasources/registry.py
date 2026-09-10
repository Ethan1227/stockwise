"""数据源注册表：register / list / get / run。"""
from app.datasources.base import DataSourceAdapter

_REGISTRY: dict[str, DataSourceAdapter] = {}


def register(adapter: DataSourceAdapter) -> None:
    """注册一个适配器（新增数据源 = 新文件 + 此处/文件底部一行注册）。"""
    _REGISTRY[adapter.source_code] = adapter


def list_adapters() -> list[DataSourceAdapter]:
    return list(_REGISTRY.values())


def get(source_code: str) -> DataSourceAdapter | None:
    return _REGISTRY.get(source_code)


def run(source_code: str, db, file_path: str) -> dict:
    """执行导入：fetch -> normalize -> validate -> load，返回统计与错误明细。

    返回：{"total": n, "success": n, "errors": [{row, message}]}
    """
    adapter = get(source_code)
    if adapter is None:
        raise ValueError(f"未知数据源：{source_code}")

    raw_rows = adapter.fetch(file_path)
    records: list[dict] = []
    errors: list[dict] = []

    for idx, row in enumerate(raw_rows, start=2):  # 第 2 行起（跳过表头）
        try:
            record = adapter.normalize(row)
        except (KeyError, ValueError) as exc:
            errors.append({"row": idx, "message": f"解析失败：{exc}"})
            continue
        row_errors = adapter.validate(record)
        if row_errors:
            errors.append({"row": idx, "message": "；".join(row_errors)})
            continue
        records.append(record)

    adapter.load(db, records)
    return {"total": len(raw_rows), "success": len(records), "errors": errors}
