from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, VerificationCode
from email_service import send_verification_email, send_welcome_email
import re
import logging
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 400,
                    'message': 'Bad Request',
                    'error': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        full_name = data['full_name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        confirm_password = data['confirm_password']
        
        # Validate input
        if len(full_name) < 2:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Full name must be at least 2 characters long'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Invalid email format'
            }), 400
        
        if password != confirm_password:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Passwords do not match'
            }), 400
        
        is_valid, password_message = validate_password(password)
        if not is_valid:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': password_message
            }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # If user exists but is not verified, allow re-signup
            if not existing_user.is_verified:
                # Update user info (in case they want to change name or password)
                existing_user.full_name = full_name
                existing_user.set_password(password)
                existing_user.updated_at = datetime.utcnow()
                
                # Invalidate old verification codes
                old_codes = VerificationCode.query.filter_by(
                    user_id=existing_user.id,
                    code_type='email_verification',
                    is_used=False
                ).all()
                
                for code in old_codes:
                    code.is_used = True
                
                # Generate new verification code
                verification_code = VerificationCode(user_id=existing_user.id)
                db.session.add(verification_code)
                db.session.commit()
                
                # Send verification email
                email_sent = send_verification_email(
                    user_email=existing_user.email,
                    user_name=existing_user.full_name,
                    verification_code=verification_code.code
                )
                
                if not email_sent:
                    logging.error(f"Failed to send verification email to {existing_user.email}")
                
                return jsonify({
                    'status': 200,
                    'message': 'Account found but not verified. New verification code sent.',
                    'data': {
                        'user_id': existing_user.id,
                        'email': existing_user.email,
                        'verification_required': True,
                        'email_sent': email_sent,
                        'is_existing_user': True
                    }
                }), 200
            else:
                # User exists and is verified
                return jsonify({
                    'status': 409,
                    'message': 'Conflict',
                    'error': 'User with this email already exists and is verified. Please try logging in instead.'
                }), 409
        
        # Create new user
        user = User(
            full_name=full_name,
            email=email
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate verification code
        verification_code = VerificationCode(user_id=user.id)
        db.session.add(verification_code)
        db.session.commit()
        
        # Send verification email
        email_sent = send_verification_email(
            user_email=user.email,
            user_name=user.full_name,
            verification_code=verification_code.code
        )
        
        if not email_sent:
            # If email fails, we should still return success but log the error
            logging.error(f"Failed to send verification email to {user.email}")
        
        return jsonify({
            'status': 201,
            'message': 'User created successfully',
            'data': {
                'user_id': user.id,
                'email': user.email,
                'verification_required': True,
                'email_sent': email_sent
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Signup error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred during registration'
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Email verification endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('verification_code'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Email and verification code are required'
            }), 400
        
        email = data['email'].strip().lower()
        code = data['verification_code'].strip()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 404,
                'message': 'Not Found',
                'error': 'User not found'
            }), 404
        
        if user.is_verified:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'User is already verified'
            }), 400
        
        # Find verification code
        verification = VerificationCode.query.filter_by(
            user_id=user.id,
            code=code,
            code_type='email_verification'
        ).first()
        
        if not verification:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Invalid verification code'
            }), 400
        
        if not verification.is_valid():
            if verification.is_expired():
                return jsonify({
                    'status': 400,
                    'message': 'Bad Request',
                    'error': 'Verification code has expired'
                }), 400
            else:
                return jsonify({
                    'status': 400,
                    'message': 'Bad Request',
                    'error': 'Verification code has already been used'
                }), 400
        
        # Mark user as verified
        user.is_verified = True
        verification.mark_as_used()
        db.session.commit()
        
        # Send welcome email
        send_welcome_email(user.email, user.full_name)
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'status': 200,
            'message': 'Email verified successfully',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Email verification error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred during verification'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({
                'status': 401,
                'message': 'Unauthorized',
                'error': 'Invalid email or password'
            }), 401
        
        if not user.is_verified:
            # Auto-generate and send new verification code for unverified users
            try:
                # Invalidate old verification codes
                old_codes = VerificationCode.query.filter_by(
                    user_id=user.id,
                    code_type='email_verification',
                    is_used=False
                ).all()
                
                for code in old_codes:
                    code.is_used = True
                
                # Generate new verification code
                verification_code = VerificationCode(user_id=user.id)
                db.session.add(verification_code)
                db.session.commit()
                
                # Send verification email
                email_sent = send_verification_email(
                    user_email=user.email,
                    user_name=user.full_name,
                    verification_code=verification_code.code
                )
                
                if not email_sent:
                    logging.error(f"Failed to send verification email to {user.email} during login")
                
                return jsonify({
                    'status': 403,
                    'message': 'Email Not Verified',
                    'error': 'Please verify your email before logging in. A new verification code has been sent to your email.',
                    'data': {
                        'email': user.email,
                        'verification_required': True,
                        'can_resend_verification': True,
                        'email_sent': email_sent,
                        'auto_sent': True
                    }
                }), 403
                
            except Exception as e:
                logging.error(f"Failed to auto-send verification code during login: {str(e)}")
                return jsonify({
                    'status': 403,
                    'message': 'Email Not Verified',
                    'error': 'Please verify your email before logging in',
                    'data': {
                        'email': user.email,
                        'verification_required': True,
                        'can_resend_verification': True,
                        'email_sent': False,
                        'auto_sent': False
                    }
                }), 403
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'status': 200,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred during login'
        }), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification code endpoint"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Email is required'
            }), 400
        
        email = data['email'].strip().lower()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 404,
                'message': 'Not Found',
                'error': 'User not found'
            }), 404
        
        if user.is_verified:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'User is already verified'
            }), 400
        
        # Invalidate old verification codes
        old_codes = VerificationCode.query.filter_by(
            user_id=user.id,
            code_type='email_verification',
            is_used=False
        ).all()
        
        for code in old_codes:
            code.is_used = True
        
        # Generate new verification code
        verification_code = VerificationCode(user_id=user.id)
        db.session.add(verification_code)
        db.session.commit()
        
        # Send verification email
        email_sent = send_verification_email(
            user_email=user.email,
            user_name=user.full_name,
            verification_code=verification_code.code
        )
        
        if not email_sent:
            logging.error(f"Failed to send verification email to {user.email} via resend endpoint")
        else:
            logging.info(f"Verification email sent successfully to {user.email} via resend endpoint")
        
        return jsonify({
            'status': 200,
            'message': 'Verification code sent successfully' if email_sent else 'Verification code generated but email sending failed',
            'data': {
                'email_sent': email_sent,
                'verification_code_generated': True
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Resend verification error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile endpoint"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 404,
                'message': 'Not Found',
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'status': 200,
            'message': 'Profile retrieved successfully',
            'data': {
                'user': user.to_dict()
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get profile error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@auth_bp.route('/check-user-status', methods=['POST'])
def check_user_status():
    """Check if user exists and their verification status"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Email is required'
            }), 400
        
        email = data['email'].strip().lower()
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 404,
                'message': 'User not found',
                'data': {
                    'exists': False,
                    'email': email
                }
            }), 404
        
        return jsonify({
            'status': 200,
            'message': 'User status retrieved',
            'data': {
                'exists': True,
                'email': user.email,
                'full_name': user.full_name,
                'is_verified': user.is_verified,
                'can_resend_verification': not user.is_verified
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Check user status error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500 