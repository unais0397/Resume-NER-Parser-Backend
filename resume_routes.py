from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Resume, User
import logging
from datetime import datetime

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/resumes', methods=['GET'])
@jwt_required()
def get_user_resumes():
    """Get all resumes for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 404,
                'message': 'User not found',
                'error': 'User not found'
            }), 404
        
        resumes = Resume.query.filter_by(user_id=user_id).order_by(Resume.created_at.desc()).all()
        
        return jsonify({
            'status': 200,
            'message': 'Resumes retrieved successfully',
            'data': {
                'resumes': [resume.to_dict() for resume in resumes]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get resumes error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@resume_bp.route('/resumes', methods=['POST'])
@jwt_required()
def save_resume():
    """Save a new resume for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 404,
                'message': 'User not found',
                'error': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('filename'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Filename is required'
            }), 400
        
        if not data.get('entities'):
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'Entities data is required'
            }), 400
        
        # Create new resume
        resume = Resume(
            user_id=user_id,
            filename=data['filename'],
            file_data=data.get('file_data'),  # Base64 PDF data (optional)
            entities=data['entities']
        )
        
        db.session.add(resume)
        db.session.commit()
        
        return jsonify({
            'status': 201,
            'message': 'Resume saved successfully',
            'data': {
                'resume': resume.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Save resume error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@resume_bp.route('/resumes/<resume_id>', methods=['GET'])
@jwt_required()
def get_resume(resume_id):
    """Get a specific resume by ID for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        
        if not resume:
            return jsonify({
                'status': 404,
                'message': 'Resume not found',
                'error': 'Resume not found or you do not have permission to access it'
            }), 404
        
        # Include file_data in response for PDF viewing
        resume_data = resume.to_dict()
        resume_data['file_data'] = resume.file_data
        
        return jsonify({
            'status': 200,
            'message': 'Resume retrieved successfully',
            'data': {
                'resume': resume_data
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Get resume error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@resume_bp.route('/resumes/<resume_id>', methods=['DELETE'])
@jwt_required()
def delete_resume(resume_id):
    """Delete a specific resume by ID for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        
        if not resume:
            return jsonify({
                'status': 404,
                'message': 'Resume not found',
                'error': 'Resume not found or you do not have permission to delete it'
            }), 404
        
        db.session.delete(resume)
        db.session.commit()
        
        return jsonify({
            'status': 200,
            'message': 'Resume deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Delete resume error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

@resume_bp.route('/resumes/<resume_id>', methods=['PUT'])
@jwt_required()
def update_resume(resume_id):
    """Update a specific resume by ID for the authenticated user"""
    try:
        user_id = get_jwt_identity()
        
        resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
        
        if not resume:
            return jsonify({
                'status': 404,
                'message': 'Resume not found',
                'error': 'Resume not found or you do not have permission to update it'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'filename' in data:
            resume.filename = data['filename']
        if 'entities' in data:
            resume.entities = data['entities']
        if 'file_data' in data:
            resume.file_data = data['file_data']
        
        resume.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 200,
            'message': 'Resume updated successfully',
            'data': {
                'resume': resume.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Update resume error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500 