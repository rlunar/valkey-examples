"""Pydantic models for the product variants stored by the demo."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
)

ProductName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=80),
]
ProductTag = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20,
        pattern=r"^[a-z0-9-]+$",
    ),
]
ProductPrice = Annotated[
    Decimal,
    Field(gt=0, max_digits=8, decimal_places=2),
]


class ProductBase(BaseModel):
    """Fields shared by every product variant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    name: ProductName
    price: ProductPrice
    active: bool
    tags: tuple[ProductTag, ...] = Field(default=(), max_length=5)
    created_at: AwareDatetime


class PhysicalProduct(ProductBase):
    """A stocked product with a physical shipping weight."""

    kind: Literal["physical"]
    stock: int = Field(ge=0)
    weight_grams: int = Field(gt=0)


class DigitalProduct(ProductBase):
    """A downloadable product with a known file size."""

    kind: Literal["digital"]
    download_url: HttpUrl
    file_size_bytes: int = Field(gt=0)


type Product = Annotated[
    PhysicalProduct | DigitalProduct,
    Field(discriminator="kind"),
]

PRODUCT_ADAPTER: TypeAdapter[Product] = TypeAdapter(Product)
