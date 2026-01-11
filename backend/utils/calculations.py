def calculate_exit_value(lot_size: float) -> float:
    """Calculate projected exit value based on LOT size"""
    return lot_size * 15  # Default multiplier

def calculate_withdrawal_fees(amount: float) -> dict:
    """Calculate withdrawal fees: 3% Merin + $1 Binance"""
    merin_fee = amount * 0.03
    binance_fee = 1.0
    total_fees = merin_fee + binance_fee
    net_amount = amount - total_fees
    
    return {
        "gross_amount": amount,
        "merin_fee": round(merin_fee, 2),
        "binance_fee": binance_fee,
        "total_fees": round(total_fees, 2),
        "net_amount": round(net_amount, 2)
    }

def calculate_lot_size(account_value: float) -> float:
    """Calculate LOT size from account value using the formula: account_value / 980"""
    if account_value <= 0:
        return 0
    return round(account_value / 980, 2)

def calculate_daily_profit(account_value: float, multiplier: float = 15) -> float:
    """Calculate projected daily profit"""
    lot_size = calculate_lot_size(account_value)
    return round(lot_size * multiplier, 2)
