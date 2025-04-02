# CrewAI Multi-Agent Project

A flexible framework for creating and managing multi-agent systems using CrewAI. This project allows you to easily configure and orchestrate multiple AI agents that can work together as a group.

## Features

- **Multiple Agent Support**: Create and manage multiple agents with different roles and capabilities
- **Model Flexibility**: Use different LLM models for different agents
- **Custom Prompts**: Configure each agent with custom system prompts
- **Agent Communication**: Enable agents to communicate and collaborate with each other
- **Subgroup Support**: Create subgroups of agents that can work together on specific tasks
- **Configuration-Based**: Define your agent system using YAML or JSON configuration

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/crewai-multi-agent-project.git
cd crewai-multi-agent-project
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"  # On Windows: set OPENAI_API_KEY=your-api-key-here
```

## Usage

### Quick Start

Run the simple example to see the system in action:

```bash
# Edit simple_example.py to add your OpenAI API key first
python simple_example.py
```

### Using Configuration Files

1. Create a YAML or JSON configuration file (see `example_config.yaml` for reference)
2. Run the system using the configuration file:
```bash
python -m src.main --config your_config.yaml
```

Or use the test_run.py script:
```bash
# Edit test_run.py to add your OpenAI API key first
python test_run.py example_config.yaml
```

### Programmatic Usage

You can also create and run crews programmatically:

```python
import os
from src.config.config import AgentConfig, TaskConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Create agent configurations
researcher_config = AgentConfig(
    name="Researcher",
    role="Senior Research Analyst",
    goal="Find comprehensive information on the given topic",
    backstory="You are an expert researcher with a knack for finding relevant information quickly.",
    model="gpt-4"
)

# Create agents
agents = {
    "researcher": AgentFactory.create_agent(researcher_config)
}

# Create task configurations
research_task_config = TaskConfig(
    name="Research Topic",
    description="Research the given topic thoroughly and compile relevant information",
    expected_output="A comprehensive collection of information on the topic",
    agent="researcher"
)

# Create tasks
tasks = TaskFactory.create_tasks_from_config(
    {"research": research_task_config},
    {name: agent for name, agent in agents.items()}
)

# Create crew configuration
crew_config = CrewConfig(
    name="Research Crew",
    description="A crew that researches a topic",
    agents={name: agent.config for name, agent in agents.items()},
    tasks={name: task.config for name, task in tasks.items()},
    process="sequential"
)

# Create crew manager
crew_manager = CrewManager(crew_config, agents, tasks)

# Run the crew
result = crew_manager.run()
print(f"Result: {result}")
```

## Configuration

### Agent Configuration

```yaml
agents:
  researcher:
    name: "Researcher"
    role: "Senior Research Analyst"
    goal: "Find comprehensive information on the given topic"
    backstory: "You are an expert researcher with a knack for finding relevant information quickly."
    verbose: true
    allow_delegation: true
    model: "gpt-4"
    max_iterations: 15
    temperature: 0.7
    system_prompt: "You are a meticulous researcher who leaves no stone unturned."
    human_input_mode: "NEVER"
    tools: []
```

### Task Configuration

```yaml
tasks:
  research:
    name: "Research Topic"
    description: "Research the given topic thoroughly and compile relevant information"
    expected_output: "A comprehensive collection of information on the topic"
    agent: "researcher"
    async_execution: false
```

### Subgroup Configuration

```yaml
subgroups:
  research_team:
    name: "Research Team"
    agents: ["researcher", "analyst"]
    tasks: ["research", "analyze"]
    process: "sequential"  # Only 'sequential' and 'hierarchical' are supported
