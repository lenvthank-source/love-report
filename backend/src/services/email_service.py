import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

class EmailService:
    def __init__(self):
        self.smtp_host = "smtp-pulse.com"
        self.smtp_port = int(os.getenv("SENDPULSE_SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SENDPULSE_SMTP_USER")
        self.smtp_pass = os.getenv("SENDPULSE_SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL", "hello@cosmicreport.com")
        self.sender_name = os.getenv("SENDER_NAME", "Cosmic Oracle Support")

    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_pass)

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Helper to send SMTP email using SendPulse host."""
        if not self.is_configured():
            print(f"\n==================================================")
            print(f"[MOCK EMAIL] TO: {to_email}")
            print(f"[MOCK EMAIL] SUBJECT: {subject}")
            print(f"[MOCK EMAIL] CONTENT:\n{html_content[:300]}...")
            print(f"==================================================\n")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email
            
            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)
            
            # port 465 requires SSL, port 587 requires STARTTLS
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.sender_email, to_email, msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.sender_email, to_email, msg.as_string())
            print(f"[EmailService] Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"[EmailService] Error sending email: {e}")
            return False

    def send_order_confirmation(self, to_email: str, customer_name: str, order_id: str) -> bool:
        """Sends the immediate 24-36 hour delivery confirmation email."""
        subject = f"✨ Preparing Your Cosmic Love & Marriage Report — Order #{order_id[-8:]}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Georgia', serif;
                    background-color: #FAF8F5;
                    color: #1E1A18;
                    margin: 0; padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #FFFFFF;
                    border: 1px solid rgba(201, 150, 123, 0.35);
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 1px solid rgba(142, 110, 94, 0.2);
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    font-family: 'Cormorant Garamond', Georgia, serif;
                    font-size: 24px;
                    color: #3B2E2B;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }}
                .content p {{
                    font-size: 16px;
                    line-height: 1.8;
                    margin-bottom: 20px;
                }}
                .boxed-info {{
                    background-color: rgba(212, 166, 140, 0.1);
                    border-left: 4px solid #C9967B;
                    padding: 20px;
                    margin: 30px 0;
                    border-radius: 0 6px 6px 0;
                }}
                .boxed-info h3 {{
                    margin-top: 0;
                    color: #5D4035;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(142, 110, 94, 0.2);
                    font-size: 13px;
                    color: #8E6E5E;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Cosmic Blueprint</h1>
                </div>
                <div class="content">
                    <p>Dear {customer_name}, ✨</p>
                    <p>Thank you for placing your trust in the stars. Your order for the <strong>Personalised Love & Marriage Analysis Report</strong> has been successfully received, and payment has been captured.</p>
                    <p>Unlike standard generic horoscopes, each report is compiled individually. Our astrologer <strong>Acharya Savvy Singh</strong> will personally align your natal placements (D1 Birth Chart) with your marital destiny gateway (D9 Navamsa) and karmic path (D30 Trimsamsha) to map your unique emotional profile.</p>
                    
                    <div class="boxed-info">
                        <h3>📋 Order Details</h3>
                        <p style="margin: 5px 0;"><strong>Order Reference:</strong> #{order_id}</p>
                        <p style="margin: 5px 0;"><strong>Estimated Delivery:</strong> Within 24 to 36 hours</p>
                        <p style="margin: 5px 0;"><strong>Support Email:</strong> hello@cosmicreport.com</p>
                    </div>

                    <p>We are currently casting your charts and preparing your reading. As soon as your stars have aligned and the report is complete, you will receive an email containing your private access link.</p>
                    <p>May this journey bring you clarity, reassurance, and the wisdom to welcome love with a peaceful mind.</p>
                </div>
                <div class="footer">
                    <p>With heartfelt blessings,<br>Acharya Savvy Singh &bull; Cosmic Oracle Support</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, html)

    def send_report_delivered(self, to_email: str, customer_name: str, order_id: str, report_url: str) -> bool:
        """Sends the final PDF delivery email containing the Storage download link."""
        subject = f"🎉 Your Cosmic Individual Love & Marriage Report is Ready!"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Georgia', serif;
                    background-color: #FAF8F5;
                    color: #1E1A18;
                    margin: 0; padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #FFFFFF;
                    border: 1px solid rgba(201, 150, 123, 0.35);
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 1px solid rgba(142, 110, 94, 0.2);
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    font-family: 'Cormorant Garamond', Georgia, serif;
                    font-size: 24px;
                    color: #3B2E2B;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }}
                .content p {{
                    font-size: 16px;
                    line-height: 1.8;
                    margin-bottom: 20px;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .btn {{
                    background-color: #C9967B;
                    color: #FFFFFF !important;
                    padding: 14px 28px;
                    font-size: 16px;
                    font-weight: bold;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    letter-spacing: 1px;
                    box-shadow: 0 4px 10px rgba(201, 150, 123, 0.3);
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(142, 110, 94, 0.2);
                    font-size: 13px;
                    color: #8E6E5E;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Stars Have Aligned</h1>
                </div>
                <div class="content">
                    <p>Dear {customer_name}, ✨</p>
                    <p>We are delighted to inform you that your **Cosmic Individual Love & Marriage Report** is complete.</p>
                    <p>Acharya Savvy Singh has finished mapping your personal charts. The insights, D1/D9/D30 maps, planetary seasons, and customized behavioural shifts are now consolidated into a premium 26-page report designed specifically for your soul's growth.</p>
                    
                    <div class="btn-container">
                        <a href="{report_url}" class="btn" target="_blank">📖 DOWNLOAD YOUR COSMIC REPORT</a>
                    </div>

                    <p>If you have any questions or require guidance on your alignments, please do not hesitate to contact our support team at hello@cosmicreport.com.</p>
                    <p>May this report light your path forward and guide you toward the love you are truly destined to experience.</p>
                </div>
                <div class="footer">
                    <p>With heartfelt blessings,<br>Acharya Savvy Singh &bull; Cosmic Oracle Support</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self._send_email(to_email, subject, html)
