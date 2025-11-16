import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product as ProductSchema, Order as OrderSchema

app = FastAPI(title="Lapiòzo Fashion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ProductResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    price: float
    category: str
    brand: str
    in_stock: bool
    images: list = []
    featured: bool = False


class SeedResponse(BaseModel):
    inserted: int


def serialize(doc: dict) -> dict:
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    # Convert nested ObjectIds if any
    for k, v in out.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
    return out


@app.get("/")
def read_root():
    return {"brand": "Lapiòzo", "status": "ok"}


@app.get("/api/products", response_model=List[ProductResponse])
def list_products(category: Optional[str] = None, featured: Optional[bool] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {}
    if category:
        filt["category"] = category
    if featured is not None:
        filt["featured"] = featured
    docs = get_documents("product", filt, limit)
    return [serialize(d) for d in docs]


@app.get("/api/products/featured", response_model=List[ProductResponse])
def featured_products(limit: int = 8):
    docs = get_documents("product", {"featured": True}, limit)
    return [serialize(d) for d in docs]


@app.post("/api/orders")
def create_order(order: OrderSchema):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Calculate total on backend for integrity
    total = sum(item.price * item.quantity for item in order.items)
    data = order.model_dump()
    data["total"] = round(total, 2)
    order_id = create_document("order", data)
    return {"id": order_id, "status": "received"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Optional: seed some sample products for quick start
@app.post("/api/seed", response_model=SeedResponse)
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"inserted": 0}

    samples = [
        {
            "title": "Silk Trench Coat",
            "description": "Double-breasted silk trench with mother-of-pearl buttons.",
            "price": 1890.0,
            "category": "Outerwear",
            "brand": "Lapiòzo",
            "in_stock": True,
            "images": [
                {"url": "https://images.unsplash.com/photo-1520975922284-047f014f2c2d", "alt": "Silk trench coat"}
            ],
            "featured": True,
        },
        {
            "title": "Cashmere Crewneck",
            "description": "Ultra-soft Italian cashmere sweater.",
            "price": 690.0,
            "category": "Knitwear",
            "brand": "Lapiòzo",
            "in_stock": True,
            "images": [
                {"url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b", "alt": "Cashmere sweater"}
            ],
            "featured": True,
        },
        {
            "title": "Signature Tailored Trousers",
            "description": "High-rise, tapered wool trousers.",
            "price": 520.0,
            "category": "Pants",
            "brand": "Lapiòzo",
            "in_stock": True,
            "images": [
                {"url": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f", "alt": "Tailored trousers"}
            ],
            "featured": False,
        },
        {
            "title": "Evening Silk Dress",
            "description": "Bias-cut silk charmeuse with open back.",
            "price": 2290.0,
            "category": "Dresses",
            "brand": "Lapiòzo",
            "in_stock": True,
            "images": [
                {"url": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb", "alt": "Silk dress"}
            ],
            "featured": True,
        },
    ]

    inserted = 0
    for s in samples:
        db["product"].insert_one({**s})
        inserted += 1

    return {"inserted": inserted}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
