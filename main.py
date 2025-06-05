from flask import Flask, request, jsonify
import config
import logging
import os
import minegold
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from ner_model import extract_resume_entities
from models import db, Resume, User
from email_service import mail
from auth_routes import auth_bp
from resume_routes import resume_bp
import warnings
warnings.filterwarnings('ignore')


app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

# Initialize extensions
db.init_app(app)
mail.init_app(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(resume_bp, url_prefix='/api')

# Configuration
RAW_FOLDER = config.RAW_FOLDER
CLEAN_FOLDER = config.CLEAN_FOLDER
LOG_FILE = config.LOG_FILE
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/minedata', methods=['POST'])
@jwt_required()
def process_file():
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'No file part in request'
            }), 400

        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 400,
                'message': 'Bad Request',
                'error': 'No selected file'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'status': 415,
                'message': 'Unsupported Media Type',
                'error': 'Only PDF files are allowed'
            }), 415

        filename = secure_filename(file.filename)
        filepath = os.path.join(RAW_FOLDER, filename)
        
        os.makedirs(RAW_FOLDER, exist_ok=True)
        
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({
                'status': 500,
                'message': 'File Save Error',
                'error': f'Could not save file: {str(e)}'
            }), 500

        try:
            extracted_text = minegold.process_pdf(filepath)
            
            if not extracted_text or len(extracted_text) < 50:
                return jsonify({
                    'status': 422,
                    'message': 'Unprocessable Content',
                    'error': 'PDF is either empty or contains too little text',
                    'character_count': len(extracted_text) if extracted_text else 0
                }), 422
            
            # Extract entities using compressed NER model
            entities = extract_resume_entities(extracted_text, model_path="compressed_resume_ner_model_v2.pt")
            
            # Get current user
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'status': 401,
                    'message': 'Unauthorized',
                    'error': 'User not found'
                }), 401
            
            # Read file data for storage
            file_data = None
            try:
                with open(filepath, 'rb') as f:
                    import base64
                    file_content = f.read()
                    file_data = f"data:application/pdf;base64,{base64.b64encode(file_content).decode('utf-8')}"
            except Exception as e:
                logging.warning(f"Could not read file for storage: {str(e)}")
            
            # Save resume to database
            resume = Resume(
                user_id=user_id,
                filename=filename,
                file_data=file_data,
                entities=entities
            )
            
            db.session.add(resume)
            db.session.commit()
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except Exception as e:
                logging.warning(f"Could not remove uploaded file: {str(e)}")
                
            return jsonify({
                'status': 200,
                'message': 'Success',
                'entities': entities,
                'resume_id': resume.id
            })

        except Exception as e:
            logger.error(f'Processing error: {str(e)}', exc_info=True)
            return jsonify({
                'status': 500,
                'message': 'PDF Processing Failed',
                'error': f'Could not process PDF: {str(e)}'
            }), 500

    except Exception as e:
        logger.critical(f'Server error: {str(e)}', exc_info=True)
        return jsonify({
            'status': 500,
            'message': 'Internal Server Error',
            'error': 'An unexpected error occurred'
        }), 500

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
    
    logger.info(f"Starting application on port {config.PORT}")
    app.run(host="0.0.0.0", debug=config.DEBUG, port=config.PORT)