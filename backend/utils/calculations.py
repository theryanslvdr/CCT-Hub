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
    
    For licensees: Returns license.current_amount
    For regular users: Returns total_deposits - total_withdrawals + total_profit + total_commission
    
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
    
    # Regular user calculation: sum all deposit amounts (positive = deposit, negative = withdrawal)
    # Then add total profit + total commission from trades
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Sum all deposit amounts - negative amounts are withdrawals
    # This is simpler and handles cases where amount is negative but is_withdrawal flag is not set
    total_net_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit"])
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)  # Sum daily commissions from trades
    
    return round(total_net_deposits + total_profit + total_commission, 2)


async def get_user_financial_summary(
    db,
    user_id: str,
    user: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Get comprehensive financial summary for a user.
    
    Returns:
        Dict with total_deposits, total_withdrawals, total_profit, account_value, is_licensee
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
    
    # Calculate account value
    if is_licensee and license_info:
        account_value = round(license_info.get("current_amount", license_info.get("starting_amount", 0)), 2)
        # For licensees, total_deposits is the starting amount
        total_deposits = license_info.get("starting_amount", 0)
    else:
        # Net deposits = total deposits - total withdrawals (or sum all amounts since negatives are withdrawals)
        net_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit"])
        account_value = round(net_deposits + total_profit, 2)
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "total_profit": round(total_profit, 2),
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
