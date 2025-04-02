
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded environment variables from .env file"
else
    echo "Warning: .env file not found. Make sure your API keys are set in the environment."
fi

source venv/bin/activate

if [ -z "$1" ]; then
    python demo2.py
else
    python demo2.py "$1"
fi
