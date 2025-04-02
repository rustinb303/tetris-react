
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

if [ -z "$1" ]; then
    TOPIC="Quantum Computing"
else
    TOPIC="$1"
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python mcp_crewai_integration.py "$TOPIC"
