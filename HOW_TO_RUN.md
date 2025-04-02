# How to Run the CrewAI Multi-Agent Demo

This guide will help you run the CrewAI multi-agent system demo using your OpenAI API key.

## Prerequisites

- An OpenAI API key
- Python 3.10 or higher

## Option 1: Using the Shell Script

1. Run the demo with your API key:

```bash
./run_demo.sh your-api-key-here
```

2. Optionally, specify a topic to research:

```bash
./run_demo.sh your-api-key-here "quantum computing"
```

## Option 2: Manual Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package:

```bash
pip install -e .
```

3. Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"  # On Windows: set OPENAI_API_KEY=your-api-key-here
```

4. Run the demo:

```bash
python demo.py
```

5. Optionally, specify a topic to research:

```bash
python demo.py "quantum computing"
```

## What to Expect

The demo will:
1. Create a Researcher agent and a Writer agent
2. Assign research and writing tasks
3. Run the agents in sequence
4. Output the final result (a summary of the researched topic)

The process may take a few minutes to complete as the agents work on their tasks.
