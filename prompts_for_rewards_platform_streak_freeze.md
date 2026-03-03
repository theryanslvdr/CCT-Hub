# Prompt for Rewards Platform — Add Streak Freeze Store Items

## Context
The main Hub application (`hub.crosscur.rent`) has been updated to support **Streak Freezes** — a feature where users can spend reward points to protect their trade streaks and daily habit streaks when they miss a day. 

The Hub already has:
- `GET /api/rewards/streak-freezes` — returns user's available freezes, usage history, and costs
- `POST /api/rewards/streak-freezes/purchase` — deducts points from the user's reward balance and adds freezes to their inventory
- Automatic streak freeze consumption: when a streak calculation detects a missed trading day, it checks the `streak_freeze_usage` collection for an existing freeze on that date

The Rewards Platform needs to be updated to:
1. **Display streak freezes as purchasable items in the store**
2. **Sync streak freeze inventory when users SSO from the Hub**
3. **Allow purchases directly from the Rewards Platform store** (which then calls back to the Hub API)

---

## Task 1: Add Streak Freeze Items to the Rewards Store

### Store Display
Add two new items to the Rewards Store:

| Item | Cost (Points) | Description |
|------|--------------|-------------|
| Trade Streak Freeze | 200 pts | Protects your trading streak when you miss a trading day. Automatically used when a missed day is detected. |
| Habit Streak Freeze | 150 pts | Protects your daily habit streak when you miss a trading day. Automatically used when a missed day is detected. |

### UI Requirements
- Display these as purchasable cards in the store alongside existing items
- Show an ice/snowflake icon (❄️ or Snowflake from lucide-react)
- Show current inventory count for each type (how many the user has available)
- Allow quantity selection (1-10)
- Show total cost before purchase
- Disable purchase if insufficient points
- After purchase, show success toast and update inventory count

---

## Task 2: Backend API Integration

### Option A: Direct Purchase (Hub API Callback)
When a user purchases a streak freeze from the Rewards Platform store:

1. Call the Hub API to process the purchase:
```
POST https://hub.crosscur.rent/api/rewards/streak-freezes/purchase
Headers:
  Authorization: Bearer <user_jwt_token>
  Content-Type: application/json
Body:
  {
    "freeze_type": "trade" | "habit",
    "quantity": 1
  }
```

2. The Hub API will:
   - Validate the user has enough points
   - Deduct points from their balance
   - Add freezes to their inventory
   - Return the updated inventory

3. Response (200 OK):
```json
{
  "success": true,
  "purchased": 1,
  "freeze_type": "trade",
  "points_spent": 200,
  "trade_freezes": 3,
  "habit_freezes": 1
}
```

4. Error Response (400):
```json
{
  "detail": "Insufficient points. Need 200 but have 50."
}
```

### Option B: Fetch Current Inventory
To display current streak freeze inventory on the store page:

```
GET https://hub.crosscur.rent/api/rewards/streak-freezes
Headers:
  Authorization: Bearer <user_jwt_token>
```

Response:
```json
{
  "trade_freezes": 2,
  "habit_freezes": 1,
  "trade_freezes_used": 5,
  "habit_freezes_used": 3,
  "costs": {
    "trade": 200,
    "habit": 150
  },
  "available_points": 450,
  "usage_history": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "freeze_type": "trade",
      "date": "2026-02-16",
      "used_at": "2026-02-17T08:00:00+00:00"
    }
  ]
}
```

---

## Task 3: SSO Token & Inventory Sync

When users SSO from the Hub to the Rewards Platform (via the "Open Rewards & Store" button), their JWT token already contains their user identity. Use this token to:

1. Fetch their streak freeze inventory from the Hub API
2. Display the inventory count on the store page
3. Use the token for any purchase API calls

The SSO flow already works — the user arrives at the Rewards Platform with a valid JWT. Just use that token for the streak freeze API calls.

---

## Data Model Reference

### Hub Database Collections

**`streak_freezes`** (inventory per user):
```json
{
  "user_id": "uuid",
  "trade_freezes": 3,
  "habit_freezes": 1,
  "trade_freezes_used": 5,
  "habit_freezes_used": 2,
  "created_at": "2026-03-01T00:00:00+00:00",
  "updated_at": "2026-03-03T00:00:00+00:00"
}
```

**`streak_freeze_usage`** (log of consumed freezes):
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "freeze_type": "trade",
  "date": "2026-02-16",
  "used_at": "2026-02-17T08:00:00+00:00"
}
```

---

## Design Guidelines
- Match the existing Rewards Platform design language (dark theme, glass cards)
- Use the Snowflake icon from lucide-react for streak freeze items
- Trade Streak Freeze: Blue accent color (#3B82F6)
- Habit Streak Freeze: Orange accent color (#F97316)
- Show a "shield" or "protection" visual metaphor
- Include a brief explanation: "Streak freezes automatically protect your streak when you miss a trading day"

---

## Testing
After implementation:
1. SSO from Hub → Rewards Platform, verify streak freeze inventory loads
2. Attempt to purchase with insufficient points → verify error message
3. Award enough points to a test user, then purchase → verify success
4. Return to Hub → verify inventory updated
5. Test with credentials: `iam@ryansalvador.com` / `admin123`
