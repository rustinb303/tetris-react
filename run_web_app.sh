#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v "^#" | xargs)
else
    echo "Warning: .env file not found. Make sure your API keys are set in the environment."
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required packages if not already installed
pip install flask flask-socketio langchain_groq

# Run the web application
python web_app.py
