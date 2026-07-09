"""
Unit tests for payments flow.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.template import Template
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentGateway, PaymentStatus


@pytest.mark.asyncio
async def test_complete_payment_flow(client: AsyncClient, db: AsyncSession):
    # 1. Seed a Category
    category = Category(name="SaaS Templates", slug="saas-templates")
    db.add(category)
    await db.flush()

    # 2. Seed a Template
    from decimal import Decimal
    template = Template(
        title="Premium SaaS Theme",
        slug="premium-saas-theme",
        short_description="Clean design for business startup",
        description="Premium SaaS Theme with animations and components.",
        price=Decimal("49.00"),
        thumbnail_url="https://picsum.photos/seed/saas/600/400",
        category_id=category.id,
        pages_count=3,
        status="published",
        download_assets={"zip": "https://storage.googleapis.com/test.zip"},
    )
    db.add(template)
    await db.flush()
    await db.commit()

    # 3. Create Order via POST /api/v1/orders
    order_payload = {
        "items": [
            {
                "template_id": str(template.id),
                "license_type": "regular"
            }
        ]
    }
    response = await client.post("/api/v1/orders", json=order_payload)
    assert response.status_code == 201
    order_data = response.json()
    assert order_data["status"] == "pending"
    order_id = order_data["id"]

    # 4. Initiate Payment session via POST /api/v1/payment/initiate
    initiate_payload = {
        "order_id": order_id,
        "gateway": "stripe"
    }
    init_res = await client.post("/api/v1/payment/initiate", json=initiate_payload)
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert "gateway_order_id" in init_data
    assert "key_id" in init_data

    # 5. Verify simulated checkout payment via POST /api/v1/payment/verify
    verify_payload = {
        "order_id": order_id,
        "gateway": "stripe",
        "gateway_payment_id": "pi_mock_testtxn123",
        "gateway_order_id": init_data["gateway_order_id"],
        "gateway_signature": "mock_sig_val",
    }
    verify_res = await client.post("/api/v1/payment/verify", json=verify_payload)
    assert verify_res.status_code == 200
    assert verify_res.json()["success"] is True

    # 6. Retrieve order to confirm it is COMPLETED now
    get_res = await client.get(f"/api/v1/orders/{order_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "completed"

    # Cleanup Database
    import uuid
    from sqlalchemy import select
    from app.models.order import Order as OrderModel
    from app.models.payment import Payment as PaymentModel
    order_obj = await db.get(OrderModel, uuid.UUID(order_id))
    if order_obj:
        pay_res = await db.execute(select(PaymentModel).where(PaymentModel.order_id == order_obj.id))
        pay_obj = pay_res.scalar_one_or_none()
        if pay_obj:
            await db.delete(pay_obj)
        await db.delete(order_obj)
    await db.delete(template)
    await db.delete(category)
    await db.commit()
