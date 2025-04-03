"""Demo script for the CrewAI multi-agent system with multiple LLM providers."""
import os
import sys
from pathlib import Path

from src.config.config import AgentConfig, TaskConfig, CrewConfig, SubgroupConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.env_loader import load_env_vars

def run_poetry_demo(theme="nature"):
    """
    Run a poetry creation demo with multiple LLM providers.
    
    Args:
        theme: The theme for the poem
    """
    load_env_vars()
    
    print(f"Running poetry demo with theme: {theme}")
    print("Creating agents with different LLM providers...")
    
    idea_generator_config = AgentConfig(
        name="IdeaGenerator",
        role="Creative Thinker",
        goal=f"Generate ONE brief creative idea for a poem about {theme}",
        backstory="You are a visionary thinker who excels at generating unique and inspiring ideas.",
        model="openai:gpt-4o-mini"  # OpenAI model
    )
    
    poet_config = AgentConfig(
        name="Poet",
        role="Master Poet",
        goal=f"Create a SHORT poem (4 lines max) about {theme} based on the provided idea",
        backstory="You are a skilled poet with a talent for crafting evocative and moving poetry.",
        model="anthropic:claude-3-sonnet"  # Anthropic model
    )
    
    editor_config = AgentConfig(
        name="Editor",
        role="Poetry Editor",
        goal=f"Make minor refinements to the short poem about {theme} to improve it",
        backstory="You are a meticulous editor with an eye for detail and a passion for perfection.",
        model="gemini:gemini-1.5-pro"  # Google Gemini model
    )
    
    critic_config = AgentConfig(
        name="Critic",
        role="Literary Critic",
        goal=f"Provide BRIEF constructive feedback (2-3 sentences max) on the poem about {theme}",
        backstory="You are an insightful critic who can identify strengths and areas for improvement.",
        model="grok:grok-2"  # xAI Grok model
    )
    
    agents = {
        "idea_generator": AgentFactory.create_agent(idea_generator_config),
        "poet": AgentFactory.create_agent(poet_config),
        "editor": AgentFactory.create_agent(editor_config),
        "critic": AgentFactory.create_agent(critic_config)
    }
    
    print("Creating tasks...")
    generate_ideas_config = TaskConfig(
        name=f"Generate Ideas for {theme} Poem",
        description=f"Generate creative ideas, concepts, and imagery for a poem about {theme}",
        expected_output=f"A list of creative ideas, concepts, and imagery for a poem about {theme}",
        agent="idea_generator"
    )
    
    write_poem_config = TaskConfig(
        name=f"Write {theme} Poem",
        description=f"Write a beautiful poem about {theme} based on the provided ideas",
        expected_output=f"A draft poem about {theme}",
        agent="poet"
    )
    
    edit_poem_config = TaskConfig(
        name=f"Edit {theme} Poem",
        description=f"Refine and polish the poem about {theme} to make it more impactful",
        expected_output=f"A refined poem about {theme}",
        agent="editor"
    )
    
    critique_poem_config = TaskConfig(
        name=f"Critique {theme} Poem",
        description=f"Provide constructive feedback on the poem about {theme}",
        expected_output=f"Constructive feedback on the poem about {theme}",
        agent="critic"
    )
    
    tasks = TaskFactory.create_tasks_from_config(
        {
            "generate_ideas": generate_ideas_config,
            "write_poem": write_poem_config,
            "edit_poem": edit_poem_config,
            "critique_poem": critique_poem_config
        },
        {name: agent for name, agent in agents.items()}
    )
    
    creation_subgroup_config = SubgroupConfig(
        name="Creation Team",
        agents=["idea_generator", "poet"],
        tasks=["generate_ideas", "write_poem"],
        process="sequential"
    )
    
    refinement_subgroup_config = SubgroupConfig(
        name="Refinement Team",
        agents=["editor", "critic"],
        tasks=["edit_poem", "critique_poem"],
        process="sequential"
    )
    
    print("Creating crew...")
    crew_config = CrewConfig(
        name=f"{theme.title()} Poetry Crew",
        description=f"A crew that creates a poem about {theme}",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        subgroups={
            "creation": creation_subgroup_config,
            "refinement": refinement_subgroup_config
        },
        process="sequential"
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    crew_manager.create_all_subgroups()
    
    print(f"\nRunning Creation Team (Idea Generator + Poet)...")
    print("This may take a few minutes...\n")
    creation_result = crew_manager.run_subgroup("Creation Team")
    
    print("\n" + "="*50)
    print(f"CREATION TEAM RESULT: {creation_result}")
    print("="*50)
    
    print(f"\nRunning Refinement Team (Editor + Critic)...")
    print("This may take a few minutes...\n")
    refinement_result = crew_manager.run_subgroup("Refinement Team")
    
    print("\n" + "="*50)
    print(f"REFINEMENT TEAM RESULT: {refinement_result}")
    print("="*50)
    
    print("\n" + "="*50)
    print(f"FINAL POEM ABOUT {theme.upper()}:")
    print(refinement_result)
    print("="*50)
    
    return refinement_result

if __name__ == "__main__":
    if os.environ.get("OPENROUTER_API_KEY"):
        print("Using OpenRouter for all model providers")
    else:
        required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GROK_API_KEY"]
        missing_keys = [key for key in required_keys if not os.environ.get(key)]
        
        if missing_keys:
            print("Error: OpenRouter API key is missing and the following direct API keys are missing:")
            for key in missing_keys:
                print(f"  - {key}")
            print("\nPlease set either OPENROUTER_API_KEY or all individual API keys in your .env file.")
            print("See .env.example for the required format.")
            sys.exit(1)
    
    theme = sys.argv[1] if len(sys.argv) > 1 else "nature"
    
    run_poetry_demo(theme)
