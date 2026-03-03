"""
Test P0 Bugs for CrossCurrent Finance Center
- PROB-1: Login persistence (Auth/Me endpoint)
- DM-1: Add new debt functionality
- PPL-1: Add new goal functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://community-hub-549.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@crosscurrent.com"
TEST_PASSWORD = "admin123"


class TestAuthPersistence:
    """Test PROB-1: Login persistence - Auth/Me endpoint should return user data with valid token"""
    
    def test_login_returns_token_and_user(self):
        """Test that login returns access_token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify token is returned
        assert "access_token" in data, "access_token not in response"
        assert isinstance(data["access_token"], str), "access_token should be string"
        assert len(data["access_token"]) > 0, "access_token should not be empty"
        
        # Verify user data is returned
        assert "user" in data, "user not in response"
        assert data["user"]["email"] == TEST_EMAIL, "Email mismatch"
        assert data["user"]["role"] == "super_admin", "Role should be super_admin"
        print(f"✓ Login successful - Token received, User: {data['user']['email']}, Role: {data['user']['role']}")
    
    def test_auth_me_with_valid_token(self):
        """Test that /auth/me returns user data with valid token (persistence check)"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]
        
        # Now test /auth/me with the token
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert me_response.status_code == 200, f"Auth/me failed: {me_response.text}"
        user_data = me_response.json()
        
        # Verify user data
        assert user_data["email"] == TEST_EMAIL, "Email mismatch in /auth/me"
        assert user_data["role"] == "super_admin", "Role mismatch in /auth/me"
        assert "id" in user_data, "id not in user data"
        assert "full_name" in user_data, "full_name not in user data"
        print(f"✓ Auth/me successful - User persisted: {user_data['email']}")
    
    def test_auth_me_without_token_fails(self):
        """Test that /auth/me fails without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Auth/me correctly rejects requests without token")
    
    def test_auth_me_with_invalid_token_fails(self):
        """Test that /auth/me fails with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Auth/me correctly rejects invalid tokens")


class TestDebtManagement:
    """Test DM-1: Add new debt functionality"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_debt(self, auth_headers):
        """Test creating a new debt via POST /api/debt"""
        unique_name = f"TEST_Debt_{uuid.uuid4().hex[:8]}"
        debt_data = {
            "name": unique_name,
            "total_amount": 1000.00,
            "minimum_payment": 50.00,
            "due_day": 15,
            "interest_rate": 5.5,
            "currency": "USD"
        }
        
        response = requests.post(f"{BASE_URL}/api/debt", json=debt_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Create debt failed: {response.text}"
        data = response.json()
        
        # Verify debt data
        assert data["name"] == unique_name, "Name mismatch"
        assert data["total_amount"] == 1000.00, "Total amount mismatch"
        assert data["remaining_amount"] == 1000.00, "Remaining amount should equal total"
        assert data["minimum_payment"] == 50.00, "Minimum payment mismatch"
        assert data["due_day"] == 15, "Due day mismatch"
        assert data["interest_rate"] == 5.5, "Interest rate mismatch"
        assert data["currency"] == "USD", "Currency mismatch"
        assert "id" in data, "id not in response"
        print(f"✓ Debt created successfully: {data['name']} - ${data['total_amount']}")
        
        return data["id"]
    
    def test_get_debts_after_create(self, auth_headers):
        """Test that created debt appears in GET /api/debt"""
        # First create a debt
        unique_name = f"TEST_GetDebt_{uuid.uuid4().hex[:8]}"
        debt_data = {
            "name": unique_name,
            "total_amount": 500.00,
            "minimum_payment": 25.00,
            "due_day": 20,
            "interest_rate": 3.0,
            "currency": "USD"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/debt", json=debt_data, headers=auth_headers)
        assert create_response.status_code == 200, f"Create debt failed: {create_response.text}"
        created_id = create_response.json()["id"]
        
        # Now get all debts
        get_response = requests.get(f"{BASE_URL}/api/debt", headers=auth_headers)
        assert get_response.status_code == 200, f"Get debts failed: {get_response.text}"
        
        debts = get_response.json()
        assert isinstance(debts, list), "Response should be a list"
        
        # Find our created debt
        found = False
        for debt in debts:
            if debt["id"] == created_id:
                found = True
                assert debt["name"] == unique_name, "Name mismatch in GET"
                break
        
        assert found, f"Created debt {created_id} not found in GET response"
        print(f"✓ Debt persisted and retrieved: {unique_name}")
    
    def test_create_debt_without_auth_fails(self):
        """Test that creating debt without auth fails"""
        debt_data = {
            "name": "Unauthorized Debt",
            "total_amount": 100.00,
            "minimum_payment": 10.00,
            "due_day": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/debt", json=debt_data)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Debt creation correctly requires authentication")


class TestGoalsManagement:
    """Test PPL-1: Add new goal functionality"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_goal(self, auth_headers):
        """Test creating a new goal via POST /api/goals"""
        unique_name = f"TEST_Goal_{uuid.uuid4().hex[:8]}"
        goal_data = {
            "name": unique_name,
            "target_amount": 5000.00,
            "current_amount": 500.00,
            "price_type": "fixed",
            "currency": "USD"
        }
        
        response = requests.post(f"{BASE_URL}/api/goals", json=goal_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Create goal failed: {response.text}"
        data = response.json()
        
        # Verify goal data
        assert data["name"] == unique_name, "Name mismatch"
        assert data["target_amount"] == 5000.00, "Target amount mismatch"
        assert data["current_amount"] == 500.00, "Current amount mismatch"
        assert data["price_type"] == "fixed", "Price type mismatch"
        assert data["currency"] == "USD", "Currency mismatch"
        assert "id" in data, "id not in response"
        assert "progress_percentage" in data, "progress_percentage not in response"
        assert data["progress_percentage"] == 10.0, "Progress should be 10%"
        print(f"✓ Goal created successfully: {data['name']} - ${data['target_amount']} (Progress: {data['progress_percentage']}%)")
        
        return data["id"]
    
    def test_get_goals_after_create(self, auth_headers):
        """Test that created goal appears in GET /api/goals"""
        # First create a goal
        unique_name = f"TEST_GetGoal_{uuid.uuid4().hex[:8]}"
        goal_data = {
            "name": unique_name,
            "target_amount": 2000.00,
            "current_amount": 0,
            "price_type": "fixed",
            "currency": "USD"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/goals", json=goal_data, headers=auth_headers)
        assert create_response.status_code == 200, f"Create goal failed: {create_response.text}"
        created_id = create_response.json()["id"]
        
        # Now get all goals
        get_response = requests.get(f"{BASE_URL}/api/goals", headers=auth_headers)
        assert get_response.status_code == 200, f"Get goals failed: {get_response.text}"
        
        goals = get_response.json()
        assert isinstance(goals, list), "Response should be a list"
        
        # Find our created goal
        found = False
        for goal in goals:
            if goal["id"] == created_id:
                found = True
                assert goal["name"] == unique_name, "Name mismatch in GET"
                break
        
        assert found, f"Created goal {created_id} not found in GET response"
        print(f"✓ Goal persisted and retrieved: {unique_name}")
    
    def test_create_goal_without_auth_fails(self):
        """Test that creating goal without auth fails"""
        goal_data = {
            "name": "Unauthorized Goal",
            "target_amount": 1000.00,
            "current_amount": 0,
            "price_type": "fixed"
        }
        
        response = requests.post(f"{BASE_URL}/api/goals", json=goal_data)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Goal creation correctly requires authentication")


class TestNavigationPersistence:
    """Test that navigation between pages maintains login state"""
    
    def test_multiple_api_calls_with_same_token(self):
        """Test that token works across multiple API calls (simulating navigation)"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Simulate navigation to different pages
        endpoints = [
            ("/api/auth/me", "Profile"),
            ("/api/profit/summary", "Profit Tracker"),
            ("/api/debt", "Debt Management"),
            ("/api/goals", "Profit Planner"),
            ("/api/trade/logs?limit=10", "Trade Monitor"),
        ]
        
        for endpoint, page_name in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert response.status_code == 200, f"Failed to access {page_name}: {response.status_code}"
            print(f"✓ Token valid for {page_name} ({endpoint})")
        
        print("✓ Login state maintained across all page navigations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
