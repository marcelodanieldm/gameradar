"""
Talent-Ping Notification Service
Cultural UX/UI: WhatsApp/Telegram for India/Vietnam, Email+PDF for Korea/China/Japan
"""
import os
from typing import List, Dict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


class PlayerAlert(BaseModel):
    """Player talent alert model"""
    player_name: str
    player_position: str
    player_age: int
    similarity_score: float
    key_stats: Dict[str, float]
    profile_url: str
    region: str


class NotificationPreference(BaseModel):
    """User notification preference"""
    user_id: str
    region: Literal["india", "vietnam", "korea", "japan", "china", "global"]
    email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    notification_channels: List[Literal["email", "whatsapp", "telegram", "in_app"]]
    alert_frequency: Literal["instant", "daily", "weekly"] = "instant"


class TalentPingNotificationService:
    """
    Regional Notification Service with Cultural Customization
    - India/Vietnam: WhatsApp + Telegram (Push-first, FOMO-driven)
    - Korea/China/Japan: Email + PDF Reports (Professional, formal)
    """
    
    def __init__(self):
        # WhatsApp Business API
        self.whatsapp_token = os.getenv("WHATSAPP_BUSINESS_TOKEN")
        self.whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        
        # Telegram Bot API
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Email SMTP
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        # Frontend URL
        self.frontend_url = os.getenv("FRONTEND_URL", "https://gameradar.com")
    
    async def send_talent_alert(
        self, 
        preference: NotificationPreference, 
        alert: PlayerAlert
    ) -> Dict[str, bool]:
        """
        Send talent alert through preferred channels
        Returns success status for each channel
        """
        results = {}
        
        # Route based on region and preferences
        if "whatsapp" in preference.notification_channels and preference.whatsapp_number:
            results["whatsapp"] = await self._send_whatsapp_alert(
                preference.whatsapp_number,
                alert,
                preference.region
            )
        
        if "telegram" in preference.notification_channels and preference.telegram_id:
            results["telegram"] = await self._send_telegram_alert(
                preference.telegram_id,
                alert,
                preference.region
            )
        
        if "email" in preference.notification_channels and preference.email:
            # Professional markets get PDF reports
            include_pdf = preference.region in ["korea", "japan", "china"]
            results["email"] = await self._send_email_alert(
                preference.email,
                alert,
                preference.region,
                include_pdf=include_pdf
            )
        
        return results
    
    async def _send_whatsapp_alert(
        self, 
        phone_number: str, 
        alert: PlayerAlert,
        region: str
    ) -> bool:
        """
        Send WhatsApp message (India/Vietnam - FOMO-driven)
        """
        try:
            if not self.whatsapp_token or not self.whatsapp_phone_id:
                return False
            
            # FOMO-driven messaging for India/Vietnam
            message = self._generate_whatsapp_message(alert, region)
            
            url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            print(f"WhatsApp error: {e}")
            return False
    
    async def _send_telegram_alert(
        self, 
        telegram_id: str, 
        alert: PlayerAlert,
        region: str
    ) -> bool:
        """
        Send Telegram message (India/Vietnam - Quick alerts)
        """
        try:
            if not self.telegram_bot_token:
                return False
            
            message = self._generate_telegram_message(alert, region)
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": telegram_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    async def _send_email_alert(
        self, 
        email: str, 
        alert: PlayerAlert,
        region: str,
        include_pdf: bool = False
    ) -> bool:
        """
        Send Email alert (Korea/China/Japan - Professional format)
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                return False
            
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = email
            msg["Subject"] = self._get_email_subject(alert, region)
            
            # HTML body based on region
            html_body = self._generate_email_html(alert, region)
            msg.attach(MIMEText(html_body, "html"))
            
            # Attach PDF report for professional markets
            if include_pdf:
                pdf_content = self._generate_pdf_report(alert)
                pdf_attachment = MIMEApplication(pdf_content, _subtype="pdf")
                pdf_attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=f"talent_report_{alert.player_name.replace(' ', '_')}.pdf"
                )
                msg.attach(pdf_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def _generate_whatsapp_message(self, alert: PlayerAlert, region: str) -> str:
        """
        Generate FOMO-driven WhatsApp message (India/Vietnam)
        """
        emoji_fire = "🔥"
        emoji_alert = "🚨"
        emoji_trophy = "🏆"
        
        return f"""{emoji_alert} *TALENT ALERT* {emoji_alert}

{emoji_fire} *New Match Found!*

*Player:* {alert.player_name}
*Position:* {alert.player_position} | *Age:* {alert.player_age}
*Match Score:* {alert.similarity_score:.1%} {emoji_trophy}

*Key Stats:*
{self._format_stats_whatsapp(alert.key_stats)}

