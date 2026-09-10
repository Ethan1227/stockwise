"""商品档案（sku_master）CRUD 路由。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import BusinessError, ok
from app.models.sku_master import SkuMaster
from app.schemas.sku import SkuCreate, SkuUpdate

router = APIRouter()


def _serialize(sku: SkuMaster) -> dict:
    return {
        "sku": sku.sku,
        "name": sku.name,
        "platform": sku.platform,
        "category": sku.category,
        "supplier": sku.supplier,
        "unit_cost": sku.unit_cost,
        "price": sku.price,
        "moq": sku.moq,
        "lead_prod_days": sku.lead_prod_days,
        "lead_ship_days": sku.lead_ship_days,
        "safety_days": sku.safety_days,
    }


@router.get("/skus")
def list_skus(db: Session = Depends(get_db)):
    skus = db.query(SkuMaster).order_by(SkuMaster.sku).all()
    return ok([_serialize(s) for s in skus])


@router.post("/skus")
def create_sku(body: SkuCreate, db: Session = Depends(get_db)):
    if db.get(SkuMaster, body.sku):
        raise BusinessError(400, f"SKU {body.sku} 已存在", http_status=400)
    sku = SkuMaster(**body.model_dump())
    db.add(sku)
    db.commit()
    return ok(_serialize(sku))


@router.put("/skus/{sku_code}")
def update_sku(sku_code: str, body: SkuUpdate, db: Session = Depends(get_db)):
    sku = db.get(SkuMaster, sku_code)
    if sku is None:
        raise BusinessError(404, f"SKU {sku_code} 不存在", http_status=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(sku, k, v)
    db.commit()
    return ok(_serialize(sku))


@router.delete("/skus/{sku_code}")
def delete_sku(sku_code: str, db: Session = Depends(get_db)):
    sku = db.get(SkuMaster, sku_code)
    if sku is None:
        raise BusinessError(404, f"SKU {sku_code} 不存在", http_status=404)
    db.delete(sku)
    db.commit()
    return ok({"sku": sku_code, "deleted": True})
