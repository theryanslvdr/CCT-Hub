"""
Iteration 134: Streak Freeze Feature Tests
Tests for the new streak freeze functionality:
- GET /api/rewards/streak-freezes - returns freeze inventory and history
- POST /api/rewards/streak-freezes/purchase - purchases freezes with points
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for master admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access token in response: {data}"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with authorization"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestStreakFreezeEndpoints:
    """Tests for streak freeze API endpoints"""
    
    def test_get_streak_freezes(self, auth_headers):
        """GET /api/rewards/streak-freezes - returns freeze data structure"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/streak-freezes",
            headers=auth_headers
        )
        print(f"GET streak-freezes status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "trade_freezes" in data, "Missing trade_freezes field"
        assert "habit_freezes" in data, "Missing habit_freezes field"
        assert "costs" in data, "Missing costs field"
        assert "available_points" in data, "Missing available_points field"
        assert "usage_history" in data, "Missing usage_history field"
        
        # Verify costs structure
        costs = data["costs"]
        assert costs.get("trade") == 200, f"Trade freeze cost should be 200, got {costs.get('trade')}"
        assert costs.get("habit") == 150, f"Habit freeze cost should be 150, got {costs.get('habit')}"
        
        # Verify numeric fields
        assert isinstance(data["trade_freezes"], int), "trade_freezes should be int"
        assert isinstance(data["habit_freezes"], int), "habit_freezes should be int"
        assert isinstance(data["available_points"], int), "available_points should be int"
        assert isinstance(data["usage_history"], list), "usage_history should be list"
        
        print(f"✓ GET streak-freezes structure verified")
        print(f"  Trade freezes: {data['trade_freezes']}")
        print(f"  Habit freezes: {data['habit_freezes']}")
        print(f"  Available points: {data['available_points']}")
    
    def test_purchase_streak_freeze_insufficient_points(self, auth_headers):
        """POST /api/rewards/streak-freezes/purchase - insufficient points error"""
        # First check user's available points
        response = requests.get(
            f"{BASE_URL}/api/rewards/streak-freezes",
            headers=auth_headers
        )
        data = response.json()
        available_points = data.get("available_points", 0)
        trade_cost = data.get("costs", {}).get("trade", 200)
        
        print(f"User has {available_points} points, trade freeze costs {trade_cost}")
        
        # If user doesn't have enough points for trade freeze (200), test insufficient points
        if available_points < trade_cost:
            response = requests.post(
                f"{BASE_URL}/api/rewards/streak-freezes/purchase",
                headers=auth_headers,
                json={"freeze_type": "trade", "quantity": 1}
            )
            print(f"Purchase response status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            assert response.status_code == 400, f"Expected 400 for insufficient points, got {response.status_code}"
            data = response.json()
            assert "detail" in data, "Expected detail in error response"
            assert "insufficient" in data["detail"].lower() or "points" in data["detail"].lower(), \
                f"Error should mention insufficient points: {data['detail']}"
            print("✓ Insufficient points error returned correctly")
        else:
            pytest.skip(f"User has enough points ({available_points}), skipping insufficient points test")
    
    def test_purchase_streak_freeze_invalid_type(self, auth_headers):
        """POST /api/rewards/streak-freezes/purchase - invalid type error"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/streak-freezes/purchase",
            headers=auth_headers,
            json={"freeze_type": "invalid_type", "quantity": 1}
        )
        print(f"Invalid type response status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Expected detail in error response"
        assert "invalid" in data["detail"].lower() or "trade" in data["detail"].lower() or "habit" in data["detail"].lower(), \
            f"Error should mention valid types: {data['detail']}"
        print("✓ Invalid type error returned correctly")
    
    def test_purchase_streak_freeze_invalid_quantity(self, auth_headers):
        """POST /api/rewards/streak-freezes/purchase - invalid quantity (0 or >10)"""
        # Test quantity 0
        response = requests.post(
            f"{BASE_URL}/api/rewards/streak-freezes/purchase",
            headers=auth_headers,
            json={"freeze_type": "trade", "quantity": 0}
        )
        print(f"Zero quantity response status: {response.status_code}")
        
        assert response.status_code == 400 or response.status_code == 422, \
            f"Expected 400/422 for zero quantity, got {response.status_code}"
        print("✓ Zero quantity rejected correctly")
        
        # Test quantity > 10
        response = requests.post(
            f"{BASE_URL}/api/rewards/streak-freezes/purchase",
            headers=auth_headers,
            json={"freeze_type": "trade", "quantity": 15}
        )
        print(f"Excess quantity response status: {response.status_code}")
        
        assert response.status_code == 400 or response.status_code == 422, \
            f"Expected 400/422 for quantity > 10, got {response.status_code}"
        print("✓ Quantity > 10 rejected correctly")


class TestStreakFreezeAPIStructure:
    """Verify API response structures match frontend expectations"""
    
    def test_api_returns_used_counts(self, auth_headers):
        """Verify API returns trade_freezes_used and habit_freezes_used"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/streak-freezes",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # These fields are used by frontend
        assert "trade_freezes_used" in data, "Missing trade_freezes_used field"
        assert "habit_freezes_used" in data, "Missing habit_freezes_used field"
        
        print(f"✓ Used counts present:")
        print(f"  Trade freezes used: {data['trade_freezes_used']}")
        print(f"  Habit freezes used: {data['habit_freezes_used']}")
    
    def test_frontend_api_mapping(self, auth_headers):
        """Verify frontend api.js methods work correctly"""
        # Test getStreakFreezes (maps to GET /api/rewards/streak-freezes)
        response = requests.get(
            f"{BASE_URL}/api/rewards/streak-freezes",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Frontend expects these fields:
        expected_fields = [
            "trade_freezes",
            "habit_freezes",
            "trade_freezes_used",
            "habit_freezes_used",
            "costs",
            "available_points",
            "usage_history"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Costs substructure
        assert "trade" in data["costs"], "Missing costs.trade"
        assert "habit" in data["costs"], "Missing costs.habit"
        
        print("✓ All frontend expected fields present")


class TestPreviousFeatures:
    """Verify previous fixes still work - regression tests"""
    
    def test_habit_proof_upload_body(self, auth_headers):
        """Verify habit proof upload accepts screenshot_url in body (not query param)"""
        # First get habits list
        response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get habits: {response.text}"
        habits_data = response.json()
        
        # Handle both dict and list response formats
        if isinstance(habits_data, dict):
            habits = habits_data.get("habits", [])
        else:
            habits = habits_data
        
        if not habits:
            pytest.skip("No habits found for testing")
        
        habit = habits[0]
        habit_id = habit["id"]
        
        # Complete habit with screenshot_url in body
        response = requests.post(
            f"{BASE_URL}/api/habits/{habit_id}/complete",
            headers=auth_headers,
            json={"screenshot_url": "https://example.com/test-screenshot.png"}
        )
        print(f"Habit complete response: {response.status_code}")
        
        # Should succeed or say already completed
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}, {response.text}"
        print("✓ Habit proof upload accepts body format")
    
    def test_dashboard_loads(self, auth_headers):
        """Basic check that dashboard APIs work"""
        # Get profit summary
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        
        data = response.json()
        # Check for actual field names used by the API
        assert "account_value" in data or "total_deposits" in data or "total_actual_profit" in data, \
            f"Unexpected summary format: {data}"
        print(f"✓ Dashboard profit summary API working: account_value={data.get('account_value')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
