"""
Tests for restocking order API endpoints.
"""
import pytest


def make_item(sku="SRV-301", name="Micro Servo Motor", quantity=5, unit_cost=445.0, lead_time_days=14):
    return {
        "sku": sku,
        "name": name,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "lead_time_days": lead_time_days,
    }


class TestRestockingOrderEndpoints:
    """Test suite for restocking-order-related endpoints."""

    def test_get_restocking_orders_returns_list(self, client):
        """Test that GET restocking orders always returns a list."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_restocking_order_happy_path(self, client):
        """Test submitting a valid restocking order."""
        item = make_item(quantity=10, unit_cost=445.0, lead_time_days=14)
        payload = {"budget": 5000, "items": [item]}

        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["status"] == "Submitted"
        assert data["total_cost"] == 4450.0
        assert data["budget"] == 5000
        assert len(data["items"]) == 1
        assert data["items"][0]["line_total"] == 4450.0

        # expected_delivery should be created_date + max lead_time_days across items
        from datetime import datetime
        created = datetime.fromisoformat(data["created_date"])
        expected = datetime.fromisoformat(data["expected_delivery"])
        assert (expected - created).days == 14

    def test_create_restocking_order_multiple_items_uses_max_lead_time(self, client):
        """Test that expected_delivery uses the longest lead time among items."""
        items = [
            make_item(sku="SRV-301", quantity=1, unit_cost=445.0, lead_time_days=14),
            make_item(sku="STP-303", quantity=1, unit_cost=325.0, lead_time_days=21),
        ]
        payload = {"budget": 10000, "items": items}

        response = client.post("/api/restocking-orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        from datetime import datetime
        created = datetime.fromisoformat(data["created_date"])
        expected = datetime.fromisoformat(data["expected_delivery"])
        assert (expected - created).days == 21

    def test_create_restocking_order_appears_in_get(self, client):
        """Test that a submitted order shows up in the GET list."""
        payload = {"budget": 5000, "items": [make_item(quantity=1)]}
        create_response = client.post("/api/restocking-orders", json=payload)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        list_response = client.get("/api/restocking-orders")
        assert list_response.status_code == 200
        ids = [o["id"] for o in list_response.json()]
        assert created_id in ids

    def test_create_restocking_order_empty_items(self, client):
        """Test that submitting with no items is rejected."""
        response = client.post("/api/restocking-orders", json={"budget": 5000, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_create_restocking_order_zero_budget(self, client):
        """Test that submitting with a zero or negative budget is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 0, "items": [make_item(quantity=1)]}
        )
        assert response.status_code == 400

    def test_create_restocking_order_negative_budget(self, client):
        """Test that a negative budget is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": -100, "items": [make_item(quantity=1)]}
        )
        assert response.status_code == 400

    def test_create_restocking_order_exceeds_budget(self, client):
        """Test that an order whose line total exceeds the budget is rejected."""
        item = make_item(quantity=100, unit_cost=445.0)  # $44,500
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 1000, "items": [item]}
        )
        assert response.status_code == 400

    def test_create_restocking_order_invalid_quantity(self, client):
        """Test that a non-positive item quantity is rejected."""
        item = make_item(quantity=0)
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 5000, "items": [item]}
        )
        assert response.status_code == 400


class TestInventoryLeadTime:
    """Test suite verifying inventory records carry lead_time_days."""

    def test_inventory_items_have_lead_time_days(self, client):
        """Test that every inventory item includes a positive lead_time_days field."""
        response = client.get("/api/inventory")
        data = response.json()
        assert len(data) > 0

        for item in data:
            assert "lead_time_days" in item
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0
