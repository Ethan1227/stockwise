"""pytest 全局配置：测试使用临时 SQLite，避免污染 data/stockwise.db。"""
import os
import tempfile
from pathlib import Path

# 必须在导入任何 app 模块之前设置（config.py 在导入时读取环境变量）
_tmp_db = Path(tempfile.gettempdir()) / "stockwise_test.db"
# 每次运行前删除旧测试库，确保用最新 schema 重建
if _tmp_db.exists():
    _tmp_db.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.as_posix()}"
