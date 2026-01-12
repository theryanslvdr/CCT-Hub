"""Email service using Emailit API"""
import os
import httpx
import logging
import uuid
from typing import Optional, List, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMAILIT_API_URL = "https://api.emailit.com/v1/emails"


async def get_emailit_api_key(db) -> Optional[str]:
    """Get Emailit API key from platform settings or environment"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    api_key = settings.get("emailit_api_key") if settings else None
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.environ.get("EMAILIT_API_KEY")
    
    return api_key


async def log_email(
    db,
    to_email: str,
    subject: str,
    template_type: str,
    status: str = "pending",
    error_message: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> str:
    """Log an email to the email_history collection"""
    email_id = str(uuid.uuid4())
    
    email_record = {
        "id": email_id,
        "to_email": to_email,
        "subject": subject,
        "template_type": template_type,
        "status": status,
        "error_message": error_message,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": datetime.now(timezone.utc).isoformat() if status == "sent" else None
    }
    
    await db.email_history.insert_one(email_record)
    return email_id


async def update_email_status(db, email_id: str, status: str, error_message: Optional[str] = None):
    """Update the status of a logged email"""
    update_data = {"status": status}
    if status == "sent":
        update_data["sent_at"] = datetime.now(timezone.utc).isoformat()
    if error_message:
        update_data["error_message"] = error_message
    
    await db.email_history.update_one({"id": email_id}, {"$set": update_data})


async def send_email(
    db,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    attachments: Optional[List[Dict]] = None,
    template_type: str = "general",
    log_email_record: bool = True,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Send an email using Emailit API
    
    Args:
        db: MongoDB database instance
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML content of the email
        text_content: Plain text content (optional)
        from_email: Sender email address (optional, uses default if not provided)
        reply_to: Reply-to email address (optional)
        attachments: List of attachments
        template_type: Type of email template for logging
        log_email_record: Whether to log the email to history
        metadata: Additional metadata to store with the email log
    
    Returns:
        Dict with status and message
    """
    email_id = None
    
    # Log email as pending if tracking enabled
    if log_email_record:
        email_id = await log_email(db, to_email, subject, template_type, "pending", metadata=metadata)
    
    api_key = await get_emailit_api_key(db)
    
    if not api_key:
        logger.warning("Emailit API key not configured")
        if email_id:
            await update_email_status(db, email_id, "error", "Email service not configured")
        return {"success": False, "error": "Email service not configured"}
    
    # Get platform settings for sender info
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    platform_name = settings.get("platform_name", "CrossCurrent") if settings else "CrossCurrent"
    
    # Default from email - use a generic sender that should be verified
    if not from_email:
        from_email = f"{platform_name} <noreply@crosscurrent.com>"
    
    # Build payload
    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "html": html_content
    }
    
    if text_content:
        payload["text"] = text_content
    
    if reply_to:
        payload["reply_to"] = reply_to
    
    if attachments:
        payload["attachments"] = attachments
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                EMAILIT_API_URL,
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return {"success": True, "message": "Email sent successfully"}
            else:
                error_detail = response.text
                logger.error(f"Emailit API error: {response.status_code} - {error_detail}")
                return {"success": False, "error": f"Failed to send email: {error_detail}"}
    
    except Exception as e:
        logger.error(f"Email sending error: {str(e)}")
        return {"success": False, "error": str(e)}


