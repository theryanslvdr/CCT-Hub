"""
Test Iteration 49 - Three New Features Testing
1. Undo Trade by Date - DELETE /api/trade/undo-by-date/{date}
2. User Holidays CRUD - GET/POST/DELETE /api/trade/holidays
3. Official Trading Signal - is_official field in POST/PUT /api/admin/signals
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

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
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestUndoTradeByDate:
    """Feature 1: Undo Trade by Date - DELETE /api/trade/undo-by-date/{date}"""
    
    def test_undo_trade_invalid_date_format(self, auth_headers):
        """Test undo trade with invalid date format returns 400"""
        response = requests.delete(
            f"{BASE_URL}/api/trade/undo-by-date/invalid-date",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid date format" in response.json().get("detail", "")
    
    def test_undo_trade_nonexistent_date(self, auth_headers):
        """Test undo trade for date with no trade returns 404"""
        # Use a date far in the past where no trade exists
        old_date = "2020-01-01"
        response = requests.delete(
            f"{BASE_URL}/api/trade/undo-by-date/{old_date}",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "No trade found" in response.json().get("detail", "")
    
    def test_undo_trade_flow(self, auth_headers):
        """Test complete undo trade flow: create trade, then undo it"""
        # Use a past date that's unlikely to have a trade
        # We'll use a date 60 days ago
        test_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        # First, try to log a missed trade for that date
        trade_response = requests.post(
            f"{BASE_URL}/api/trade/log-missed-trade",
            headers=auth_headers,
            params={
                "date": test_date,
                "actual_profit": 50.00,
                "direction": "BUY",
                "notes": "Test trade for undo"
            }
        )
        
        # If trade already exists for this date, skip this test
        if trade_response.status_code == 400 and "already exists" in trade_response.text.lower():
            pytest.skip(f"Trade already exists for {test_date} - cannot test undo flow")
        
        if trade_response.status_code == 200:
            trade_data = trade_response.json()
            trade_id = trade_data.get("trade", {}).get("id")
            
            # Now undo the trade
            undo_response = requests.delete(
                f"{BASE_URL}/api/trade/undo-by-date/{test_date}",
                headers=auth_headers
            )
            
            assert undo_response.status_code == 200
            data = undo_response.json()
            assert data.get("message") == "Trade undone successfully"
            assert data.get("trade_date") == test_date
            # The trade_id should match what we created
            assert data.get("trade_id") == trade_id
        else:
            # If we couldn't create a trade, just verify the endpoint works
            pytest.skip(f"Could not create test trade: {trade_response.status_code} - {trade_response.text}")


class TestUserHolidays:
    """Feature 2: User Holidays CRUD - GET/POST/DELETE /api/trade/holidays"""
    
    def test_get_holidays_empty(self, auth_headers):
        """Test getting holidays returns list (may be empty)"""
        response = requests.get(
            f"{BASE_URL}/api/trade/holidays",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "holidays" in data
        assert isinstance(data["holidays"], list)
    
    def test_add_holiday_invalid_date(self, auth_headers):
        """Test adding holiday with invalid date format returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/trade/holidays",
            headers=auth_headers,
            params={"date": "invalid-date", "reason": "Test"}
        )
        assert response.status_code == 400
        assert "Invalid date format" in response.json().get("detail", "")
    
    def test_add_holiday_success(self, auth_headers):
        """Test adding a holiday successfully"""
        # Use a future date to avoid conflicts with existing trades
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # First, try to remove if it exists (cleanup from previous test)
        requests.delete(
            f"{BASE_URL}/api/trade/holidays/{future_date}",
            headers=auth_headers
        )
        
        # Add the holiday
        response = requests.post(
            f"{BASE_URL}/api/trade/holidays",
            headers=auth_headers,
            params={"date": future_date, "reason": "Test holiday"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Holiday marked successfully"
        assert "holiday" in data
        assert data["holiday"]["date"] == future_date
        assert data["holiday"]["reason"] == "Test holiday"
    
    def test_add_duplicate_holiday(self, auth_headers):
        """Test adding duplicate holiday returns 400"""
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Try to add the same holiday again
        response = requests.post(
            f"{BASE_URL}/api/trade/holidays",
            headers=auth_headers,
            params={"date": future_date, "reason": "Duplicate test"}
        )
        
        assert response.status_code == 400
        assert "already marked as a holiday" in response.json().get("detail", "")
    
    def test_get_holidays_after_add(self, auth_headers):
        """Test getting holidays includes the added holiday"""
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/trade/holidays",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        holidays = data.get("holidays", [])
        
        # Check if our holiday is in the list
        holiday_dates = [h.get("date") for h in holidays]
        assert future_date in holiday_dates
    
    def test_remove_holiday_success(self, auth_headers):
        """Test removing a holiday successfully"""
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.delete(
            f"{BASE_URL}/api/trade/holidays/{future_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("message") == "Holiday removed successfully"
        assert data.get("date") == future_date
    
    def test_remove_nonexistent_holiday(self, auth_headers):
        """Test removing non-existent holiday returns 404"""
        old_date = "2020-01-01"
        
        response = requests.delete(
            f"{BASE_URL}/api/trade/holidays/{old_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Holiday not found" in response.json().get("detail", "")


class TestOfficialTradingSignal:
    """Feature 3: Official Trading Signal - is_official field in signals"""
    
    def test_create_signal_with_is_official_true(self, auth_headers):
        """Test creating a signal with is_official=true"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers,
            json={
                "product": "MOIL10",
                "trade_time": "12:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "notes": "Test official signal",
                "is_official": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_official") == True
        assert data.get("product") == "MOIL10"
        assert data.get("direction") == "BUY"
        
        # Store signal ID for cleanup
        return data.get("id")
    
    def test_create_signal_with_is_official_false(self, auth_headers):
        """Test creating a signal with is_official=false (default)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers,
            json={
                "product": "MOIL10",
                "trade_time": "14:00",
                "trade_timezone": "Asia/Manila",
                "direction": "SELL",
                "profit_points": 15,
                "notes": "Test non-official signal",
                "is_official": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_official") == False
        
        return data.get("id")
    
    def test_create_signal_without_is_official(self, auth_headers):
        """Test creating a signal without is_official defaults to false"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers,
            json={
                "product": "MOIL10",
                "trade_time": "16:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "notes": "Test signal without is_official"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Default should be False
        assert data.get("is_official") == False
        
        return data.get("id")
    
    def test_update_signal_is_official(self, auth_headers):
        """Test updating a signal's is_official field"""
        # First create a signal
        create_response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers,
            json={
                "product": "MOIL10",
                "trade_time": "18:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "is_official": False
            }
        )
        
        assert create_response.status_code == 200
        signal_id = create_response.json().get("id")
        
        # Update is_official to True
        update_response = requests.put(
            f"{BASE_URL}/api/admin/signals/{signal_id}",
            headers=auth_headers,
            json={
                "is_official": True
            }
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data.get("is_official") == True
        
        # Update is_official back to False
        update_response2 = requests.put(
            f"{BASE_URL}/api/admin/signals/{signal_id}",
            headers=auth_headers,
            json={
                "is_official": False
            }
        )
        
        assert update_response2.status_code == 200
        data2 = update_response2.json()
        assert data2.get("is_official") == False
    
    def test_get_active_signal_includes_is_official(self, auth_headers):
        """Test that active signal response includes is_official field"""
        # Create an official signal first
        requests.post(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers,
            json={
                "product": "MOIL10",
                "trade_time": "20:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "is_official": True
            }
        )
        
        # Get active signal
        response = requests.get(
            f"{BASE_URL}/api/trade/active-signal",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data.get("signal"):
            signal = data["signal"]
            # is_official should be present in the response
            assert "is_official" in signal
            assert signal.get("is_official") == True


class TestEndpointAuthentication:
    """Test that endpoints require authentication"""
    
    def test_undo_trade_requires_auth(self):
        """Test undo trade endpoint requires authentication"""
        response = requests.delete(
            f"{BASE_URL}/api/trade/undo-by-date/2024-01-01"
        )
        assert response.status_code in [401, 403]
    
    def test_holidays_get_requires_auth(self):
        """Test get holidays endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trade/holidays")
        assert response.status_code in [401, 403]
    
    def test_holidays_post_requires_auth(self):
        """Test add holiday endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/trade/holidays",
            params={"date": "2024-01-01", "reason": "Test"}
        )
        assert response.status_code in [401, 403]
    
    def test_holidays_delete_requires_auth(self):
        """Test remove holiday endpoint requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/trade/holidays/2024-01-01")
        assert response.status_code in [401, 403]
    
    def test_create_signal_requires_auth(self):
        """Test create signal endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            json={
                "product": "MOIL10",
                "trade_time": "12:00",
                "direction": "BUY"
            }
        )
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
