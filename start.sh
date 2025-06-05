#!/bin/bash

# Resume NER Backend Start Script
echo "Starting Resume NER Backend..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Make migrations and setup database
python setup_database.py

# Start the Flask application
python main.py 