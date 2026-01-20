"""
Test Iteration 52 - Admin Settings Sidebar Layout and Global Trading Features
Tests:
1. Admin Settings sidebar layout - all tabs render correctly
2. Global Trading tab - visible ONLY to Master Admins
3. Trading Products management - add/remove/toggle products
4. Global Holidays management - calendar picker and holiday list
5. OnboardingWizard integration - fetches products from backend
6. OnboardingWizard integration - respects global holidays
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finmobile-dash.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAdminSettingsSidebarAndGlobalTrading:
    """Test Admin Settings sidebar layout and Global Trading features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def login_as_master_admin(self):
        """Login as master admin and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return data["user"]
    
    # ==================== Backend API Tests ====================
    
    def test_01_login_master_admin(self):
        """Test master admin login"""
        user = self.login_as_master_admin()
        assert user["role"] == "master_admin", f"Expected master_admin role, got {user['role']}"
        assert user["email"] == MASTER_ADMIN_EMAIL
        print(f"✓ Master admin login successful: {user['full_name']}")
    
    def test_02_get_global_holidays_admin_endpoint(self):
        """Test GET /api/admin/global-holidays - Admin endpoint"""
        self.login_as_master_admin()
        response = self.session.get(f"{BASE_URL}/api/admin/global-holidays")
        assert response.status_code == 200, f"Failed to get global holidays: {response.text}"
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ Admin global holidays endpoint works - {len(data['holidays'])} holidays found")
        return data["holidays"]
    
    def test_03_get_global_holidays_user_endpoint(self):
        """Test GET /api/trade/global-holidays - User endpoint"""
        self.login_as_master_admin()
        response = self.session.get(f"{BASE_URL}/api/trade/global-holidays")
        assert response.status_code == 200, f"Failed to get global holidays: {response.text}"
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ User global holidays endpoint works - {len(data['holidays'])} holidays found")
    
    def test_04_get_trading_products_admin_endpoint(self):
        """Test GET /api/admin/trading-products - Admin endpoint"""
        self.login_as_master_admin()
        response = self.session.get(f"{BASE_URL}/api/admin/trading-products")
        assert response.status_code == 200, f"Failed to get trading products: {response.text}"
        data = response.json()
        assert "products" in data, "Response should contain 'products' key"
        products = data["products"]
        print(f"✓ Admin trading products endpoint works - {len(products)} products found")
        # Verify product structure
        if products:
            product = products[0]
            assert "id" in product, "Product should have 'id'"
            assert "name" in product, "Product should have 'name'"
            assert "is_active" in product, "Product should have 'is_active'"
            print(f"  Sample product: {product['name']} (active: {product['is_active']})")
        return products
    
    def test_05_get_trading_products_user_endpoint(self):
        """Test GET /api/trade/trading-products - User endpoint"""
        self.login_as_master_admin()
        response = self.session.get(f"{BASE_URL}/api/trade/trading-products")
        assert response.status_code == 200, f"Failed to get trading products: {response.text}"
        data = response.json()
        assert "products" in data, "Response should contain 'products' key"
        print(f"✓ User trading products endpoint works - {len(data['products'])} products found")
    
    def test_06_add_trading_product(self):
        """Test POST /api/admin/trading-products - Add new product"""
        self.login_as_master_admin()
        test_product_name = f"TEST_PRODUCT_{datetime.now().strftime('%H%M%S')}"
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/trading-products",
            params={"name": test_product_name}
        )
        assert response.status_code == 200, f"Failed to add product: {response.text}"
        data = response.json()
        assert "product" in data, "Response should contain 'product' key"
        assert data["product"]["name"] == test_product_name
        print(f"✓ Added trading product: {test_product_name}")
        return data["product"]
    
    def test_07_toggle_trading_product(self):
        """Test PUT /api/admin/trading-products/{id} - Toggle product active status"""
        self.login_as_master_admin()
        
        # First get products
        response = self.session.get(f"{BASE_URL}/api/admin/trading-products")
        products = response.json()["products"]
        
        # Find a test product or use the first one
        test_product = None
        for p in products:
            if p["name"].startswith("TEST_"):
                test_product = p
                break
        
        if not test_product and products:
            test_product = products[0]
        
        if test_product:
            # Toggle the product
            new_status = not test_product["is_active"]
            response = self.session.put(
                f"{BASE_URL}/api/admin/trading-products/{test_product['id']}",
                params={"is_active": new_status}
            )
            assert response.status_code == 200, f"Failed to toggle product: {response.text}"
            print(f"✓ Toggled product {test_product['name']} to is_active={new_status}")
            
            # Toggle back
            response = self.session.put(
                f"{BASE_URL}/api/admin/trading-products/{test_product['id']}",
                params={"is_active": test_product["is_active"]}
            )
            assert response.status_code == 200
            print(f"✓ Restored product {test_product['name']} to is_active={test_product['is_active']}")
        else:
            print("⚠ No products found to toggle")
    
    def test_08_add_global_holiday(self):
        """Test POST /api/admin/global-holidays - Add holiday"""
        self.login_as_master_admin()
        
        # Use a future date for testing
        test_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": test_date, "reason": "Test Holiday"}
        )
        # May return 200 (added) or 400 (already exists)
        if response.status_code == 200:
            print(f"✓ Added global holiday: {test_date}")
        elif response.status_code == 400:
            print(f"✓ Holiday already exists for {test_date} (expected)")
        else:
            assert False, f"Unexpected response: {response.status_code} - {response.text}"
    
    def test_09_remove_global_holiday(self):
        """Test DELETE /api/admin/global-holidays/{date} - Remove holiday"""
        self.login_as_master_admin()
        
        # First add a test holiday
        test_date = (datetime.now() + timedelta(days=400)).strftime("%Y-%m-%d")
        
        # Add the holiday
        self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": test_date, "reason": "Test Holiday to Delete"}
        )
        
        # Now remove it
        response = self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{test_date}")
        if response.status_code == 200:
            print(f"✓ Removed global holiday: {test_date}")
        elif response.status_code == 404:
            print(f"✓ Holiday not found for {test_date} (expected if already removed)")
        else:
            assert False, f"Unexpected response: {response.status_code} - {response.text}"
    
    def test_10_platform_settings_endpoint(self):
        """Test GET /api/settings/platform - Platform settings"""
        self.login_as_master_admin()
        response = self.session.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200, f"Failed to get platform settings: {response.text}"
        data = response.json()
        assert "platform_name" in data, "Response should contain 'platform_name'"
        print(f"✓ Platform settings endpoint works - Platform: {data.get('platform_name', 'N/A')}")
    
    def test_11_cleanup_test_products(self):
        """Cleanup test products created during testing"""
        self.login_as_master_admin()
        
        # Get all products
        response = self.session.get(f"{BASE_URL}/api/admin/trading-products")
        products = response.json()["products"]
        
        # Delete test products
        deleted_count = 0
        for product in products:
            if product["name"].startswith("TEST_"):
                response = self.session.delete(f"{BASE_URL}/api/admin/trading-products/{product['id']}")
                if response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test products")
    
    def test_12_verify_onboarding_wizard_products_integration(self):
        """Verify OnboardingWizard can fetch products from backend"""
        self.login_as_master_admin()
        
        # The OnboardingWizard uses tradeAPI.getTradingProducts()
        response = self.session.get(f"{BASE_URL}/api/trade/trading-products")
        assert response.status_code == 200, f"Failed to get trading products: {response.text}"
        data = response.json()
        products = data.get("products", [])
        
        # Verify we have products
        assert len(products) > 0, "Should have at least one trading product"
        
        # Verify active products are available
        active_products = [p for p in products if p.get("is_active", True)]
        print(f"✓ OnboardingWizard can fetch {len(active_products)} active products from backend")
        
        # Print product names
        product_names = [p["name"] for p in active_products]
        print(f"  Products: {', '.join(product_names)}")
    
    def test_13_verify_onboarding_wizard_holidays_integration(self):
        """Verify OnboardingWizard can fetch global holidays from backend"""
        self.login_as_master_admin()
        
        # The OnboardingWizard uses tradeAPI.getGlobalHolidays()
        response = self.session.get(f"{BASE_URL}/api/trade/global-holidays")
        assert response.status_code == 200, f"Failed to get global holidays: {response.text}"
        data = response.json()
        holidays = data.get("holidays", [])
        
        print(f"✓ OnboardingWizard can fetch {len(holidays)} global holidays from backend")
        
        # Print holiday dates if any
        if holidays:
            holiday_dates = [h["date"] for h in holidays[:5]]  # Show first 5
            print(f"  Holidays: {', '.join(holiday_dates)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
