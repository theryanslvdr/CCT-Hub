"""Calculation utility functions for trading, LOT size, etc."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List


async def calculate_account_value(
    db,
    user_id: str,
    user: Optional[Dict] = None,
    include_licensee_check: bool = True
) -> float:
    """
    Calculate account value for a user.
    
    For licensees: Returns license.current_amount (their virtual share of Master Admin's pool)
    For regular users/Master Admin: Returns total_deposits - total_withdrawals + total_profit + total_commission
    
    NOTE: Licensee funds are ALREADY INCLUDED in Master Admin's account value (they deposited into it).
    We do NOT add licensee funds on top - that would be double-counting.
    
    Args:
        db: Database connection
        user_id: User's ID
        user: Optional user dict (to avoid extra DB lookup)
        include_licensee_check: Whether to check if user is a licensee
    
    Returns:
        Account value as float
    """
    # Check if user is a licensee
    if include_licensee_check:
        if user is None:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        if user and user.get("license_type"):
            license = await db.licenses.find_one(
                {"user_id": user_id, "is_active": True},
                {"_id": 0}
            )
            if license:
                return round(license.get("current_amount", license.get("starting_amount", 0)), 2)
    
    # Regular user / Master Admin calculation: sum all deposit amounts (positive = deposit, negative = withdrawal)
    # Then add total profit + total commission from trades
    # NOTE: For Master Admin, licensee deposits are already in the deposits collection
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Sum all deposit amounts - negative amounts are withdrawals
    total_net_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit"])
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)
    
    return round(total_net_deposits + total_profit + total_commission, 2)


async def calculate_total_managed_licensee_funds(db, master_admin_id: str) -> float:
    """
    Calculate the total virtual share funds across all active licensees managed by a Master Admin.
    
    IMPORTANT: These funds are ALREADY PART OF the Master Admin's account value.
    Licensees deposited into the Master Admin's Merin account.
    This function calculates how much of the Master Admin's pool belongs to licensees.
    
    Args:
        db: Database connection
        master_admin_id: The Master Admin's user ID (who created the licenses)
    
    Returns:
        Total virtual share across all active licensees
    """
    # Get all active licenses created by this master admin
    active_licenses = await db.licenses.find(
        {"created_by": master_admin_id, "is_active": True},
        {"_id": 0}
    ).to_list(1000)
    
    total_licensee_funds = 0.0
    for license in active_licenses:
        # Use current_amount if available, otherwise use starting_amount
        amount = license.get("current_amount", license.get("starting_amount", 0))
        total_licensee_funds += amount
    
    return round(total_licensee_funds, 2)


async def get_master_admin_financial_breakdown(db, user_id: str, user: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get detailed financial breakdown for a Master Admin, including licensee funds.
    
    Returns:
        Dict with personal_account_value, licensee_funds, total_account_value, licensee_count, etc.
    """
    if user is None:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user or user.get("role") != "master_admin":
        return {"error": "User is not a Master Admin"}
    
    # Get Master Admin's total account value (this is the actual Merin balance)
    # Licensee funds are ALREADY PART OF this balance
    master_summary = await get_user_financial_summary(db, user_id, user)
    total_pool = master_summary["account_value"]
    
    # Get licensee virtual share breakdown
    active_licenses = await db.licenses.find(
        {"created_by": user_id, "is_active": True},
        {"_id": 0}
    ).to_list(1000)
    
    total_licensee_funds = 0.0
    licensee_breakdown = []
    
    for license in active_licenses:
        licensee_user = await db.users.find_one({"id": license["user_id"]}, {"_id": 0, "full_name": 1})
        current_amount = license.get("current_amount", license.get("starting_amount", 0))
        starting_amount = license.get("starting_amount", 0)
        # Total profit for licensee = current_amount - starting_amount (projected profits accumulated when manager traded)
        total_profit = round(current_amount - starting_amount, 2)
        total_licensee_funds += current_amount
        
        # Calculate percentage share of the pool
        share_percentage = round((current_amount / total_pool * 100) if total_pool > 0 else 0, 2)
        
        licensee_breakdown.append({
            "license_id": license.get("id"),
            "user_id": license.get("user_id"),
            "user_name": licensee_user.get("full_name") if licensee_user else "Unknown",
            "license_type": license.get("license_type"),
            "starting_amount": round(starting_amount, 2),  # Total Deposit
            "current_amount": round(current_amount, 2),    # Current Balance
            "total_profit": total_profit,                   # Total Profit (projected profits when manager traded)
            "share_percentage": share_percentage,           # % Share of the pool
            "effective_start_date": license.get("effective_start_date")
        })
    
    # Master Admin's remaining portion = Total Pool - Licensee Virtual Shares
    master_admin_portion = round(total_pool - total_licensee_funds, 2)
    master_admin_share_percentage = round((master_admin_portion / total_pool * 100) if total_pool > 0 else 100, 2)
    
    return {
        "total_pool": round(total_pool, 2),                      # Merin Balance (the actual trading account)
        "master_admin_portion": master_admin_portion,             # Master Admin's remaining share
        "master_admin_share_percentage": master_admin_share_percentage,
        "licensee_funds": round(total_licensee_funds, 2),        # Total of all licensee virtual shares
        "licensee_share_percentage": round(100 - master_admin_share_percentage, 2),
        "licensee_count": len(active_licenses),
        "licensee_breakdown": licensee_breakdown,
        # Include other summary fields for reference
        "total_deposits": master_summary["total_deposits"],
        "total_profit": master_summary["total_profit"],
        "total_commission": master_summary["total_commission"],
        "total_trades": master_summary["total_trades"]
    }


async def get_user_financial_summary(
    db,
    user_id: str,
    user: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Get comprehensive financial summary for a user.
    
    NOTE: For Master Admin, account_value is their actual Merin balance.
    Licensee funds are ALREADY PART OF this balance (not added on top).
    
    Args:
        db: Database connection
        user_id: User's ID
        user: Optional user dict (to avoid extra DB lookup)
    
    Returns:
        Dict with total_deposits, total_withdrawals, total_profit, total_commission, account_value, is_licensee
    """
    is_licensee = False
    license_info = None
    
    # Check for licensee
    if user is None:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if user and user.get("license_type"):
        license = await db.licenses.find_one(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        )
        if license:
            is_licensee = True
            license_info = license
    
    # Get deposits and trades
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Calculate total deposits (positive amounts only)
    total_deposits = sum(
        d.get("amount", 0) for d in deposits 
        if d.get("amount", 0) > 0 and d.get("type") not in ["profit"]
    )
    # Calculate total withdrawals (negative amounts - take absolute value)
    total_withdrawals = sum(
        abs(d.get("amount", 0)) for d in deposits 
        if d.get("amount", 0) < 0 or d.get("is_withdrawal")
    )
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_projected = sum(t.get("projected_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)
    
    # Calculate account value
    if is_licensee and license_info:
        account_value = round(license_info.get("current_amount", license_info.get("starting_amount", 0)), 2)
        # For licensees, total_deposits is the starting amount
        total_deposits = license_info.get("starting_amount", 0)
    else:
        # Net deposits = total deposits - total withdrawals (or sum all amounts since negatives are withdrawals)
        # NOTE: For Master Admin, licensee deposits are already included in the deposits collection
        net_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit"])
        account_value = round(net_deposits + total_profit + total_commission, 2)
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "total_profit": round(total_profit, 2),
        "total_commission": round(total_commission, 2),
        "total_projected_profit": round(total_projected, 2),
        "account_value": account_value,
        "total_trades": len(trades),
        "is_licensee": is_licensee,
        "license_type": license_info.get("license_type") if license_info else None,
        "performance_rate": round((total_profit / total_projected * 100) if total_projected > 0 else 0, 2)
    }


def calculate_lot_size(account_value: float, lot_divisor: float = 980) -> float:
    """Calculate LOT size from account value
    
    Formula: LOT = Account Value / 980
    """
    if account_value <= 0:
        return 0
    return round(account_value / lot_divisor, 2)


def calculate_projected_profit(lot_size: float, profit_points: float = 15) -> float:
    """Calculate projected profit from LOT size
    
    Formula: Projected Profit = LOT × Profit Points (default 15)
    """
    return round(lot_size * profit_points, 2)


def calculate_profit_difference(actual_profit: float, projected_profit: float) -> float:
    """Calculate the difference between actual and projected profit"""
    return round(actual_profit - projected_profit, 2)


def determine_performance(actual_profit: float, projected_profit: float, tolerance: float = 0.5) -> str:
    """Determine performance category based on profit comparison
    
    Returns: 'exceeded', 'perfect', or 'below'
    """
    diff = actual_profit - projected_profit
    if diff > tolerance:
        return 'exceeded'
    elif abs(diff) <= tolerance:
        return 'perfect'
    else:
        return 'below'


def calculate_performance_rate(actual_profit: float, projected_profit: float) -> float:
    """Calculate performance rate as a percentage
    
    Formula: (Actual / Projected) × 100
    Returns 0 if projected is 0 to avoid division by zero
    """
    if projected_profit == 0:
        return 0.0
    return round((actual_profit / projected_profit) * 100, 2)


def calculate_withdrawal_fees(amount: float, merin_fee_percent: float = 3.0, binance_fee: float = 1.0) -> Dict[str, float]:
    """Calculate withdrawal fees
    
    - Merin Fee: 3% of withdrawal amount
    - Binance Fee: $1 flat fee
    """
    merin_fee = round(amount * (merin_fee_percent / 100), 2)
    total_fees = round(merin_fee + binance_fee, 2)
    net_amount = round(amount - total_fees, 2)
    
    return {
        "gross_amount": amount,
        "merin_fee": merin_fee,
        "merin_fee_percent": merin_fee_percent,
        "binance_fee": binance_fee,
        "total_fees": total_fees,
        "net_amount": net_amount
    }


def calculate_quarterly_profit(trades: List[Dict], start_date: datetime) -> Dict[str, Any]:
    """Calculate quarterly profit for licensees
    
    Returns profit data grouped by quarter
    """
    quarters = {}
    
    for trade in trades:
        trade_date = trade.get('created_at', datetime.now(timezone.utc))
        if isinstance(trade_date, str):
            trade_date = datetime.fromisoformat(trade_date.replace('Z', '+00:00'))
        
        # Determine quarter
        quarter_num = (trade_date.month - 1) // 3 + 1
        quarter_key = f"Q{quarter_num} {trade_date.year}"
        
        if quarter_key not in quarters:
            quarters[quarter_key] = {
                "total_profit": 0,
                "trade_count": 0,
                "start_date": None,
                "end_date": None
            }
        
        quarters[quarter_key]["total_profit"] += trade.get('actual_profit', 0)
        quarters[quarter_key]["trade_count"] += 1
        
        if quarters[quarter_key]["start_date"] is None or trade_date < quarters[quarter_key]["start_date"]:
            quarters[quarter_key]["start_date"] = trade_date
        if quarters[quarter_key]["end_date"] is None or trade_date > quarters[quarter_key]["end_date"]:
            quarters[quarter_key]["end_date"] = trade_date
    
    return quarters


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string"""
    symbols = {
        "USD": "$",
        "PHP": "₱",
        "SGD": "S$",
        "TWD": "NT$",
        "USDT": "₮"
    }
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:,.2f}"


def get_trading_day_range(timezone_str: str = "Asia/Manila") -> Dict[str, datetime]:
    """Get the start and end of the trading day in the specified timezone"""
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    
    # Trading day starts at 8 AM
    start_of_day = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now < start_of_day:
        start_of_day -= timedelta(days=1)
    
    end_of_day = start_of_day + timedelta(hours=12)  # 8 PM
    
    return {
        "start": start_of_day,
        "end": end_of_day,
        "timezone": timezone_str
    }
