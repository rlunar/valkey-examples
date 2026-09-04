# Product Catalog

This context describes the product variants persisted by the validated object
storage demonstration.

## Language

**Product**:
A purchasable catalog item with a stable identity, price, availability state,
tags, and creation time.
_Avoid_: Object, record, item

**Physical product**:
A product whose availability is represented by stock and whose fulfillment
depends on its physical weight.
_Avoid_: Shipped product, inventory object

**Digital product**:
A product delivered through a download whose size is known before purchase.
_Avoid_: Virtual product, file object
