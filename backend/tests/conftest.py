"""pytest 全局配置：测试使用唯一临时 SQLite，避免污染 data/stockwise.db 及跨运行残留。"""
import os
import tempfile

# 唯一临时库（每次运行独立，避免 Windows 文件锁导致的跨运行残留）
# 必须在导入任何 app 模块之前设置（config.py 在导入时读取环境变量）
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