# Email Templates
def get_license_invite_email(invite_code: str, invitee_name: str, license_type: str, starting_amount: float, base_url: str) -> Dict[str, str]:
    """Generate license invite email content"""
    invite_link = f"{base_url}/license-registration?code={invite_code}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #06B6D4); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .details {{ background: white; padding: 15px; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 You're Invited!</h1>
            </div>
            <div class="content">
                <p>Hello{' ' + invitee_name if invitee_name else ''},</p>
                <p>You have been invited to join CrossCurrent Finance Center as a <strong>{license_type.title()} Licensee</strong>!</p>
                
                <div class="details">
                    <h3>Your License Details:</h3>
                    <p><strong>License Type:</strong> {license_type.title()}</p>
                    <p><strong>Starting Amount:</strong> ${starting_amount:,.2f}</p>
                </div>
                
                <p>Click the button below to complete your registration:</p>
                <p style="text-align: center;">
                    <a href="{invite_link}" class="button">Complete Registration</a>
                </p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy this link: {invite_link}
                </p>
                
                <div class="footer">
                    <p>This invitation was sent from CrossCurrent Finance Center.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    You're Invited to CrossCurrent Finance Center!
    
    Hello{' ' + invitee_name if invitee_name else ''},
    
    You have been invited to join as a {license_type.title()} Licensee!
    
    License Details:
    - License Type: {license_type.title()}
    - Starting Amount: ${starting_amount:,.2f}
    
    Complete your registration: {invite_link}
    
    This invitation was sent from CrossCurrent Finance Center.
    """
    
    return {
        "subject": "You're Invited to Join CrossCurrent Finance Center",
        "html": html,
        "text": text
    }


def get_admin_notification_email(notification_type: str, user_name: str, message: str, amount: Optional[float] = None) -> Dict[str, str]:
    """Generate admin notification email content"""
    
    type_emoji = {
        "deposit": "💰",
        "withdrawal": "💸",
        "trade_underperform": "📉",
        "new_member": "👤",
        "license_activated": "🎫"
    }
    
    emoji = type_emoji.get(notification_type, "📢")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #18181B; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f4f4f5; padding: 25px; border-radius: 0 0 8px 8px; }}
            .alert-box {{ background: white; padding: 15px; border-left: 4px solid #3B82F6; border-radius: 4px; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #10B981; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{emoji} Admin Notification</h2>
            </div>
            <div class="content">
                <div class="alert-box">
                    <p><strong>Member:</strong> {user_name}</p>
                    <p><strong>Activity:</strong> {notification_type.replace('_', ' ').title()}</p>
                    {f'<p class="amount">${amount:,.2f}</p>' if amount else ''}
                    <p>{message}</p>
                </div>
                <p style="margin-top: 20px; color: #6b7280; font-size: 12px;">
                    This is an automated notification from CrossCurrent Finance Center.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Admin Notification - {notification_type.replace('_', ' ').title()}
    
    Member: {user_name}
    Activity: {notification_type.replace('_', ' ').title()}
    {f'Amount: ${amount:,.2f}' if amount else ''}
    
    {message}
    
    This is an automated notification from CrossCurrent Finance Center.
    """
    
    return {
        "subject": f"[Admin Alert] {notification_type.replace('_', ' ').title()} - {user_name}",
        "html": html,
        "text": text
    }


def get_password_reset_email(reset_link: str, user_name: str) -> Dict[str, str]:
    """Generate password reset email content"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #18181B; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .warning {{ background: #FEF3C7; border: 1px solid #F59E0B; padding: 12px; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We received a request to reset your password for your CrossCurrent Finance Center account.</p>
                
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>
                
                <div class="warning">
                    <strong>⚠️ Important:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
                </div>
                
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy this link: {reset_link}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Password Reset Request
    
    Hello {user_name},
    
    We received a request to reset your password for your CrossCurrent Finance Center account.
    
    Click here to reset: {reset_link}
    
    This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.
    """
    
    return {
        "subject": "Reset Your CrossCurrent Password",
        "html": html,
        "text": text
    }


