"""Calculation utility functions for trading, LOT size, etc."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List


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
