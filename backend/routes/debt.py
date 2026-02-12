"""Debt management routes."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import List
import uuid

from deps import db, get_current_user

# Import models from server (will be moved later)
import sys
sys.path.insert(0, '/app/backend')

router = APIRouter(prefix="/debt", tags=["Debt Management"])


@router.post("")
async def create_debt(data: dict, user: dict = Depends(get_current_user)):
    from server import DebtCreate, DebtResponse
    parsed = DebtCreate(**data) if isinstance(data, dict) else data
    debt_id = str(uuid.uuid4())
    debt = {
        "id": debt_id,
        "user_id": user["id"],
        "name": parsed.name,
        "total_amount": parsed.total_amount,
        "remaining_amount": parsed.total_amount,
        "minimum_payment": parsed.minimum_payment,
        "due_day": parsed.due_day,
        "interest_rate": parsed.interest_rate,
        "currency": parsed.currency,
        "payments": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.debts.insert_one(debt)
    return DebtResponse(**{**debt, "created_at": datetime.fromisoformat(debt["created_at"])})


@router.get("")
async def get_debts(user: dict = Depends(get_current_user)):
    from server import DebtResponse
    debts = await db.debts.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return [
        DebtResponse(
            **{
                **d,
                "created_at": datetime.fromisoformat(d["created_at"])
                if isinstance(d["created_at"], str)
                else d["created_at"],
            }
        )
        for d in debts
    ]


@router.post("/{debt_id}/payment")
async def make_debt_payment(debt_id: str, amount: float, user: dict = Depends(get_current_user)):
    debt = await db.debts.find_one({"id": debt_id, "user_id": user["id"]}, {"_id": 0})
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    new_remaining = max(0, debt["remaining_amount"] - amount)
    payment = {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "date": datetime.now(timezone.utc).isoformat(),
    }

    await db.debts.update_one(
        {"id": debt_id},
        {"$set": {"remaining_amount": new_remaining}, "$push": {"payments": payment}},
    )

    return {"message": "Payment recorded", "new_remaining": new_remaining}


@router.get("/plan")
async def get_debt_repayment_plan(user: dict = Depends(get_current_user)):
    debts = await db.debts.find(
        {"user_id": user["id"], "remaining_amount": {"$gt": 0}}, {"_id": 0}
    ).to_list(100)

    monthly_commitment = sum(d["minimum_payment"] for d in debts)

    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)

    total_deposits = sum(d["amount"] for d in deposits)
    total_profit = sum(t["actual_profit"] for t in trades)
    account_value = total_deposits + total_profit

    upcoming_payments = []
    today = datetime.now(timezone.utc)

    for debt_item in debts:
        due_day = debt_item["due_day"]
        if today.day < due_day:
            next_due = today.replace(day=due_day)
        else:
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year if today.month < 12 else today.year + 1
            next_due = today.replace(year=next_year, month=next_month, day=due_day)

        days_until = (next_due - today).days
        upcoming_payments.append({
            "debt_name": debt_item["name"],
            "amount": debt_item["minimum_payment"],
            "due_date": next_due.isoformat(),
            "days_until": days_until,
            "withdrawal_deadline": (next_due - timedelta(days=2)).isoformat(),
        })

    return {
        "total_debt": sum(d["remaining_amount"] for d in debts),
        "monthly_commitment": monthly_commitment,
        "account_value": round(account_value, 2),
        "can_cover_this_month": account_value >= monthly_commitment,
        "upcoming_payments": sorted(upcoming_payments, key=lambda x: x["days_until"]),
        "debts_count": len(debts),
    }
