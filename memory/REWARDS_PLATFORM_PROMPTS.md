# Rewards Platform Integration Prompts

These are ready-to-paste prompts for the rewards platform at `rewards.crosscur.rent` (hosted on Emergent at `trade-rewards-1.emergent.host`).

---

## PROMPT 1: JWT SSO Auto-Login (Primary Flow)

Copy and paste this prompt into Emergent for the rewards platform:

```
I need to add JWT-based SSO (Single Sign-On) auto-login for the rewards platform. The CrossCurrent Hub sends users to our platform via a signed JWT token in the URL.

## What needs to happen:

When a user visits `https://rewards.crosscur.rent/store?token=xxx`, the platform should:

1. **Read the JWT token** from the `token` URL query parameter
2. **Verify the JWT** using HS256 algorithm with the same JWT_SECRET used by the hub backend (check your .env for JWT_SECRET or SECRET_KEY)
3. **Validate claims**: issuer must be `crosscurrent-hub`, audience must be `crosscurrent-store`
4. **Extract user data** from the JWT payload:
   - `sub` = hub user ID
   - `email` = user's email
   - `name` = user's full name
   - `role` = hub role (master_admin, super_admin, admin, member)
   - `level` = rewards level
   - `points` = lifetime points
5. **Find or create the user**:
   - Search existing users by email first
   - If found: update their name and admin flags to match the hub (hub is source of truth), then log them in
   - If NOT found: create a new user account with:
     - `email` from JWT
     - `name` from JWT  
     - `is_admin` = true if role is master_admin, super_admin, admin, or basic_admin
     - `is_super_admin` = true if role is master_admin or super_admin
     - Generate a random password (user won't need it since they login via hub)
     - Auto-verify their email
   - Then log them in automatically
6. **Redirect to the store page** (or dashboard) with the user logged in via session/cookie

## Admin Role Mapping:
- Hub `master_admin` or `super_admin` → rewards `is_admin: true, is_super_admin: true`
- Hub `admin` or `basic_admin` → rewards `is_admin: true, is_super_admin: false`
- Hub `member` → rewards `is_admin: false, is_super_admin: false`

## JWT Verification Code (Python example):
```python
import jwt

JWT_SECRET = os.environ.get("JWT_SECRET")  # Must match the hub's secret

def verify_hub_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience="crosscurrent-store",
            issuer="crosscurrent-hub",
        )
        return payload  # Contains: sub, email, name, role, level, points
    except jwt.ExpiredSignatureError:
        return None  # Token expired (10-minute window)
    except jwt.InvalidTokenError:
        return None  # Invalid token
```

## Important Notes:
- The JWT has a 10-minute expiry, so verification must happen immediately on page load
- The hub's JWT_SECRET must be shared with this platform (check if it's already in your .env)
- Hub is the SOURCE OF TRUTH for user data. When syncing, always overwrite rewards platform data with hub data.
- For example, the master admin has `iam@ryansalvador.com` in the hub but `iam@theryansalvador.com` in the rewards platform. When the JWT arrives with `iam@ryansalvador.com`, if no exact email match is found, try matching by hub_user_id (the `sub` claim). If still no match, create a new account.
```

---

## PROMPT 2: POST /external/users Endpoint (Credential Sync)

Copy and paste this prompt into Emergent for the rewards platform:

```
I need to add a new API endpoint `POST /external/users` to the external API for creating and updating full user accounts. This is used by the CrossCurrent Hub to sync user credentials.

## Endpoint: POST /api/external/users

### Authentication: X-API-Key header (same as existing external endpoints)

### Request Body (JSON):
{
  "email": "user@example.com",          // Required - primary identifier
  "name": "Full Name",                  // Required
  "password": "$2b$12$hashedpassword",   // Optional - bcrypt hash from hub
  "hub_user_id": "uuid-from-hub",       // Optional - for cross-reference
  "is_admin": false,                     // Optional - admin flag
  "is_super_admin": false,               // Optional - super admin flag
  "source": "hub_sync"                   // Optional - sync source identifier
}

### Logic:
1. **Find existing user** by email (case-insensitive)
2. **If found**: Update the user with the provided fields. Hub is source of truth, so:
   - Update `name` if provided
   - Update `password` if provided (it's already a bcrypt hash, store as-is)
   - Update `is_admin` and `is_super_admin` if provided
   - Store `hub_user_id` for cross-reference
   - Set `email_verified` to true (hub users are pre-verified)
   - Return: `{"id": "existing-uuid", "message": "User updated", "action": "updated"}`
3. **If NOT found**: Create a new user with:
   - Generate a new UUID for the user
   - Set all provided fields
   - If no password provided, generate a random one (bcrypt hash)
   - Set `email_verified` to true
   - Generate a `referral_code` if your system requires one
   - Return: `{"id": "new-uuid", "message": "User created", "action": "created"}`

### Admin Role Mapping from Hub:
- The hub sends `is_admin` and `is_super_admin` booleans
- These should directly map to your user model's admin fields
- Always trust the hub's admin flags (hub is source of truth)

### Example curl:
```bash
curl -X POST "https://trade-rewards-1.emergent.host/api/external/users" \
  -H "X-API-Key: cct_izJiIkSgzqQGiqSr_VZn1icO5Fw7cjMj-zw4OW4LqW4" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "iam@ryansalvador.com",
    "name": "Ryan Salvador",
    "is_admin": true,
    "is_super_admin": true,
    "hub_user_id": "b4628e3e-9de...",
    "source": "hub_sync"
  }'
```

### Important:
- This endpoint should use the SAME permissions as the existing POST /external/members (write + admin)
- Email matching must be case-insensitive
- The password field contains a BCRYPT HASH (not plaintext) - store it directly
- Add the endpoint to the existing external API router alongside the other /external/* endpoints
```

---

## PROMPT 3: Shared JWT_SECRET Setup

If the rewards platform doesn't already have the same JWT_SECRET as the hub:

```
I need to add a JWT_SECRET environment variable to the rewards platform backend. This secret must match the CrossCurrent Hub's JWT_SECRET so that JWT tokens generated by the hub can be verified by the rewards platform.

Please add to .env:
JWT_SECRET=<the same value as the hub's JWT_SECRET>

This is used for verifying SSO tokens sent from the hub when users click "Open Rewards & Store".
```

To find the hub's JWT_SECRET, check `/app/backend/.env` on the hub platform.
