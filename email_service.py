from flask_mail import Mail, Message
from flask import current_app
import logging

mail = Mail()

def send_verification_email(user_email, user_name, verification_code):
    """
    Send verification email to user
    """
    try:
        # Check if email is properly configured
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        
        if not mail_username or not mail_password:
            logging.error("Email not configured properly - MAIL_USERNAME or MAIL_PASSWORD is missing")
            return False
            
        # Log email configuration for debugging (but don't log password)
        logging.info(f"Email config - Server: {current_app.config.get('MAIL_SERVER')}, Port: {current_app.config.get('MAIL_PORT')}")
        logging.info(f"Email config - TLS: {current_app.config.get('MAIL_USE_TLS')}, SSL: {current_app.config.get('MAIL_USE_SSL')}")
        logging.info(f"Email config - Username: {mail_username}")
        logging.info(f"Attempting to send verification email to: {user_email}")
        logging.info(f"Verification code: {verification_code}")
        
        subject = "Verify Your Email - Resume NER Parser"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196f3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .code {{ background-color: #e3f2fd; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 3px; margin: 20px 0; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Email Verification</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Thank you for signing up for Resume NER Parser. To complete your registration, please verify your email address using the code below:</p>
                    
                    <div class="code">{verification_code}</div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This verification code will expire in 3 minutes for security reasons.
                    </div>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                    
                    <p>Best regards,<br>Resume NER Parser Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        Hello {user_name}!
        
        Thank you for signing up for Resume NER Parser. To complete your registration, please verify your email address using the code below:
        
        Verification Code: {verification_code}
        
        ⚠️ Important: This verification code will expire in 3 minutes for security reasons.
        
        If you didn't create an account with us, please ignore this email.
        
        Best regards,
        Resume NER Parser Team
        
        ---
        This is an automated email. Please do not reply to this message.
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        logging.info(f"Verification email sent successfully to {user_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send verification email to {user_email}: {str(e)}")
        return False

def send_welcome_email(user_email, user_name):
    """
    Send welcome email after successful verification
    """
    try:
        subject = "Welcome to Resume NER Parser!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                .feature {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196f3; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Resume NER Parser!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Congratulations! Your email has been successfully verified and your account is now active.</p>
                    
                    <h3>What you can do now:</h3>
                    <div class="feature">
                        <strong>📄 Upload Resume PDFs</strong><br>
                        Upload your resume in PDF format for AI-powered analysis
                    </div>
                    <div class="feature">
                        <strong>🤖 Extract Entities</strong><br>
                        Get detailed entity extraction including names, skills, companies, and more
                    </div>
                    <div class="feature">
                        <strong>📊 View Results</strong><br>
                        See extracted entities in beautiful card layouts and view your original PDF
                    </div>
                    
                    <p>Ready to get started? <a href="http://localhost:3000" style="color: #2196f3; text-decoration: none;">Visit the application</a></p>
                    
                    <p>Best regards,<br>Resume NER Parser Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hello {user_name}!
        
        Congratulations! Your email has been successfully verified and your account is now active.
        
        What you can do now:
        📄 Upload Resume PDFs - Upload your resume in PDF format for AI-powered analysis
        🤖 Extract Entities - Get detailed entity extraction including names, skills, companies, and more
        📊 View Results - See extracted entities in beautiful card layouts and view your original PDF
        
        Ready to get started? Visit: http://localhost:3000
        
        Best regards,
        Resume NER Parser Team
        
        ---
        This is an automated email. Please do not reply to this message.
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        logging.info(f"Welcome email sent successfully to {user_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send welcome email to {user_email}: {str(e)}")
        return False 