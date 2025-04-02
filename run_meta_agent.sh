
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

if [ -z "$1" ]; then
    echo "Usage: ./run_meta_agent.sh \"Your task description\" [output_filename.py]"
    echo "Example: ./run_meta_agent.sh \"Create agents for jailbreak detection\" jailbreak.py"
    exit 1
fi

if [ -z "$2" ]; then
    python meta_agent_generator.py "$1"
else
    python meta_agent_generator.py "$1" "$2"
fi
