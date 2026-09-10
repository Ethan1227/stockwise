"""数据导入、导入日志、数据源状态路由。"""
import csv
import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.datasources  # noqa: F401  # 注册所有适配器
from app.core.db import get_db
from app.core.exceptions import BusinessError, ok
from app.datasources import registry
from app.models.import_log import ImportLog

router = APIRouter()


def _read_header(path: str) -> list[str]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        try:
            return next(csv.reader(f))
        except StopIteration:
            return []


@router.get("/import/logs")
def import_logs(db: Session = Depends(get_db)):
    logs = db.query(ImportLog).order_by(ImportLog.imported_at.desc()).limit(100).all()
    data = [
        {
            "source_code": l.source_code,
            "filename": l.filename,
            "total_rows": l.total_rows,
            "success_rows": l.success_rows,
            "error_rows": l.error_rows,
            "imported_at": l.imported_at.isoformat() if l.imported_at else None,
        }
        for l in logs
    ]
    return ok(data)


@router.get("/datasources")
def list_datasources(db: Session = Depends(get_db)):
    data = []
    for a in registry.list_adapters():
        last = (
            db.query(ImportLog)
            .filter_by(source_code=a.source_code)
            .order_by(ImportLog.imported_at.desc())
            .first()
        )
        data.append(
            {
                "source_code": a.source_code,
                "name": a.name,
                "last_sync": last.imported_at.isoformat() if last else None,
                "status": "已连接" if last else "待更新",
            }
        )
    return ok(data)


@router.post("/import/{source}")
async def import_csv(source: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传 CSV 并导入标准表（缺列 400；坏行进错误明细，成功部分入库）。"""
    adapter = registry.get(source)
    if adapter is None:
        raise BusinessError(404, f"未知数据源：{source}", http_status=404)

    # 落临时文件
    content = await file.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    try:
        tmp.write(content)
        tmp.close()

        # 表头校验：缺列直接 400
        header = _read_header(tmp.name)
        missing = [c for c in adapter.required_columns if c not in header]
        if missing:
            raise BusinessError(400, f"缺少列：{'、'.join(missing)}", http_status=400)

        result = registry.run(source, db, tmp.name)
        db.commit()

        db.add(
            ImportLog(
                source_code=source,
                filename=file.filename or "",
                total_rows=result["total"],
                success_rows=result["success"],
                error_rows=len(result["errors"]),
                error_detail={"errors": result["errors"][:50]},
                operator="system",
            )
        )
        db.commit()

        return ok(
            {
                "source": source,
                "filename": file.filename,
                "total": result["total"],
                "written": result["success"],
                "errors": result["errors"],
            }
        )
    finally:
        os.unlink(tmp.name)
