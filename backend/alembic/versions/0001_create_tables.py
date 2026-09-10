"""create all tables

Revision ID: 0001
Revises:
Create Date: 2026-09-10

初始迁移：一次性建齐 9 张业务表（以 Base.metadata 为准）。
"""
from alembic import op

import app.models  # noqa: F401  # 注册全部模型
from app.core.db import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