{emoji_fire} *Don't miss this opportunity!*
View full profile: {self.frontend_url}/player/{alert.profile_url}

_Powered by GameRadar Talent-Ping_"""
    
    def _generate_telegram_message(self, alert: PlayerAlert, region: str) -> str:
        """
        Generate Telegram message (India/Vietnam)
        """
        return f"""🔔 *TALENT PING ALERT*

**{alert.player_name}**
Position: {alert.player_position} | Age: {alert.player_age}
Match Score: *{alert.similarity_score:.1%}*

**Key Statistics:**
{self._format_stats_telegram(alert.key_stats)}

[View Full Profile]({self.frontend_url}/player/{alert.profile_url})

_Real-time talent discovery by GameRadar_"""
    
    def _get_email_subject(self, alert: PlayerAlert, region: str) -> str:
        """
        Email subject based on region
        """
        if region in ["korea", "japan", "china"]:
            return f"GameRadar Talent Report: {alert.player_name} - {alert.similarity_score:.1%} Match"
        else:
            return f"🔥 New Talent Alert: {alert.player_name}"
    
    def _generate_email_html(self, alert: PlayerAlert, region: str) -> str:
        """
        Generate HTML email (Professional format for Korea/Japan/China)
        """
        if region in ["korea", "japan", "china"]:
            # Professional format
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px;">
                    <h2 style="color: #1a73e8;">GameRadar Talent Analysis Report</h2>
                    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                    
                    <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">{alert.player_name}</h3>
                        <p><strong>Position:</strong> {alert.player_position}</p>
                        <p><strong>Age:</strong> {alert.player_age}</p>
                        <p><strong>Similarity Score:</strong> {alert.similarity_score:.1%}</p>
                    </div>
                    
                    <h4>Performance Metrics</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        {self._format_stats_html_table(alert.key_stats)}
                    </table>
                    
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{self.frontend_url}/player/{alert.profile_url}" 
                           style="background: #1a73e8; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            View Complete Analysis
                        </a>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 12px; color: #666;">
                        This is an automated talent discovery report. Please review the attached PDF for detailed analysis.
                    </p>
                </div>
            </body>
            </html>
            """
        else:
            # Casual format for other regions
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2>🔥 New Talent Match!</h2>
                    <h3>{alert.player_name}</h3>
                    <p><strong>Position:</strong> {alert.player_position} | <strong>Age:</strong> {alert.player_age}</p>
                    <p><strong>Match Score:</strong> {alert.similarity_score:.1%}</p>
                    
                    <a href="{self.frontend_url}/player/{alert.profile_url}" 
                       style="background: #ff6b35; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Check Profile Now
                    </a>
                </div>
            </body>
            </html>
            """
    
    def _format_stats_whatsapp(self, stats: Dict[str, float]) -> str:
        """Format stats for WhatsApp"""
        lines = []
        for key, value in list(stats.items())[:5]:  # Top 5 stats
            lines.append(f"• {key}: {value:.2f}")
        return "\n".join(lines)
    
    def _format_stats_telegram(self, stats: Dict[str, float]) -> str:
        """Format stats for Telegram"""
        lines = []
        for key, value in list(stats.items())[:5]:
            lines.append(f"• {key}: `{value:.2f}`")
        return "\n".join(lines)
    
    def _format_stats_html_table(self, stats: Dict[str, float]) -> str:
        """Format stats as HTML table"""
        rows = []
        for key, value in stats.items():
            rows.append(f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 8px;">{key}</td>
                    <td style="padding: 8px; text-align: right;"><strong>{value:.2f}</strong></td>
                </tr>
            """)
        return "".join(rows)
    
    def _generate_pdf_report(self, alert: PlayerAlert) -> bytes:
        """
        Generate PDF report (Korea/Japan/China)
        Using ReportLab for PDF generation
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.units import inch
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"<b>GameRadar Talent Analysis Report</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Player Info
            player_info = [
                ["Player Name", alert.player_name],
                ["Position", alert.player_position],
                ["Age", str(alert.player_age)],
                ["Similarity Score", f"{alert.similarity_score:.1%}"],
                ["Report Date", datetime.now().strftime("%Y-%m-%d %H:%M")]
            ]
            
            info_table = Table(player_info, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Stats Table
            story.append(Paragraph("<b>Performance Metrics</b>", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            stats_data = [["Metric", "Value"]]
            for key, value in alert.key_stats.items():
                stats_data.append([key, f"{value:.2f}"])
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(stats_table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.read()
            
        except ImportError:
            # Fallback if reportlab not installed
            return b"PDF generation requires reportlab package"
        except Exception as e:
            print(f"PDF generation error: {e}")
            return b"Error generating PDF"


# Singleton instance
talent_ping_service = TalentPingNotificationService()
