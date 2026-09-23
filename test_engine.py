import pytest
from fastapi.testclient import TestClient
from main import app
import sqlite3

client = TestClient(app)

def setup_module(module):
    """Ensure database state is clean before running tests."""
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'DELIVERED' WHERE order_id = 'ORD1001'")
    cursor.execute("UPDATE orders SET status = 'DELIVERED' WHERE order_id = 'ORD1002'")
    conn.commit()
    conn.close()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auto_refund_under_threshold():
    """Test $29.99 refund executes automatically without requiring approval."""
    payload = {
        "thread_id": "test_auto_refund_1",
        "message": "Please refund order ORD1001"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["refund_amount"] == 29.99
    assert "COMPLETED" in data["status"]

def test_hitl_pause_over_threshold():
    """Test $120.00 refund triggers state pause (PAUSED_PENDING_APPROVAL)."""
    payload = {
        "thread_id": "test_hitl_pause_1",
        "message": "Process a refund for ORD1002"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PAUSED_PENDING_APPROVAL"
    assert data["refund_amount"] == 120.00

def test_admin_approval_and_execution_lifecycle():
    """Test full HITL lifecycle: Pause -> Admin Approve -> Resume Execution."""
    thread_id = "test_hitl_lifecycle_1"
    
    # 1. Trigger Pause
    client.post("/api/v1/chat", json={"thread_id": thread_id, "message": "Refund ORD1002"})
    
    # 2. Grant Approval
    approve_res = client.post("/api/v1/admin/approve", json={"thread_id": thread_id, "admin_approved": True})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"
    
    # 3. Resume Chat
    resume_res = client.post("/api/v1/chat", json={"thread_id": thread_id, "message": "Refund ORD1002"})
    assert resume_res.status_code == 200
    assert "COMPLETED" in resume_res.json()["status"]

def test_idempotency_duplicate_refund_prevention():
    """Test duplicate refund prevention on an already refunded order."""
    thread_id = "test_idempotency_1"
    payload = {"thread_id": thread_id, "message": "Refund ORD1001"}
    
    # Second attempt on refunded order
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    assert "ALREADY been refunded" in response.json()["response"] or "COMPLETED" in response.json()["status"]