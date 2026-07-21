"""Product sync route for WordPress integration.

The endpoint enqueues changes into the sync_queue table and returns instantly.
A background worker processes the queue independently.
"""
from __future__ import annotations

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.dependencies import get_sync_enqueuer
from src.api.middleware import require_jwt
from src.domain.sync import SyncEnqueuer

router = APIRouter(prefix="/sync", tags=["sync"])
logger = structlog.get_logger("ramon.sync")


class ProductChange(BaseModel):
    """A single product change (upsert or delete)."""

    action: str = Field(..., pattern="^(upsert|delete)$")
    product_id: str = Field(..., min_length=1)
    fields: Optional[dict] = None


class SyncRequest(BaseModel):
    """Batch of product changes from WordPress."""

    changes: List[ProductChange]


class SyncResponse(BaseModel):
    """Response from the sync endpoint."""

    queued: int


@router.post("/products", response_model=SyncResponse)
async def sync_products(
    request: SyncRequest,
    enqueuer: SyncEnqueuer = Depends(get_sync_enqueuer),
    _: dict = Depends(require_jwt),
) -> SyncResponse:
    """Receive a batch of product changes from WordPress.

    Each change must have an `action` ("upsert" or "delete"), a `product_id`,
    and for upserts, a `fields` dict with the product data.

    Changes are immediately enqueued into the sync_queue table for background
    processing. The response returns the number of items queued.

    Requires a valid JWT token in the Authorization header.
    """
    if not request.changes:
        return SyncResponse(queued=0)

    changes_data = [
        {
            "action": c.action,
            "product_id": c.product_id,
            "fields": c.fields or {},
        }
        for c in request.changes
    ]

    count = await enqueuer.enqueue(changes_data)
    logger.info("sync.request.completed", count=count)
    return SyncResponse(queued=count)
