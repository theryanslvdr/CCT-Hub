"""
Iteration 180: Trade Log Fix & Admin Member Update Testing
Tests:
1. POST /api/trade/log WITHOUT lot_size field succeeds (critical fix)
2. POST /api/trade/log WITH lot_size field still works (backward compatibility)
3. POST /api/trade/log returns correct response structure
4. PUT /api/admin/members/{id} with merin_referral_code updates correctly
5. PUT /api/admin/members/{id} with referred_by_user_id updates correctly
6. PUT /api/admin/members/{id} with BOTH fields in same request
7. PUT /api/admin/members/{id} with referred_by_user_id='' clears inviter
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

# Test member IDs provided
TEST_MEMBER_JJ_ID = "07062f66-d9ea-49ba-8fed-86ac6628b4e8"
TEST_MEMBER_RYAN_ID = "a9566813-3880-47c5-8703-7fa22fdb601d"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for requests"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestHealthCheck:
    """Basic health check"""
    
    def test_server_health(self):
        """Verify server is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Server health check PASSED")


class TestTradeLogCriticalFix:
    """Test the critical trade log fix - lot_size is now Optional"""
    
    def test_trade_log_without_lot_size(self, auth_headers):
        """CRITICAL: POST /api/trade/log WITHOUT lot_size field should succeed"""
        # This was the bug - lot_size was required but frontend doesn't send it
        payload = {
            "direction": "BUY",
            "actual_profit": 15.50,
            "commission": 0,
            "notes": "TEST_trade_without_lot_size_iteration_180"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/trade/log",
            json=payload,
            headers=auth_headers
        )
        
        # Should NOT get 422 validation error anymore
        assert response.status_code != 422, f"Still getting 422 validation error - fix not applied! Response: {response.text}"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain trade id"
        assert "lot_size" in data, "Response should contain calculated lot_size"
        assert data["lot_size"] > 0, "lot_size should be calculated by server"
        assert data["actual_profit"] == 15.50, "actual_profit should match input"
        
        print(f"CRITICAL FIX VERIFIED: Trade logged without lot_size - id={data['id']}, server calculated lot_size={data['lot_size']}")
        return data
    
    def test_trade_log_with_lot_size_backward_compat(self, auth_headers):
        """POST /api/trade/log WITH lot_size should still work (backward compatibility)"""
        payload = {
            "lot_size": 0.5,  # Frontend sends this in some cases
            "direction": "SELL",
            "actual_profit": 12.00,
            "commission": 0.5,
            "notes": "TEST_trade_with_lot_size_iteration_180"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/trade/log",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Trade with lot_size failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        # Server recalculates lot_size from account_value, so it may differ from input
        assert "lot_size" in data
        print(f"Backward compat PASSED: Trade with lot_size - id={data['id']}, final lot_size={data['lot_size']}")
        return data
    
    def test_trade_log_response_structure(self, auth_headers):
        """POST /api/trade/log returns correct response with all required fields"""
        payload = {
            "direction": "BUY",
            "actual_profit": 10.00,
            "commission": 1.00,
            "notes": "TEST_response_structure_iteration_180"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/trade/log",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields in TradeLogResponse
        required_fields = ["id", "user_id", "lot_size", "direction", "projected_profit", 
                          "actual_profit", "profit_difference", "performance", "created_at"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify performance calculation
        assert data["performance"] in ["perfect", "exceeded", "below"], f"Invalid performance: {data['performance']}"
        
        print(f"Response structure PASSED: Contains all required fields, performance={data['performance']}")
        return data


class TestAdminMemberUpdate:
    """Test admin member update with referral fields"""
    
    def test_update_merin_referral_code(self, auth_headers):
        """PUT /api/admin/members/{id} with merin_referral_code updates correctly"""
        # Generate a unique test code
        test_code = f"TEST{uuid.uuid4().hex[:4].upper()}"
        
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            json={"merin_referral_code": test_code},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify the update by fetching member details
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        member_data = verify_response.json()
        assert member_data["user"]["merin_referral_code"] == test_code, "merin_referral_code not updated"
        
        print(f"merin_referral_code update PASSED: Set to {test_code}")
    
    def test_update_referred_by_user_id(self, auth_headers):
        """PUT /api/admin/members/{id} with referred_by_user_id updates correctly"""
        # Set TEST_MEMBER_RYAN as the inviter for TEST_MEMBER_JJ
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            json={"referred_by_user_id": TEST_MEMBER_RYAN_ID},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify the update
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        member_data = verify_response.json()
        
        # Should have both referred_by_user_id and resolved referred_by
        user = member_data["user"]
        assert user.get("referred_by_user_id") == TEST_MEMBER_RYAN_ID, "referred_by_user_id not set"
        assert user.get("referred_by") is not None, "referred_by should be resolved from inviter"
        
        print(f"referred_by_user_id update PASSED: Set to {TEST_MEMBER_RYAN_ID}, referred_by={user.get('referred_by')}")
    
    def test_update_both_fields_same_request(self, auth_headers):
        """PUT /api/admin/members/{id} with BOTH merin_referral_code AND referred_by_user_id"""
        test_code = f"BOTH{uuid.uuid4().hex[:4].upper()}"
        
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            json={
                "merin_referral_code": test_code,
                "referred_by_user_id": TEST_MEMBER_RYAN_ID
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify both fields
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        user = verify_response.json()["user"]
        
        assert user["merin_referral_code"] == test_code, "merin_referral_code not updated"
        assert user.get("referred_by_user_id") == TEST_MEMBER_RYAN_ID, "referred_by_user_id not updated"
        
        print(f"Both fields update PASSED: merin_code={test_code}, inviter={TEST_MEMBER_RYAN_ID}")
    
    def test_clear_inviter_with_empty_string(self, auth_headers):
        """PUT /api/admin/members/{id} with referred_by_user_id='' clears the inviter"""
        # First ensure there's an inviter set
        requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            json={"referred_by_user_id": TEST_MEMBER_RYAN_ID},
            headers=auth_headers
        )
        
        # Now clear it with empty string
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            json={"referred_by_user_id": ""},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Clear inviter failed: {response.text}"
        
        # Verify inviter is cleared
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_JJ_ID}",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        user = verify_response.json()["user"]
        
        # Both fields should be None or empty
        assert user.get("referred_by") is None, f"referred_by should be cleared, got: {user.get('referred_by')}"
        assert user.get("referred_by_user_id") is None, f"referred_by_user_id should be cleared, got: {user.get('referred_by_user_id')}"
        
        print("Clear inviter PASSED: Both referred_by and referred_by_user_id are None")


class TestCleanup:
    """Cleanup test trades created during testing"""
    
    def test_cleanup_test_trades(self, auth_headers):
        """Delete test trades created during testing"""
        # Get recent trades to find test trades
        response = requests.get(
            f"{BASE_URL}/api/trade/logs?limit=20",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            trades = response.json()
            test_trades = [t for t in trades if "TEST_" in (t.get("notes") or "") and "iteration_180" in (t.get("notes") or "")]
            
            # Note: Would need master_admin to delete trades, so just report
            print(f"Found {len(test_trades)} test trades to clean up (requires master_admin to delete)")
        
        # This test always passes - cleanup is informational
        assert True