```

### Crew Configuration

```yaml
name: "Research and Analysis Crew"
description: "A crew that researches a topic and provides analysis"
process: "sequential"  # Only 'sequential' and 'hierarchical' are supported
verbose: true
memory: true
cache: false
step_callback: false
```

## Project Structure

```
crewai-multi-agent-project/
├── src/
│   ├── agents/
│   │   ├── agent_factory.py
│   │   └── base_agent.py
│   ├── config/
│   │   └── config.py
│   ├── models/
│   │   └── crew_manager.py
│   ├── tasks/
│   │   ├── base_task.py
│   │   └── task_factory.py
│   ├── utils/
│   │   ├── config_loader.py
│   │   └── tool_registry.py
│   └── main.py
├── example.py
├── example_config.yaml
├── simple_example.py
├── test_run.py
├── test_structure.py
├── requirements.txt
└── setup.py
```

## Testing

Run the structure test to verify the system is set up correctly:

```bash
python test_structure.py
```

## Multi-Model Support

This project supports multiple LLM providers:

- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-Turbo, etc.
- **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, etc.
- **Google**: Gemini 1.5 Pro, Gemini 2.0 Flash, etc.
- **xAI**: Grok-1, Grok-2, etc.

To use a specific model, specify it in the format `provider:model` in your agent configuration:

```yaml
agents:
  researcher:
    model: "openai:gpt-4"  # OpenAI model
  writer:
    model: "anthropic:claude-3-sonnet"  # Anthropic model
  editor:
    model: "gemini:gemini-1.5-pro"  # Google Gemini model
  critic:
    model: "grok:grok-2"  # xAI Grok model
```

## Database and External Tool Integration

This project includes integrations with various external tools and databases:

### Supabase Integration

Agents can read and write data to Supabase databases:

```python
from src.utils.database_tools import SupabaseTool

# Create a Supabase tool
supabase_tool = SupabaseTool(
    table_name="your_table",
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY")
)

# Use the tool in your agent
agent = Agent(
    name="DataAgent",
    tools=[supabase_tool],
    # other configuration...
)
```

To run a demo with Supabase integration:

```bash
./run_demo3.sh "Your topic"
```

### Google Sheets Integration

Agents can also interact with Google Sheets:

```python
from src.utils.spreadsheet_tools import GoogleSheetsTools

# Create a Google Sheets tool
sheets_tool = GoogleSheetsTools(
    credentials_path="path/to/credentials.json",
    spreadsheet_id="your-spreadsheet-id"
)

# Use the tool in your agent
agent = Agent(
    name="SpreadsheetAgent",
    tools=[sheets_tool],
    # other configuration...
)
```

## Model Context Protocol (MCP)

This project includes an implementation of the [Model Context Protocol](https://modelcontextprotocol.io/) for standardized access to external data sources:

### File System Integration

```python
from src.mcp import MCPClient
from src.mcp.integrations import FileSystemServer
from mcp_crewai_integration import MCPFileTool

# Set up MCP
client = MCPClient()
fs_server = FileSystemServer(name="filesystem")
client.register_server(fs_server)

# Create MCP tool for CrewAI agents
file_tool = MCPFileTool(client)

# Use the tool in your agents
agent = Agent(
    name="FileAgent",
    tools=[file_tool],
    # other configuration...
)
```

### Google Drive Integration

```python
from src.mcp.integrations import GoogleDriveServer
from mcp_crewai_integration import MCPGoogleDriveTool

# Set up MCP with Google Drive
drive_server = GoogleDriveServer(
    name="googledrive",
    credentials_path="path/to/credentials.json"
)
client.register_server(drive_server)

# Create MCP Google Drive tool
drive_tool = MCPGoogleDriveTool(client)

# Use the tool in your agents
agent = Agent(
    name="DriveAgent",
    tools=[drive_tool],
    # other configuration...
)
```

To run a demo with MCP integration:

```bash
./run_mcp_demo.sh "Your topic"
```

## API Keys

To use multiple model providers, you need to set up API keys in a `.env` file:

```
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API Key (Claude models)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google API Key (Gemini models)
GOOGLE_API_KEY=your-google-api-key-here

# xAI API Key (Grok models)
GROK_API_KEY=your-grok-api-key-here
```

## Notes

- This project requires CrewAI version 0.108.0 or higher
- The Process enum in CrewAI only supports 'sequential' and 'hierarchical' options
- You must provide valid API keys for the model providers you want to use

## License

MIT
