"""
Email service — sends forgot-password OTP codes via SMTP.
Works with Gmail App Passwords, SendGrid, or any SMTP provider.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def _build_reset_email(to_email: str, user_name: str, code: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your Hazeon AI password reset code: {code}"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    plain = f"""Hi {user_name},

You requested a password reset for your Hazeon AI account.

Your reset code is: {code}

This code expires in 15 minutes. If you did not request this, please ignore this email.

— Hazeon AI Team
"""

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0f1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#1a1d26;border-radius:12px;border:1px solid #2a2d3a;overflow:hidden;">
          <!-- Header -->
          <tr>
            <td style="padding:28px 36px 20px;border-bottom:1px solid #2a2d3a;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                              border-radius:10px;width:40px;height:40px;text-align:center;
                              vertical-align:middle;font-size:16px;font-weight:700;color:#fff;">
                    HZ
                  </td>
                  <td style="padding-left:12px;">
                    <div style="font-size:18px;font-weight:700;color:#e2e8f0;">Hazeon AI</div>
                    <div style="font-size:12px;color:#64748b;">B2B Answer Evaluation Platform</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 36px;">
              <p style="margin:0 0 8px;font-size:20px;font-weight:600;color:#e2e8f0;">
                Password Reset Request
              </p>
              <p style="margin:0 0 24px;font-size:14px;color:#94a3b8;line-height:1.6;">
                Hi <strong style="color:#e2e8f0;">{user_name}</strong>, use the code below to reset your password.
                It expires in <strong style="color:#e2e8f0;">15 minutes</strong>.
              </p>

              <!-- OTP Box -->
              <div style="background:#0f1117;border:1px solid #6366f1;border-radius:10px;
                          padding:24px;text-align:center;margin:0 0 24px;">
                <div style="font-size:11px;letter-spacing:2px;color:#64748b;text-transform:uppercase;
                             margin-bottom:10px;">Your Reset Code</div>
                <div style="font-size:38px;font-weight:700;letter-spacing:10px;
                             color:#a5b4fc;font-family:monospace;">
                  {code}
                </div>
              </div>

              <p style="margin:0;font-size:13px;color:#64748b;line-height:1.6;">
                If you didn't request this, you can safely ignore this email. Your account remains secure.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:16px 36px 24px;border-top:1px solid #2a2d3a;">
              <p style="margin:0;font-size:12px;color:#475569;text-align:center;">
                &copy; 2026 Hazeon AI &mdash; Empowering UPSC &amp; HCS Aspirants
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_reset_code(to_email: str, user_name: str, code: str) -> None:
    """Send a password-reset OTP to the given email address."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # Dev fallback — print to console so developers can test without SMTP
        print(f"\n[EMAIL SERVICE — DEV MODE]\nTo: {to_email}\nReset code: {code}\n")
        return

    msg = _build_reset_email(to_email, user_name, code)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
