# Resume NER Parser - Backend

A Flask-based backend service for extracting named entities from resume PDFs using a fine-tuned BERT model.

## Features

- 🤖 **AI-Powered NER**: Fine-tuned BERT model for resume entity extraction
- 📧 **Email Verification**: Secure user registration with email verification
- 🔐 **JWT Authentication**: Secure token-based authentication
- 📄 **PDF Processing**: Extract text and entities from PDF resumes
- 🗄️ **PostgreSQL Database**: Robust data storage
- 📊 **Entity Types**: Extract names, skills, companies, locations, degrees, etc.

## Technology Stack

- **Framework**: Flask
- **Database**: PostgreSQL
- **AI Model**: Fine-tuned BERT (compressed to 208MB)
- **Authentication**: JWT + Email verification
- **Email**: Flask-Mail with SMTP
- **PDF Processing**: pdfminer.six

## Quick Start

### 1. Environment Setup

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key

# Email (Gmail example)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Optional
DEBUG=False
PORT=8002
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database

```bash
python setup_database.py
```

### 4. Run the Server

```bash
python main.py
```

## Deployment on Render

### Prerequisites

1. **PostgreSQL Database**: Create a PostgreSQL database on Render
2. **Git LFS**: Install Git LFS for the large model file
3. **Email Account**: Gmail with app password (or other SMTP)

### Steps

1. **Prepare Repository**:
   ```bash
   git lfs install
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create Web Service** on Render:
   - Connect your GitHub repository
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

3. **Set Environment Variables**:
   ```
   DATABASE_URL=<your-render-postgres-url>
   JWT_SECRET_KEY=<secure-random-string>
   MAIL_USERNAME=<your-email>
   MAIL_PASSWORD=<your-app-password>
   MAIL_DEFAULT_SENDER=<your-email>
   DEBUG=False
   ```

4. **Deploy**: The service will automatically deploy

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify-email` - Email verification
- `POST /auth/resend-verification` - Resend verification code

### Resume Processing
- `POST /minedata` - Upload and process resume PDF
- `GET /api/resumes` - Get user's resumes
- `GET /api/resumes/<id>` - Get specific resume

## Model Information

- **Original Size**: 415MB
- **Compressed Size**: 208MB (50% reduction)
- **Compression Method**: Mixed precision (float16/float32)
- **Entity Types**: NAME, DESIGNATION, EMAIL, LOCATION, DEGREE, COLLEGE NAME, COMPANY, SKILLS

## Git LFS Setup

The compressed model file is tracked with Git LFS:

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "*.pt"
git add .gitattributes
git add compressed_resume_ner_model_v2.pt
git commit -m "Add model with LFS"
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes |
| `MAIL_USERNAME` | SMTP username | Yes |
| `MAIL_PASSWORD` | SMTP password/app password | Yes |
| `MAIL_DEFAULT_SENDER` | Default sender email | Yes |
| `DEBUG` | Enable debug mode | No (default: False) |
| `PORT` | Server port | No (default: 8002) |

## Development

### Running Tests
```bash
# Test email configuration
python -c "from email_service import *; print('Email service working!')"
```

### Model Compression
The BERT model has been compressed using mixed precision to reduce size while maintaining accuracy.

## Security Notes

- Always use environment variables for sensitive data
- Use app passwords for Gmail (not regular passwords)
- Keep JWT secret key secure and random
- Set DEBUG=False in production

## License

This project is for educational purposes. 