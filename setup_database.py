#!/usr/bin/env python3
"""
Database setup script for Resume NER Parser
This script creates all necessary database tables
"""

import os
import sys
from flask import Flask
from models import db, User, Resume, VerificationCode
import config

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Initialize database
    db.init_app(app)
    
    return app

def setup_database():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print table information
            print("\n📊 Created tables:")
            print("  - users (stores user accounts)")
            print("  - verification_codes (stores email verification codes)")
            print("  - resumes (stores uploaded resumes and extracted entities)")
            
            print(f"\n🔗 Database URL: {config.SQLALCHEMY_DATABASE_URI}")
            print("\n🚀 Database setup complete! You can now start the application.")
            
        except Exception as e:
            print(f"❌ Error creating database tables: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    print("🔧 Setting up Resume NER Parser database...")
    setup_database() 