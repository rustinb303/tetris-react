"""Meta-agent system that interviews users and generates specialized agent configurations."""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.config.config import AgentConfig, TaskConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.env_loader import load_env_vars


def get_llm(provider: str, model: str):
    """
    Get a language model based on provider and model name.
    
    Args:
        provider: The provider name (openai, anthropic, gemini, grok)
        model: The model name
        
    Returns:
        A language model instance
    """
    load_env_vars()
    
    if provider.lower() == "openai":
        return ChatOpenAI(model=model, temperature=0.7)
    elif provider.lower() == "anthropic":
        return ChatAnthropic(model=model, temperature=0.7)
    elif provider.lower() == "gemini":
        return ChatGoogleGenerativeAI(model=model, temperature=0.7)
    elif provider.lower() == "grok":
        return ChatGroq(model=model, temperature=0.7)
    else:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


class MetaAgentGenerator:
    """
    A system that uses AI agents to interview users and generate specialized agent configurations.
    """
    
    def __init__(self, default_provider: str = "openai", default_model: str = "gpt-4o-mini"):
        """
        Initialize the meta-agent generator.
        
        Args:
            default_provider: Default LLM provider
            default_model: Default model name
        """
        self.default_provider = default_provider
        self.default_model = default_model
        self.user_requirements = {}
        self.agent_designs = {}
        self.task_designs = {}
        self.generated_code = ""
        
        load_env_vars()
    
    def create_interviewer_agent(self) -> Agent:
        """
        Create an agent that interviews the user about their requirements.
        
        Returns:
            An interviewer agent
        """
        return Agent(
            role="Requirements Interviewer",
            goal="Gather detailed requirements for the AI agent system",
            backstory="""You are an expert AI system designer who knows how to ask 
            the right questions to understand what a user needs. You excel at 
            extracting specific requirements and use cases.""",
            verbose=True,
            llm=get_llm(self.default_provider, self.default_model),
            tools=[]
        )
    
    def create_architect_agent(self) -> Agent:
        """
        Create an agent that designs the agent architecture based on requirements.
        
        Returns:
            An architect agent
        """
        return Agent(
            role="AI System Architect",
            goal="Design an optimal multi-agent system architecture",
            backstory="""You are a brilliant AI system architect who can design 
            the perfect combination of specialized agents to solve complex problems. 
            You know how to break down tasks and assign them to the right agents.""",
            verbose=True,
            llm=get_llm(self.default_provider, self.default_model),
            tools=[]
        )
    
    def create_coder_agent(self) -> Agent:
        """
        Create an agent that generates code for the designed system.
        
        Returns:
            A coder agent
        """
        return Agent(
            role="AI System Coder",
            goal="Generate clean, functional code for the designed agent system",
            backstory="""You are an expert Python developer specializing in AI systems. 
            You can translate designs into clean, well-structured code that follows 
            best practices and is easy to understand and maintain.""",
            verbose=True,
            llm=get_llm(self.default_provider, self.default_model),
            tools=[]
        )
    
    def create_evaluator_agent(self) -> Agent:
        """
        Create an agent that evaluates the generated code.
        
        Returns:
            An evaluator agent
        """
        return Agent(
            role="Code Quality Evaluator",
            goal="Ensure the generated code is high-quality and meets requirements",
            backstory="""You are a meticulous code reviewer with an eye for detail. 
            You can spot potential issues, suggest improvements, and ensure the code 
            meets all requirements and follows best practices.""",
            verbose=True,
            llm=get_llm(self.default_provider, self.default_model),
            tools=[]
        )
    
    def interview_user(self, task_description: str) -> Dict[str, Any]:
        """
        Interview the user about their requirements.
        
        Args:
            task_description: Initial task description from the user
            
        Returns:
            Dictionary of user requirements
        """
        interviewer = self.create_interviewer_agent()
        
        interview_task = Task(
            description=f"""
            Interview the user about their requirements for: "{task_description}"
            
            Ask specific questions to understand:
            1. What is the main goal of the agent system?
            2. What specific tasks should the agents perform?
            3. What types of agents would be most effective for this task?
            4. What tools or external resources might the agents need?
            5. How should the agents collaborate or share information?
            6. What output format is expected from the system?
            7. Are there any specific constraints or requirements?
            
            Based on the answers, create a structured JSON object with the following fields:
            - main_goal: The primary goal of the system
            - tasks: List of specific tasks to perform
            - agent_types: List of agent types that would be effective
            - tools_needed: List of tools or resources needed
            - collaboration_method: How agents should collaborate
            - output_format: Expected output format
            - constraints: Any specific constraints or requirements
            
            The user has provided this initial description: "{task_description}"
            
            Analyze this description and ask follow-up questions to fill in any gaps.
            Return your final analysis as a JSON object.
            """,
            agent=interviewer,
            expected_output="A JSON object containing detailed user requirements"
        )
        
        print("\n" + "="*50)
        print("🤖 INTERVIEWER AGENT")
        print("="*50)
        print("I'll ask you some questions to understand your requirements better.")
        print("Please provide detailed answers to help me design the perfect agent system for you.")
        print("="*50 + "\n")
        
        
        result = interview_task.execute_sync()
        
        try:
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            json_str = result[json_start:json_end]
            requirements = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing requirements: {e}")
            requirements = {
                "main_goal": task_description,
                "tasks": ["Analyze the task", "Generate solution"],
                "agent_types": ["Analyzer", "Generator"],
                "tools_needed": [],
                "collaboration_method": "Sequential",
                "output_format": "Text report",
                "constraints": []
            }
        
        self.user_requirements = requirements
        return requirements
    
    def design_agents(self, requirements: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Design agent configurations based on requirements.
        
        Args:
            requirements: User requirements
            
        Returns:
            Dictionary of agent configurations
        """
        architect = self.create_architect_agent()
        
        design_task = Task(
            description=f"""
            Design a multi-agent system based on these requirements:
            {json.dumps(requirements, indent=2)}
            
            For each agent, specify:
            1. Name: A short, descriptive name
            2. Role: The specific role this agent plays
            3. Goal: What this agent aims to achieve
            4. Backstory: A brief backstory that shapes the agent's perspective
            5. Tools: Any specific tools this agent should use
            6. Model: The LLM model this agent should use (provider:model format)
            
            Also, design the tasks that each agent should perform, including:
            1. Name: A short, descriptive name
            2. Description: What the task involves
            3. Expected output: What the task should produce
            4. Agent: Which agent performs this task
            
            Finally, specify how these agents should collaborate:
            1. Process: Sequential, hierarchical, or parallel
            2. Information sharing: How agents share information
            
            Return your design as a JSON object with these sections:
            - agents: Dictionary of agent configurations
            - tasks: Dictionary of task configurations
            - process: Collaboration process details
            """,
            agent=architect,
            expected_output="A JSON object containing agent and task designs"
        )
        
        print("\n" + "="*50)
        print("🤖 ARCHITECT AGENT")
        print("="*50)
        print("Designing the optimal agent system based on your requirements...")
        print("="*50 + "\n")
        
        result = design_task.execute_sync()
        
        try:
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            json_str = result[json_start:json_end]
            design = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing design: {e}")
            design = {
                "agents": {
                    "analyzer": {
                        "name": "Analyzer",
                        "role": "Data Analyzer",
                        "goal": f"Analyze {requirements.get('main_goal', 'the task')}",
                        "backstory": "You are an expert analyst.",
                        "tools": [],
                        "model": "openai:gpt-4o-mini"
                    },
                    "generator": {
                        "name": "Generator",
                        "role": "Solution Generator",
                        "goal": f"Generate solutions for {requirements.get('main_goal', 'the task')}",
                        "backstory": "You are a creative problem solver.",
                        "tools": [],
                        "model": "openai:gpt-4o-mini"
                    }
                },
                "tasks": {
                    "analyze": {
                        "name": "Analyze Task",
                        "description": f"Analyze {requirements.get('main_goal', 'the task')}",
                        "expected_output": "Analysis report",
                        "agent": "analyzer"
                    },
                    "generate": {
                        "name": "Generate Solution",
                        "description": f"Generate solutions for {requirements.get('main_goal', 'the task')}",
                        "expected_output": "Solution report",
                        "agent": "generator"
                    }
                },
                "process": {
                    "type": "sequential",
                    "information_sharing": "Results are passed between tasks"
                }
            }
        
        self.agent_designs = design.get("agents", {})
        self.task_designs = design.get("tasks", {})
        self.process_design = design.get("process", {"type": "sequential"})
        
        return design
    
    def generate_code(self, design: Dict[str, Any], output_filename: str) -> str:
        """
        Generate code for the designed agent system.
        
        Args:
            design: Agent and task design
            output_filename: Name of the output Python file
            
        Returns:
            Generated code as a string
        """
        coder = self.create_coder_agent()
        
        code_task = Task(
            description=f"""
            Generate a complete Python file implementing this agent system design:
            {json.dumps(design, indent=2)}
            
            The file should be named {output_filename} and should:
            1. Import all necessary libraries
            2. Define all agents according to the design
            3. Define all tasks according to the design
            4. Create a crew with the specified process
            5. Include a main function that runs the system
            6. Include proper error handling and environment variable loading
            7. Be well-commented and follow PEP 8 style guidelines
            8. Be completely self-contained and runnable
            
            Use the CrewAI framework and follow the patterns from the existing codebase.
            The code should be production-ready and include proper documentation.
            
            Return only the complete Python code without any additional explanation.
            """,
            agent=coder,
            expected_output=f"Complete Python code for {output_filename}"
        )
        
        print("\n" + "="*50)
        print("🤖 CODER AGENT")
        print("="*50)
        print(f"Generating code for {output_filename}...")
        print("="*50 + "\n")
        
        result = code_task.execute_sync()
        
        if "```python" in result:
            code_start = result.find("```python") + 10
            code_end = result.rfind("```")
            code = result[code_start:code_end].strip()
        elif "```" in result:
            code_start = result.find("```") + 3
            code_end = result.rfind("```")
            code = result[code_start:code_end].strip()
        else:
            code = result.strip()
        
        self.generated_code = code
        return code
    
    def evaluate_code(self, code: str, requirements: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate the generated code against requirements.
        
        Args:
            code: Generated code
            requirements: User requirements
            
        Returns:
            Tuple of (is_approved, feedback)
        """
        evaluator = self.create_evaluator_agent()
        
        evaluation_task = Task(
            description=f"""
            Evaluate this generated code against the original requirements:
            
            REQUIREMENTS:
            {json.dumps(requirements, indent=2)}
            
            CODE:
            ```python
            {code}
            ```
            
            Assess the code for:
            1. Functionality: Does it implement all required features?
            2. Quality: Is it well-structured and maintainable?
            3. Completeness: Does it handle all aspects of the requirements?
            4. Best practices: Does it follow Python and AI best practices?
            5. Potential issues: Are there any bugs or edge cases?
            
            Provide specific feedback on what works well and what could be improved.
            Conclude with an overall assessment: APPROVED or NEEDS REVISION.
            
            If NEEDS REVISION, clearly explain what changes are needed.
            """,
            agent=evaluator,
            expected_output="Detailed code evaluation with approval status"
        )
        
        print("\n" + "="*50)
        print("🤖 EVALUATOR AGENT")
        print("="*50)
        print("Evaluating the generated code...")
        print("="*50 + "\n")
        
        result = evaluation_task.execute_sync()
        
        is_approved = "APPROVED" in result.upper() and "NEEDS REVISION" not in result
        
        return is_approved, result
    
    def save_code(self, code: str, filename: str) -> str:
        """
        Save the generated code to a file.
        
        Args:
            code: Generated code
            filename: Output filename
            
        Returns:
            Path to the saved file
        """
        output_path = os.path.join(os.getcwd(), filename)
        
        with open(output_path, "w") as f:
            f.write(code)
        
        os.chmod(output_path, 0o755)
        
        print(f"\nCode saved to: {output_path}")
        return output_path
    
    def create_run_script(self, filename: str) -> str:
        """
        Create a shell script to run the generated code.
        
        Args:
            filename: Python file to run
            
        Returns:
            Path to the run script
        """
        script_name = f"run_{os.path.splitext(filename)[0]}.sh"
        script_path = os.path.join(os.getcwd(), script_name)
        
        script_content = f"""#!/bin/bash

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python {filename} "$@"
"""
        
        with open(script_path, "w") as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        print(f"Run script created: {script_path}")
        return script_path
    
    def generate_agent_system(self, task_description: str, output_filename: str) -> Dict[str, Any]:
        """
        Generate a complete agent system based on a task description.
        
        Args:
            task_description: Description of the task
            output_filename: Name of the output Python file
            
        Returns:
            Dictionary with paths to generated files and evaluation results
        """
        print("\n" + "="*80)
        print(f"🤖 META-AGENT SYSTEM: GENERATING AGENT SYSTEM FOR '{task_description}'")
        print("="*80 + "\n")
        
        requirements = self.interview_user(task_description)
        
        design = self.design_agents(requirements)
        
        code = self.generate_code(design, output_filename)
        
        is_approved, evaluation = self.evaluate_code(code, requirements)
        
        if is_approved:
            code_path = self.save_code(code, output_filename)
            run_script_path = self.create_run_script(output_filename)
        else:
            print("\n" + "="*50)
            print("⚠️ CODE NEEDS REVISION")
            print("="*50)
            print(evaluation)
            print("\nPlease review the feedback and try again.")
            code_path = None
            run_script_path = None
        
        return {
            "requirements": requirements,
            "design": design,
            "code": code,
            "evaluation": evaluation,
            "is_approved": is_approved,
            "code_path": code_path,
            "run_script_path": run_script_path
        }


def main():
    """Main function to run the meta-agent generator."""
    load_env_vars()
    
    if len(sys.argv) < 2:
        print("Usage: python meta_agent_generator.py \"Task description\" [output_filename]")
        sys.exit(1)
    
    task_description = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_filename = sys.argv[2]
    else:
        task_words = task_description.lower().split()
        if len(task_words) > 3:
            task_words = task_words[:3]
        filename_base = "_".join(task_words)
        output_filename = f"{filename_base}_agents.py"
    
    generator = MetaAgentGenerator()
    result = generator.generate_agent_system(task_description, output_filename)
    
    if result["is_approved"]:
        print("\n" + "="*50)
        print("✅ AGENT SYSTEM GENERATED SUCCESSFULLY")
        print("="*50)
        print(f"Code saved to: {result['code_path']}")
        print(f"Run script: {result['run_script_path']}")
        print("\nTo run the agent system:")
        print(f"  ./{os.path.basename(result['run_script_path'])}")
    else:
        print("\n" + "="*50)
        print("❌ AGENT SYSTEM GENERATION FAILED")
        print("="*50)
        print("Please review the evaluation feedback and try again.")


if __name__ == "__main__":
    main()