def get_trade_alert_email(signal: Dict, user_name: str) -> Dict[str, str]:
    """Generate trade alert email content"""
    
    direction_color = "#10B981" if signal.get("direction") == "BUY" else "#EF4444"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10B981, #3B82F6); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .signal-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
            .direction {{ font-size: 32px; font-weight: bold; color: {direction_color}; }}
            .details {{ display: flex; justify-content: space-around; margin-top: 15px; }}
            .detail-item {{ text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Trading Signal Alert</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>A new trading signal has been posted:</p>
                
                <div class="signal-box">
                    <p class="direction">{signal.get('direction', 'N/A')}</p>
                    <div class="details">
                        <div class="detail-item">
                            <strong>Product</strong><br>{signal.get('product', 'MOIL10')}
                        </div>
                        <div class="detail-item">
                            <strong>Time</strong><br>{signal.get('trade_time', 'N/A')}
                        </div>
                        <div class="detail-item">
                            <strong>Profit Points</strong><br>{signal.get('profit_points', 15)}
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center; color: #6b7280;">
                    Log in to your dashboard to view more details and track your trades.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Trading Signal Alert
    
    Hello {user_name},
    
    A new trading signal has been posted:
    
    Direction: {signal.get('direction', 'N/A')}
    Product: {signal.get('product', 'MOIL10')}
    Time: {signal.get('trade_time', 'N/A')}
    Profit Points: {signal.get('profit_points', 15)}
    
    Log in to your dashboard to view more details.
    """
    
    return {
        "subject": f"🔔 Trading Signal: {signal.get('direction', 'N/A')} - {signal.get('product', 'MOIL10')}",
        "html": html,
        "text": text
    }


def get_welcome_email(user_name: str, login_url: str) -> Dict[str, str]:
    """Generate welcome email for new users"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #06B6D4); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .features {{ margin: 20px 0; }}
            .feature {{ display: flex; align-items: center; margin: 10px 0; padding: 10px; background: white; border-radius: 6px; }}
            .feature-icon {{ width: 40px; height: 40px; background: #EFF6FF; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-right: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to CrossCurrent!</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Welcome to CrossCurrent Finance Center! Your account has been successfully created.</p>
                
                <div class="features">
                    <h3>Here's what you can do:</h3>
                    <div class="feature">
                        <div class="feature-icon">📊</div>
                        <div>
                            <strong>Track Your Profits</strong>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">Monitor your daily trading performance</p>
                        </div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">⏰</div>
                        <div>
                            <strong>Trade Monitor</strong>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">Never miss a trading signal</p>
                        </div>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">💰</div>
                        <div>
                            <strong>Manage Finances</strong>
                            <p style="margin: 0; font-size: 14px; color: #6b7280;">Plan your profits and manage debts</p>
                        </div>
                    </div>
                </div>
                
                <p style="text-align: center;">
                    <a href="{login_url}" class="button">Get Started</a>
                </p>
                
                <p style="color: #6b7280; font-size: 14px; text-align: center;">
                    If you have any questions, feel free to reach out to our support team.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Welcome to CrossCurrent Finance Center!
    
    Hello {user_name},
    
    Your account has been successfully created.
    
    Here's what you can do:
    - Track Your Profits: Monitor your daily trading performance
    - Trade Monitor: Never miss a trading signal
    - Manage Finances: Plan your profits and manage debts
    
    Get started: {login_url}
    """
    
    return {
        "subject": "🎉 Welcome to CrossCurrent Finance Center!",
        "html": html,
        "text": text
    }


def get_transaction_update_email(
    user_name: str, 
    transaction_type: str, 
    status: str, 
    amount: float,
    message: str = "",
    dashboard_url: str = ""
) -> Dict[str, str]:
    """Generate transaction status update email"""
    
    status_colors = {
        "pending": "#F59E0B",
        "processing": "#3B82F6",
        "awaiting_confirmation": "#06B6D4",
        "completed": "#10B981",
        "rejected": "#EF4444"
    }
    
    status_color = status_colors.get(status, "#6B7280")
    type_label = "Deposit" if transaction_type == "deposit" else "Withdrawal"
    status_label = status.replace("_", " ").title()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {status_color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .status-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border-left: 4px solid {status_color}; }}
            .amount {{ font-size: 32px; font-weight: bold; color: #111; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{type_label} Update</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Your {type_label.lower()} request has been updated.</p>
                
                <div class="status-box">
                    <p style="margin: 0; color: #6b7280;">Amount</p>
                    <p class="amount">${amount:,.2f}</p>
                    <p style="margin: 10px 0 0; font-weight: bold; color: {status_color};">
                        Status: {status_label}
                    </p>
                </div>
                
                {f'<p style="background: #FEF3C7; padding: 12px; border-radius: 6px; border-left: 4px solid #F59E0B;"><strong>Note:</strong> {message}</p>' if message else ''}
                
                <p style="text-align: center;">
                    <a href="{dashboard_url}" class="button">View Dashboard</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    {type_label} Update
    
    Hello {user_name},
    
    Your {type_label.lower()} request has been updated.
    
    Amount: ${amount:,.2f}
    Status: {status_label}
    
    {f'Note: {message}' if message else ''}
    
    View your dashboard: {dashboard_url}
    """
    
    return {
        "subject": f"💵 {type_label} {status_label} - ${amount:,.2f}",
        "html": html,
        "text": text
    }


def get_missed_trade_email(user_name: str, signal: Dict, dashboard_url: str) -> Dict[str, str]:
    """Generate missed trade notification email"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #F59E0B; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .alert-box {{ background: #FEF3C7; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 1px solid #F59E0B; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ You Missed a Trade!</h1>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>We noticed you didn't log a trade for today's signal.</p>
                
                <div class="alert-box">
                    <p style="margin: 0; font-weight: bold; font-size: 18px;">{signal.get('direction', 'N/A')} Signal</p>
                    <p style="margin: 5px 0;">Product: {signal.get('product', 'MOIL10')}</p>
                    <p style="margin: 5px 0;">Time: {signal.get('trade_time', 'N/A')}</p>
                    <p style="margin: 5px 0;">Expected Profit: ${signal.get('profit_points', 15) * signal.get('lot_size', 1):.2f}</p>
                </div>
                
                <p>Don't forget to log your trades to keep accurate records of your performance!</p>
                
                <p style="text-align: center;">
                    <a href="{dashboard_url}" class="button">Log Trade Now</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    You Missed a Trade!
    
    Hello {user_name},
    
    We noticed you didn't log a trade for today's signal.
    
    {signal.get('direction', 'N/A')} Signal
    Product: {signal.get('product', 'MOIL10')}
    Time: {signal.get('trade_time', 'N/A')}
    
    Don't forget to log your trades to keep accurate records!
    
    Log trade: {dashboard_url}
    """
    
    return {
        "subject": "⚠️ You Missed Today's Trade - CrossCurrent",
        "html": html,
        "text": text
    }


def get_weekly_summary_email(
    user_name: str,
    week_stats: Dict,
    dashboard_url: str
) -> Dict[str, str]:
    """Generate weekly performance summary email"""
    
    total_profit = week_stats.get("total_profit", 0)
    trades_count = week_stats.get("trades_count", 0)
    performance_rate = week_stats.get("performance_rate", 0)
    profit_color = "#10B981" if total_profit >= 0 else "#EF4444"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3B82F6, #8B5CF6); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
            .stat-box {{ background: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 28px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
            .button {{ display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Your Weekly Summary</h1>
                <p style="margin: 0; opacity: 0.9;">Week of {week_stats.get('week_start', 'N/A')}</p>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                <p>Here's your trading performance summary for the week:</p>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <p class="stat-value" style="color: {profit_color};">${abs(total_profit):,.2f}</p>
                        <p class="stat-label">{'Profit' if total_profit >= 0 else 'Loss'}</p>
                    </div>
                    <div class="stat-box">
                        <p class="stat-value" style="color: #3B82F6;">{trades_count}</p>
                        <p class="stat-label">Trades</p>
                    </div>
                    <div class="stat-box">
                        <p class="stat-value" style="color: #8B5CF6;">{performance_rate:.1f}%</p>
                        <p class="stat-label">Performance</p>
                    </div>
                </div>
                
                <p style="text-align: center;">
                    <a href="{dashboard_url}" class="button">View Full Report</a>
                </p>
                
                <p style="color: #6b7280; font-size: 14px; text-align: center;">
                    Keep up the great work! 💪
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Your Weekly Summary - Week of {week_stats.get('week_start', 'N/A')}
    
    Hello {user_name},
    
    Here's your trading performance summary:
    
    {'Profit' if total_profit >= 0 else 'Loss'}: ${abs(total_profit):,.2f}
    Trades: {trades_count}
    Performance: {performance_rate:.1f}%
    
    View full report: {dashboard_url}
    """
    
    return {
        "subject": f"📊 Your Weekly Summary - {'Profit' if total_profit >= 0 else 'Loss'} ${abs(total_profit):,.2f}",
        "html": html,
        "text": text
    }

