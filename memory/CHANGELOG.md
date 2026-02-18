# CrossCurrent Hub - Changelog

## Feb 18, 2026
### P0 Fix: Profit Tracker Data Consistency for Direct Licensee Login
- Fixed `/api/profit/licensee/welcome-info` to use `calculate_honorary_licensee_value()` instead of stale `license.current_amount`
- Verified all 4 key endpoints return identical dynamically calculated values for honorary licensees
- Backend test: 10/10 passed (iteration_114)

### Admin Temp Password with Forced Reset on First Login
- Modified login endpoint to return `must_change_password` flag (removed `response_model=TokenResponse`)
- Added `POST /api/auth/force-change-password` endpoint
- Added force change password dialog in `LoginPage.jsx`
- Fixed redirect race condition: dialog now renders before dashboard redirect
- Frontend verified: dialog appears correctly for temp password users

## Feb 17, 2026
### Family Account Feature (End-to-End)
- Created `honorary_fa` license type with family member CRUD
- Built all APIs for admin conversion, member management, withdrawal approvals
- Frontend: FamilyAccountsPage.jsx for licensees, admin dashboard integration

### Admin Reset Functionality
- Reset starting balance, trade start date, and family member reset endpoints
- All resets immediately reflected in dynamic projections

### Profit Tracker Logic Refactor (Partial)
- Dynamic `calculate_honorary_licensee_value()` with quarterly compounding
- Applied to admin simulation and member details endpoints
