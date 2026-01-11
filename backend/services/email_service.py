"""Email service using Emailit API"""
import os
import httpx
import logging
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


async def send_email(
    db,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    attachments: Optional[List[Dict]] = None
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
        attachments: List of attachments [{"filename": "...", "content": "...", "content_type": "..."}]
    
    Returns:
        Dict with status and message
    """
    api_key = await get_emailit_api_key(db)
    
    if not api_key:
        logger.warning("Emailit API key not configured")
        return {"success": False, "error": "Email service not configured"}
    
    # Get platform settings for sender info
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    platform_name = settings.get("platform_name", "CrossCurrent") if settings else "CrossCurrent"
    
    # Default from email
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
        "subject": f"You're Invited to Join CrossCurrent Finance Center",
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
