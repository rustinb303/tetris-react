"""Web interface for the meta-agent system with chat functionality."""
import os
import sys
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid

from meta_agent_generator import MetaAgentGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

active_sessions = {}

class MetaAgentSession:
    """Class to manage a meta-agent session."""
    
    def __init__(self, session_id, task_description):
        self.session_id = session_id
        self.task_description = task_description
        self.interview_results = None
        self.design_results = None
        self.code_results = None
        self.evaluation_results = None
        self.output_filename = None
        self.messages = []
        self.current_stage = "interview"
        self.is_running = False
        self.thread = None
    
    def add_message(self, role, content):
        """Add a message to the conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.messages.append(message)
        return message
    
    def get_messages(self):
        """Get all messages in the conversation."""
        return self.messages
    
    def run_meta_agent_process(self):
        """Run the meta-agent process in a separate thread."""
        self.is_running = True
        self.user_responses = {}
        self.waiting_for_response = False
        self.current_question = None
        
        try:
            generator = MetaAgentGenerator()
            
            self.current_stage = "interview"
            socketio.emit('status_update', {
                'session_id': self.session_id,
                'stage': 'interview',
                'message': 'Starting interview process...'
            })
            
            def interview_callback(message, expect_response=False):
                self.send_agent_message(message)
                
                if expect_response:
                    self.waiting_for_response = True
                    self.current_question = message
                    
                    max_wait_time = 300  # 5 minutes timeout
                    wait_start = time.time()
                    
                    while self.waiting_for_response:
                        time.sleep(0.5)
                        if time.time() - wait_start > max_wait_time:
                            self.waiting_for_response = False
                            return "No response received"
                    
                    return self.user_responses.get(message, "")
                
                return None
            
            self.interview_results = generator.interview_user(
                self.task_description, 
                callback=interview_callback
            )
            
            self.current_stage = "design"
            socketio.emit('status_update', {
                'session_id': self.session_id,
                'stage': 'design',
                'message': 'Designing agent system...'
            })
            
            self.send_agent_message("Designing the optimal agent system based on your requirements...")
            self.design_results = generator.design_agents(self.interview_results)
            
            self.current_stage = "code"
            socketio.emit('status_update', {
                'session_id': self.session_id,
                'stage': 'code',
                'message': 'Generating code...'
            })
            
            output_filename = f"{self.task_description.lower().replace(' ', '_')[:20]}.py"
            self.output_filename = output_filename
            self.send_agent_message(f"Generating code for {output_filename}...")
            self.code_results = generator.generate_code(self.design_results, output_filename)
            
            self.current_stage = "evaluate"
            socketio.emit('status_update', {
                'session_id': self.session_id,
                'stage': 'evaluate',
                'message': 'Evaluating code...'
            })
            
            self.send_agent_message("Evaluating the generated code...")
            is_approved, self.evaluation_results = generator.evaluate_code(self.code_results, self.interview_results)
            
            self.current_stage = "complete"
            socketio.emit('status_update', {
                'session_id': self.session_id,
                'stage': 'complete',
                'message': 'Creating run script...'
            })
            
            code_path = generator.save_code(self.code_results, output_filename)
            
            if is_approved:
                script_name = generator.create_run_script(output_filename)
                
                completion_message = (
                    f"✅ Task complete! Generated files:\n\n"
                    f"- {output_filename}: Main agent system implementation\n"
                    f"- {script_name}: Run script for easy execution\n\n"
                    f"You can run the system with: ./{script_name}"
                )
                self.send_agent_message(completion_message)
                
                socketio.emit('process_complete', {
                    'session_id': self.session_id,
                    'output_filename': output_filename,
                    'script_name': script_name,
                    'code_content': self.code_results
                })
            else:
                self.send_agent_message(
                    f"⚠️ The generated code needs revision. Here are the evaluation results:\n\n"
                    f"{self.evaluation_results}\n\n"
                    f"The code has been saved to {output_filename} for your reference."
                )
                
                socketio.emit('process_complete', {
                    'session_id': self.session_id,
                    'output_filename': output_filename,
                    'evaluation_results': self.evaluation_results,
                    'needs_revision': True,
                    'code_content': self.code_results
                })
            
        except Exception as e:
            error_message = f"Error in meta-agent process: {str(e)}"
            self.send_agent_message(error_message)
            socketio.emit('error', {
                'session_id': self.session_id,
                'error': error_message
            })
        
        finally:
            self.is_running = False
    
    def send_agent_message(self, content):
        """Send a message from the agent to the client."""
        message = self.add_message("agent", content)
        socketio.emit('agent_message', {
            'session_id': self.session_id,
            'message': message
        })
        return message
    
    def send_user_message(self, content):
        """Process a message from the user."""
        message = self.add_message("user", content)
        socketio.emit('user_message_received', {
            'session_id': self.session_id,
            'message': message
        })
        return message
    
    def start_process(self):
        """Start the meta-agent process in a separate thread."""
        if not self.is_running:
            self.thread = threading.Thread(target=self.run_meta_agent_process)
            self.thread.daemon = True
            self.thread.start()
            return True
        return False


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new meta-agent session."""
    try:
        data = request.json
        task_description = data.get('task_description', '')
        
        if not task_description:
            return jsonify({'error': 'Task description is required'}), 400
        
        session_id = str(uuid.uuid4())
        new_session = MetaAgentSession(session_id, task_description)
        active_sessions[session_id] = new_session
        
        new_session.add_message(
            "agent", 
            f"Hello! I'll help you create an AI agent system for: {task_description}\n\n"
            f"Let's start by gathering some information about your requirements."
        )
        
        try:
            started = new_session.start_process()
            if not started:
                return jsonify({'error': 'Failed to start session process'}), 500
        except Exception as e:
            print(f"Error starting session process: {str(e)}")
            return jsonify({'error': f'Error starting session: {str(e)}'}), 500
        
        return jsonify({
            'session_id': session_id,
            'task_description': task_description
        })
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        return jsonify({'error': f'Error creating session: {str(e)}'}), 500


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = active_sessions[session_id]
    return jsonify({
        'session_id': session.session_id,
        'task_description': session.task_description,
        'current_stage': session.current_stage,
        'is_running': session.is_running,
        'messages': session.get_messages()
    })


@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
def get_messages(session_id):
    """Get all messages for a session."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = active_sessions[session_id]
    return jsonify({
        'messages': session.get_messages()
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'status': 'connected'})


@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a session."""
    session_id = data.get('session_id')
    if session_id not in active_sessions:
        emit('error', {'error': 'Session not found'})
        return
    
    emit('session_joined', {
        'session_id': session_id,
        'messages': active_sessions[session_id].get_messages()
    })


@socketio.on('user_message')
def handle_user_message(data):
    """Handle message from user."""
    session_id = data.get('session_id')
    content = data.get('content')
    
    if not session_id or not content:
        emit('error', {'error': 'Session ID and content are required'})
        return
    
    if session_id not in active_sessions:
        emit('error', {'error': 'Session not found'})
        return
    
    session = active_sessions[session_id]
    message = session.send_user_message(content)
    
    if session.is_running and hasattr(session, 'waiting_for_response') and session.waiting_for_response:
        if hasattr(session, 'current_question') and session.current_question:
            session.user_responses[session.current_question] = content
            session.waiting_for_response = False
    elif not session.is_running:
        response = "I've received your message, but the meta-agent process has already completed."
        session.send_agent_message(response)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
