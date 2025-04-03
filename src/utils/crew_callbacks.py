"""Callback handlers for CrewAI."""
from typing import Dict, Any, Optional, List, Callable

from .agent_logger import AgentActivityLogger

class CrewCallbackHandler:
    """Callback handler for CrewAI step_callback."""
    
    def __init__(self, logger: AgentActivityLogger):
        """
        Initialize the crew callback handler.
        
        Args:
            logger: The agent activity logger to use
        """
        self.logger = logger
    
    def __call__(
        self,
        step_type: str,
        step_index: int,
        step_input: Optional[Any] = None,
        step_output: Optional[Any] = None,
        **kwargs
    ) -> None:
        """
        Handle a CrewAI step callback.
        
        Args:
            step_type: The type of step (e.g., 'task', 'step')
            step_index: The index of the step
            step_input: Optional input to the step
            step_output: Optional output from the step
        """
        agent_name = kwargs.get("agent_name", "Unknown Agent")
        task_name = kwargs.get("task_name", "Unknown Task")
        
        if step_type == "task:start":
            self.logger.log_activity(
                agent_name=agent_name,
                activity_type="task_start",
                activity_data={
                    "task_name": task_name,
                    "description": step_input,
                    "step_index": step_index
                }
            )
        
        elif step_type == "task:end":
            self.logger.log_activity(
                agent_name=agent_name,
                activity_type="task_end",
                activity_data={
                    "task_name": task_name,
                    "result": step_output,
                    "step_index": step_index
                }
            )
        
        elif step_type == "agent:prompt":
            self.logger.log_activity(
                agent_name=agent_name,
                activity_type="prompt",
                activity_data={
                    "task_name": task_name,
                    "prompt": step_input,
                    "step_index": step_index
                }
            )
        
        elif step_type == "agent:response":
            self.logger.log_activity(
                agent_name=agent_name,
                activity_type="response",
                activity_data={
                    "task_name": task_name,
                    "response": step_output,
                    "step_index": step_index
                }
            )
        
        else:
            self.logger.log_activity(
                agent_name=agent_name,
                activity_type=f"step:{step_type}",
                activity_data={
                    "task_name": task_name,
                    "input": step_input,
                    "output": step_output,
                    "step_index": step_index
                }
            )

def create_callback(
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_to_db: bool = False,
    log_dir: str = "./agent_logs",
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    table_name: str = "agent_activities"
) -> Callable:
    """
    Create a callback function for CrewAI step_callback.
    
    Args:
        log_to_console: Whether to log activities to console
        log_to_file: Whether to log activities to file
        log_to_db: Whether to log activities to database
        log_dir: Directory for log files
        supabase_url: Supabase URL for database logging
        supabase_key: Supabase API key for database logging
        table_name: Supabase table name for storing agent activities
        
    Returns:
        Callback function for CrewAI step_callback
    """
    logger = AgentActivityLogger(
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        log_to_db=log_to_db,
        log_dir=log_dir,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        table_name=table_name
    )
    
    return CrewCallbackHandler(logger)
