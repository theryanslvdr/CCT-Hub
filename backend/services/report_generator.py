"""
Performance Recap Report Generator
Generates image-based performance reports for trading statistics
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import os

# Colors
COLORS = {
    'background': '#18181B',  # zinc-900
    'card_bg': '#27272A',     # zinc-800
    'text_primary': '#FFFFFF',
    'text_secondary': '#A1A1AA',  # zinc-400
    'text_muted': '#71717A',  # zinc-500
    'accent_green': '#34D399',  # emerald-400
    'accent_red': '#F87171',   # red-400
    'accent_blue': '#60A5FA',  # blue-400
    'accent_purple': '#A78BFA', # purple-400
    'accent_amber': '#FBBF24',  # amber-400
    'border': '#3F3F46',      # zinc-700
}

def get_font(size: int, bold: bool = False):
    """Get a font - uses default if custom font not available"""
    try:
        # Try to use a better font if available
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except:
        pass
    return ImageFont.load_default()

def draw_rounded_rect(draw: ImageDraw, xy: tuple, radius: int, fill: str):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill)

def format_currency(value: float) -> str:
    """Format value as currency"""
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.1f}K"
    return f"${value:.2f}"

def format_percent(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"

async def generate_performance_report(
    user_name: str,
    period: str,  # 'daily', 'weekly', 'monthly'
    stats: Dict[str, Any],
    trades: list = None,
    platform_name: str = "CrossCurrent"
) -> bytes:
    """
    Generate an image-based performance report
    
    Args:
        user_name: Name of the user
        period: Report period (daily, weekly, monthly)
        stats: Dictionary containing:
            - account_value: Current account value
            - total_profit: Total profit for period
            - total_trades: Number of trades
            - win_rate: Percentage of profitable trades
            - avg_profit_per_trade: Average profit per trade
            - best_trade: Best trade profit
            - worst_trade: Worst trade profit
            - streak: Current win/loss streak
        trades: List of recent trades (optional)
        platform_name: Name of the platform
    
    Returns:
        PNG image as bytes
    """
    
    # Image dimensions
    width = 800
    height = 600
    padding = 30
    
    # Create image
    img = Image.new('RGB', (width, height), COLORS['background'])
    draw = ImageDraw.Draw(img)
    
    # Fonts
    font_title = get_font(28, bold=True)
    font_subtitle = get_font(16)
    font_large = get_font(32, bold=True)
    font_medium = get_font(18, bold=True)
    font_small = get_font(14)
    font_tiny = get_font(12)
    
    # Header
    y = padding
    draw.text((padding, y), f"{platform_name}", font=font_title, fill=COLORS['accent_blue'])
    
    period_text = {
        'daily': 'Daily',
        'weekly': 'Weekly', 
        'monthly': 'Monthly'
    }.get(period, 'Performance')
    
    draw.text((width - padding - 200, y), f"{period_text} Report", font=font_subtitle, fill=COLORS['text_secondary'])
    
    y += 45
    draw.text((padding, y), f"{user_name}'s Performance", font=font_medium, fill=COLORS['text_primary'])
    
    # Date
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    draw.text((width - padding - 150, y), date_str, font=font_small, fill=COLORS['text_muted'])
    
    y += 40
    draw.line([(padding, y), (width - padding, y)], fill=COLORS['border'], width=1)
    y += 20
    
    # Main Stats Cards
    card_width = (width - padding * 3) // 2
    card_height = 100
    
    # Account Value Card
    draw_rounded_rect(draw, (padding, y, padding + card_width, y + card_height), 10, COLORS['card_bg'])
    draw.text((padding + 15, y + 15), "Account Value", font=font_small, fill=COLORS['text_secondary'])
    account_value = stats.get('account_value', 0)
    draw.text((padding + 15, y + 40), format_currency(account_value), font=font_large, fill=COLORS['text_primary'])
    
    # Total Profit Card
    profit_x = padding * 2 + card_width
    draw_rounded_rect(draw, (profit_x, y, profit_x + card_width, y + card_height), 10, COLORS['card_bg'])
    draw.text((profit_x + 15, y + 15), f"{period_text} Profit", font=font_small, fill=COLORS['text_secondary'])
    total_profit = stats.get('total_profit', 0)
    profit_color = COLORS['accent_green'] if total_profit >= 0 else COLORS['accent_red']
    profit_prefix = "+" if total_profit >= 0 else ""
    draw.text((profit_x + 15, y + 40), f"{profit_prefix}{format_currency(total_profit)}", font=font_large, fill=profit_color)
    
    y += card_height + 20
    
    # Stats Row 1
    stats_y = y
    stat_width = (width - padding * 4) // 3
    stat_height = 80
    
    # Total Trades
    draw_rounded_rect(draw, (padding, stats_y, padding + stat_width, stats_y + stat_height), 8, COLORS['card_bg'])
    draw.text((padding + 12, stats_y + 12), "Total Trades", font=font_tiny, fill=COLORS['text_muted'])
    draw.text((padding + 12, stats_y + 35), str(stats.get('total_trades', 0)), font=font_medium, fill=COLORS['accent_purple'])
    
    # Win Rate
    wr_x = padding * 2 + stat_width
    draw_rounded_rect(draw, (wr_x, stats_y, wr_x + stat_width, stats_y + stat_height), 8, COLORS['card_bg'])
    draw.text((wr_x + 12, stats_y + 12), "Win Rate", font=font_tiny, fill=COLORS['text_muted'])
    win_rate = stats.get('win_rate', 0)
    wr_color = COLORS['accent_green'] if win_rate >= 50 else COLORS['accent_amber']
    draw.text((wr_x + 12, stats_y + 35), format_percent(win_rate), font=font_medium, fill=wr_color)
    
    # Avg Profit/Trade
    avg_x = padding * 3 + stat_width * 2
    draw_rounded_rect(draw, (avg_x, stats_y, avg_x + stat_width, stats_y + stat_height), 8, COLORS['card_bg'])
    draw.text((avg_x + 12, stats_y + 12), "Avg/Trade", font=font_tiny, fill=COLORS['text_muted'])
    avg_profit = stats.get('avg_profit_per_trade', 0)
    avg_color = COLORS['accent_green'] if avg_profit >= 0 else COLORS['accent_red']
    draw.text((avg_x + 12, stats_y + 35), format_currency(avg_profit), font=font_medium, fill=avg_color)
    
    y = stats_y + stat_height + 15
    
    # Stats Row 2
    # Best Trade
    draw_rounded_rect(draw, (padding, y, padding + stat_width, y + stat_height), 8, COLORS['card_bg'])
    draw.text((padding + 12, y + 12), "Best Trade", font=font_tiny, fill=COLORS['text_muted'])
    best_trade = stats.get('best_trade', 0)
    draw.text((padding + 12, y + 35), f"+{format_currency(best_trade)}", font=font_medium, fill=COLORS['accent_green'])
    
    # Worst Trade
    draw_rounded_rect(draw, (wr_x, y, wr_x + stat_width, y + stat_height), 8, COLORS['card_bg'])
    draw.text((wr_x + 12, y + 12), "Worst Trade", font=font_tiny, fill=COLORS['text_muted'])
    worst_trade = stats.get('worst_trade', 0)
    draw.text((wr_x + 12, y + 35), format_currency(worst_trade), font=font_medium, fill=COLORS['accent_red'])
    
    # Streak
    draw_rounded_rect(draw, (avg_x, y, avg_x + stat_width, y + stat_height), 8, COLORS['card_bg'])
    draw.text((avg_x + 12, y + 12), "Current Streak", font=font_tiny, fill=COLORS['text_muted'])
    streak = stats.get('streak', 0)
    streak_text = f"{abs(streak)} {'Win' if streak > 0 else 'Loss'}" if streak != 0 else "0"
    streak_color = COLORS['accent_green'] if streak > 0 else COLORS['accent_red'] if streak < 0 else COLORS['text_secondary']
    draw.text((avg_x + 12, y + 35), streak_text, font=font_medium, fill=streak_color)
    
    y += stat_height + 25
    
    # Recent Trades Section (if provided)
    if trades and len(trades) > 0:
        draw.text((padding, y), "Recent Trades", font=font_small, fill=COLORS['text_secondary'])
        y += 25
        
        # Table header
        draw.text((padding, y), "Date", font=font_tiny, fill=COLORS['text_muted'])
        draw.text((padding + 100, y), "Direction", font=font_tiny, fill=COLORS['text_muted'])
        draw.text((padding + 200, y), "LOT", font=font_tiny, fill=COLORS['text_muted'])
        draw.text((padding + 280, y), "Profit", font=font_tiny, fill=COLORS['text_muted'])
        y += 20
        
        for trade in trades[:5]:  # Show max 5 trades
            date_str = trade.get('date', '-')
            direction = trade.get('direction', '-')
            lot_size = trade.get('lot_size', 0)
            profit = trade.get('actual_profit', 0)
            
            draw.text((padding, y), str(date_str)[:10], font=font_tiny, fill=COLORS['text_secondary'])
            dir_color = COLORS['accent_green'] if direction == 'BUY' else COLORS['accent_red']
            draw.text((padding + 100, y), direction, font=font_tiny, fill=dir_color)
            draw.text((padding + 200, y), f"{lot_size:.2f}", font=font_tiny, fill=COLORS['accent_purple'])
            profit_color = COLORS['accent_green'] if profit >= 0 else COLORS['accent_red']
            draw.text((padding + 280, y), format_currency(profit), font=font_tiny, fill=profit_color)
            y += 18
    
    # Footer
    y = height - 40
    draw.line([(padding, y), (width - padding, y)], fill=COLORS['border'], width=1)
    y += 15
    draw.text((padding, y), f"Generated by {platform_name} Finance Center", font=font_tiny, fill=COLORS['text_muted'])
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    draw.text((width - padding - 150, y), timestamp, font=font_tiny, fill=COLORS['text_muted'])
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    return buffer.getvalue()

async def generate_report_base64(
    user_name: str,
    period: str,
    stats: Dict[str, Any],
    trades: list = None,
    platform_name: str = "CrossCurrent"
) -> str:
    """Generate report and return as base64 encoded string"""
    image_bytes = await generate_performance_report(user_name, period, stats, trades, platform_name)
    return base64.b64encode(image_bytes).decode('utf-8')
