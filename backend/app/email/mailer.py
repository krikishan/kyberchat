"""
Gmail SMTP email delivery using a dedicated project Gmail account + App Password.
Never logs the password; never returns it in any API response.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger("kyberchat.mail")


class EmailDeliveryError(Exception):
    pass


def _build_credentials_email(name: str, username: str, temporary_password: str, login_url: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to the Secure Communication Platform"

    text_body = f"""Welcome, {name}.

Your account has been created by the Team Administrator.

Username: {username}
Temporary Password: {temporary_password}

Please log in and change your password immediately: {login_url}
"""

    html_body = f"""
    <div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 480px; margin: 0 auto; color: #1a1a1a;">
      <h2 style="font-weight: 600;">Welcome to the Secure Communication Platform</h2>
      <p>Hi {name}, your account has been created by the Team Administrator.</p>
      <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr><td style="padding: 8px 0; color: #6b7280;">Username</td><td style="padding: 8px 0; font-weight: 600;">{username}</td></tr>
        <tr><td style="padding: 8px 0; color: #6b7280;">Temporary Password</td><td style="padding: 8px 0; font-weight: 600;">{temporary_password}</td></tr>
      </table>
      <p>Please log in and change your password immediately.</p>
      <a href="{login_url}" style="display: inline-block; padding: 10px 20px; background: #111827; color: #fff; text-decoration: none; border-radius: 6px;">Log in</a>
    </div>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


def send_credentials_email(config, to_email: str, name: str, username: str, temporary_password: str) -> None:
    """Raises EmailDeliveryError on any failure (invalid recipient, SMTP failure,
    timeout, connection failure) — caller decides whether to roll back account creation."""
    if not config.get("MAIL_USERNAME") or not config.get("MAIL_PASSWORD"):
        raise EmailDeliveryError("Email service is not configured.")

    msg = _build_credentials_email(name, username, temporary_password, config.get("FRONTEND_URL", ""))
    msg["From"] = config["MAIL_USERNAME"]
    msg["To"] = to_email

    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as server:
            if config.get("MAIL_USE_TLS", True):
                server.starttls()
            server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            server.sendmail(config["MAIL_USERNAME"], [to_email], msg.as_string())
    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailDeliveryError("The recipient email address was rejected.") from exc
    except (smtplib.SMTPException, TimeoutError, OSError) as exc:
        logger.error("SMTP delivery failed (recipient omitted from log detail)")
        raise EmailDeliveryError("Unable to send the account email. Please try again.") from exc
