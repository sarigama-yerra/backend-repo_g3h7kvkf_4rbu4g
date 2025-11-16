"""
Database Schemas for Lapiòzo Fashion

Each Pydantic model represents a collection in MongoDB. The collection name
is the lowercase class name (e.g., Product -> "product").
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Image(BaseModel):
    url: str = Field(..., description="Public image URL")
    alt: Optional[str] = Field(None, description="Alt text for accessibility")


class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    brand: str = Field("Lapiòzo", description="Brand name")
    in_stock: bool = Field(True, description="Whether product is in stock")
    images: List[Image] = Field(default_factory=list, description="Gallery images")
    featured: bool = Field(False, description="Whether shown as featured")


class OrderItem(BaseModel):
    product_id: str = Field(..., description="Referenced product id")
    title: str
    price: float
    quantity: int = Field(..., ge=1)
    image: Optional[str] = None


class Customer(BaseModel):
    name: str
    email: str
    address: Optional[str] = None


class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem]
    customer: Customer
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status")

