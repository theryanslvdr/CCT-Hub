# CrossCurrent Hub - Changelog

## 2026-03-06 - Major Refactoring Release

### Backend Refactoring
- **server.py**: Reduced from 10,302 lines to 352 lines (97% reduction)
- Extracted routes into 5 modular files:
  - `routes/auth_routes.py` (705 lines) - Authentication endpoints
  - `routes/profit_routes.py` (2,241 lines) - Profit/financial endpoints
  - `routes/trade_routes.py` (1,246 lines) - Trade monitoring endpoints
  - `routes/admin_routes.py` (4,510 lines) - Admin management endpoints
  - `routes/general_routes.py` (472 lines) - General API endpoints
- Updated `helpers.py` with all shared functions (notifications, calculations, scheduler tasks)
- Updated `routes/__init__.py` with new module registry
- Removed old route stubs (auth.py, profit.py, trade.py, admin.py)
- All 27 backend endpoints verified working (100% pass rate)

### Frontend Refactoring
- **ProfitTrackerPage.jsx**: Reduced from 5,452 lines to 4,450 lines (18% reduction)
- Extracted pure utility functions to `utils/profitCalculations.js` (612 lines)
  - Formatting: truncateTo2Decimals, formatFullCurrency, formatLargeNumber, formatCompact, maskAmount
  - Trading: isTradingDay, isHoliday, addBusinessDays
  - Projections: generateProjectionData, generateDailyProjectionForMonth, generateMonthlyProjection, groupMonthsByYear
- Extracted `components/profit/DailyProjectionDialog.jsx` (416 lines)
  - Monthly projection table with trade status, P/L diff, commission tracking
  - Manager traded toggle for licensees
  - Holiday handling

### Testing
- Full regression test passed (27/27 backend, all frontend pages verified)
- Test report: `/app/test_reports/iteration_144.json`

## 2026-03-05 - Feature Batch Release

### Completed Features
- Fixed critical balance calculation bug (double-counting in server.py)
- Forum enhancements (CRUD, categories, pinning, @mentions)
- Admin transaction correction/deletion UI
- Member self-edit widget for recent transactions (48-hour window, last 2 transactions)
- Trade history streak calculation fix (non-trading days)
- Balance Audit Trail modal
- Real-time notification enhancements (forum replies, mentions)
- Admin Transactions page: Profits filter, user search
- Documentation: instructionals_admin.md, instructionals_members.md
