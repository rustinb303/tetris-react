
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Make sure your API keys are set in the environment."
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python web_app.py
