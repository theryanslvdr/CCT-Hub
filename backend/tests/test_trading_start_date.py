"""
Test trading_start_date and trading_type fields in /api/auth/me endpoint
These fields are used to filter past dates for users who reset as "new trader"
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTradingStartDateFields:
    """Test that /api/auth/me returns trading_start_date and trading_type fields"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_login_returns_trading_fields(self):
        """Test that login response includes trading_start_date and trading_type"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        
        data = response.json()
        user = data.get("user", {})
        
        # Verify trading_start_date field exists in response
        assert "trading_start_date" in user, "trading_start_date field missing from login response"
        
        # Verify trading_type field exists in response
        assert "trading_type" in user, "trading_type field missing from login response"
        
        print(f"Login response - trading_start_date: {user.get('trading_start_date')}")
        print(f"Login response - trading_type: {user.get('trading_type')}")
    
    def test_auth_me_returns_trading_fields(self, auth_token):
        """Test that /api/auth/me returns trading_start_date and trading_type"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify trading_start_date field exists
        assert "trading_start_date" in data, "trading_start_date field missing from /auth/me response"
        
        # Verify trading_type field exists
        assert "trading_type" in data, "trading_type field missing from /auth/me response"
        
        print(f"/auth/me response - trading_start_date: {data.get('trading_start_date')}")
        print(f"/auth/me response - trading_type: {data.get('trading_type')}")
    
    def test_experienced_user_has_correct_trading_type(self, auth_token):
        """Test that experienced user has trading_type='experienced'"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        trading_type = data.get("trading_type")
        
        # Master Admin is set as 'experienced' so they see all their history
        assert trading_type == "experienced", f"Expected 'experienced', got '{trading_type}'"
        print(f"User trading_type is correctly set to: {trading_type}")
    
    def test_trading_start_date_format(self, auth_token):
        """Test that trading_start_date is in valid ISO format when set"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        trading_start_date = data.get("trading_start_date")
        
        if trading_start_date:
            # Should be in ISO format (YYYY-MM-DD or full ISO datetime)
            assert len(trading_start_date) >= 10, f"Invalid date format: {trading_start_date}"
            # Check it starts with a valid year
            year = trading_start_date[:4]
            assert year.isdigit(), f"Invalid year in date: {trading_start_date}"
            print(f"trading_start_date format is valid: {trading_start_date}")
        else:
            print("trading_start_date is null (user may not have reset)")


class TestUserResponseModel:
    """Test UserResponse model includes trading fields"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    def test_user_response_schema(self, auth_token):
        """Test that user response has all expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields from UserResponse model
        expected_fields = [
            "id", "email", "full_name", "role", "created_at",
            "profile_picture", "lot_size", "timezone",
            "allowed_dashboards", "license_type",
            "trading_start_date", "trading_type"  # New fields
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"All expected fields present in UserResponse")
        print(f"Fields: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
