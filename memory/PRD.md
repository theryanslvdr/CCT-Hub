# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard. Features include JWT authentication with Heartbeat verification, role-based access, and API Center for external app communication.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification gatekeeper
- **Integrations**: Cloudinary (file uploads), Emailit (emails), ExchangeRate-API (currency conversion), Merin Trading Platform (embedded iframe)

## User Personas & Role Hierarchy
1. **Normal Member** (role: `member`) - Modular dashboard access assigned by Super Admin
2. **Basic Admin** (role: `basic_admin`) - Manage members, trading signals, assist with resets
3. **Super Admin** (role: `super_admin`) - Full access except hidden features (Code: `CROSSCURRENT2024`)
4. **Master Admin** (role: `master_admin`) - Full access including hidden features (Code: `CrossCurrentGODSEYE`)
5. **Extended Licensee** / **Honorary Licensee** - Special member types with custom profit calculation

## Core Requirements
- [x] Heartbeat community verification for registration
- [x] LOT Size Calculator (LOT × 15 = Exit Value)
- [x] Withdrawal fees: 3% Merin + $1 Binance, 1-2 business days processing
- [x] Live currency conversion (USDT-USD-Local currencies)
- [x] Trading signals in GMT+8 timezone

## Completed Work

### Session 28 (2026-01-11) - P1 Complete ✅

#### P1 Backend Services Package
Created modular `/app/backend/services/` package:

1. **email_service.py** - Emailit Integration ✅
   - `send_email()` - Send emails via Emailit API
   - `get_license_invite_email()` - HTML template for license invites
   - `get_admin_notification_email()` - HTML template for admin alerts
   - `get_password_reset_email()` - HTML template for password reset
   - `get_trade_alert_email()` - HTML template for trade signals

2. **file_service.py** - Cloudinary Integration ✅
   - `upload_file()` - Generic file upload
   - `upload_profile_picture()` - User profile picture upload
   - `upload_deposit_screenshot()` - Transaction screenshot upload
   - `delete_file()` - Delete from Cloudinary
   - `get_user_files()` - Get user's uploaded files

3. **websocket_service.py** - Real-time Notifications ✅
   - `ConnectionManager` - Manages WebSocket connections per user/role
   - `notify_admins_deposit_request()` - Alert admins about deposits
   - `notify_admins_withdrawal_request()` - Alert admins about withdrawals
   - `notify_user_transaction_status()` - Notify user of status changes
   - `notify_trade_signal()` - Broadcast new trade signals
   - `notify_system_announcement()` - System-wide announcements

#### New API Endpoints Added
- `POST /api/email/test` - Send test email (Master Admin only)
- `POST /api/email/send-license-invite` - Send license invite email
- `POST /api/upload/profile-picture` - Upload profile picture
- `POST /api/upload/deposit-screenshot/{transaction_id}` - Upload transaction screenshot
- `POST /api/upload/general` - General file upload
- `GET /api/ws/status` - WebSocket connection statistics (Admin only)
- `WS /ws/{user_id}` - WebSocket endpoint for real-time notifications

#### Frontend WebSocket Integration
- `WebSocketContext.jsx` - React context for WebSocket management
- Updated `Header.jsx` - Notification bell shows WS connection status
- Real-time toasts for incoming notifications

### Session 27 - P0 Complete ✅
All 6 P0 features implemented and tested (100% pass rate):
1. Dashboard Tabs for Members
2. API Key Security Modal
3. Persistent Footer
4. Login Customization
5. Production Site URL Setting
6. CrossCurrent Branding

## P1 Backend Models Package (Created)
```
/app/backend/models/
├── __init__.py - Exports all models
├── user.py - UserCreate, UserLogin, UserResponse, TokenResponse
├── trade.py - TradeLogCreate, TradingSignalCreate/Update/Response
├── common.py - DepositCreate, DebtCreate, GoalCreate, NotificationCreate
├── license.py - LicenseCreate, LicenseInviteCreate, LicenseeTransactionStatus
└── settings.py - PlatformSettings, EmailTemplateType
```

## P1 Backend Utils Package (Created)
```
/app/backend/utils/
├── __init__.py - Exports all utilities
├── auth.py - hash_password, verify_password, create_access_token, decode_token
└── calculations.py - calculate_lot_size, calculate_projected_profit, calculate_withdrawal_fees
```

## Future/Backlog (P2)
- [ ] Refactor large frontend components (AdminMembersPage, AdminLicensesPage)
- [ ] Add Tooltips to Debt Management page
- [ ] Add Alarm Music Selection for Trade Monitor
- [ ] Complete migration of routes from server.py to /routes/ package

## Test Credentials
- **Master Admin**: iam@ryansalvador.com / admin123
- **Regular Member**: jaspersalvador9413@gmail.com / test123

## API Keys (Configured in Admin Settings > Integrations)
- **Heartbeat**: For community verification
- **Emailit**: For sending notification emails
- **Cloudinary**: For file uploads and image storage

## Key Technical Notes
- **Backend:** FastAPI, Motor (async MongoDB), PyJWT, Pydantic
- **Frontend:** React, React Router, Axios, TailwindCSS, Shadcn/UI, Recharts
- **State Management:** React Context API (AuthContext, WebSocketContext)
- **Real-time:** WebSocket for notifications with auto-reconnect
- **File Uploads:** Cloudinary with base64 encoding

## Database Schema (key collections)
- **platform_settings:** Extended with login customization, footer settings, API keys
- **users:** Synced with licenses.current_amount for licensees
- **licenses:** current_amount is source of truth for licensee balance
- **file_uploads:** Stores Cloudinary file references
- **admin_notifications:** Stores notifications for admin dashboard
