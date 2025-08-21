import uuid
from datetime import datetime
import json
import time
import numpy as np
from flask import jsonify

# Global variables that will be set by the main app
db = None
ChatHistory = None
ChatSession = None
ToolUsage = None
ToolDefinition = None
ChatHistoryManager = None

def init_chat_db(database):
    """Initialize the database reference and create models"""
    global db, ChatHistory, ChatSession, ToolUsage, ToolDefinition, ChatHistoryManager, AgentDefinition
    db = database

    # Helper function to convert model instances to dictionaries
    def to_dict_helper(instance):
        d = {}
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            if isinstance(value, datetime):
                d[column.name] = value.isoformat()
            else:
                d[column.name] = value
        return d
    
    class AgentDefinition(db.Model):
        __tablename__ = 'agent_definitions'
        agent_id = db.Column(db.String(255), primary_key=True, default=lambda: f"agent_{uuid.uuid4()}")
        name = db.Column(db.String(255), unique=True, nullable=False)
        description = db.Column(db.Text)
        llm_config = db.Column(db.JSON, nullable=False)
        prompt_template = db.Column(db.Text, nullable=False)

        def to_dict(self):
            return to_dict_helper(self)

    class ChatSession(db.Model):
        __tablename__ = 'chat_sessions'
        session_id = db.Column(db.String(255), primary_key=True, default=lambda: f"session_{uuid.uuid4()}")
        user_id = db.Column(db.String(255), nullable=False)
        title = db.Column(db.String(500))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return to_dict_helper(self)
        
    class ToolDefinition(db.Model):
        __tablename__ = 'tool_definitions'
        tool_id = db.Column(db.String(255), primary_key=True, default=lambda: f"tooldef_{uuid.uuid4()}")
        name = db.Column(db.String(255), unique=True, nullable=False)
        description = db.Column(db.Text)
        input_schema = db.Column(db.JSON, nullable=False)
        version = db.Column(db.String(50), default='1.0.0')
        is_active = db.Column(db.Boolean, default=True)
        cost_per_call_cents = db.Column(db.Integer, default=0) 
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return to_dict_helper(self)
        
    class ToolUsage(db.Model):
        __tablename__ = 'tool_usage'
        tool_call_id = db.Column(db.String(255), primary_key=True, default=lambda: f"tool_{uuid.uuid4()}")
        session_id = db.Column(db.String(255), nullable=False)
        message_id = db.Column(db.String(255), db.ForeignKey('chat_history.message_id'))
        trace_id = db.Column(db.String(255), db.ForeignKey('chat_history.trace_id'))
        tool_id = db.Column(db.String(255), db.ForeignKey('tool_definitions.tool_id'), nullable=False)
        tool_name = db.Column(db.String(255), nullable=False)
        tool_input = db.Column(db.JSON, nullable=False)
        tool_output = db.Column(db.JSON)
        tool_error = db.Column(db.Text)
        execution_time_ms = db.Column(db.Integer)
        status = db.Column(db.String(50), default='pending')  # 'pending', 'success', 'error', 'timeout'
        started_at = db.Column(db.DateTime, default=datetime.utcnow)
        completed_at = db.Column(db.DateTime)
        
        # Additional tracking fields
        cost_cents = db.Column(db.Integer)  # For paid APIs
        tokens_used = db.Column(db.Integer)
        rate_limit_hit = db.Column(db.Boolean, default=False)
        retry_count = db.Column(db.Integer, default=0)

        def to_dict(self):
            return to_dict_helper(self)

    class ChatHistory(db.Model):
        __tablename__ = 'chat_history'
        message_id = db.Column(db.String(255), primary_key=True, default=lambda: f"msg_{uuid.uuid4()}")
        session_id = db.Column(db.String(255), db.ForeignKey('chat_sessions.session_id'))
        trace_id = db.Column(db.String(255), nullable=False)
        user_id = db.Column(db.String(255), nullable=False)
        agent_id = db.Column(db.String(255), db.ForeignKey('agent_definitions.agent_id'))
        message_type = db.Column(db.String(50), nullable=False)  # 'human', 'ai', 'system', 'tool_call', 'tool_result'
        content = db.Column(db.Text)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
        # LangChain specific fields
        additional_kwargs = db.Column(db.JSON, default=lambda: {})
        model = db.Column(db.String(255))
        response_time_ms = db.Column(db.Integer)
        tool_calls_made = db.Column(db.Integer, default=0)
        response_md = db.Column(db.JSON, default=lambda: {})
        
        # Tool usage fields
        tool_call_id = db.Column(db.String(255))
        tool_name = db.Column(db.String(255))
        tool_input = db.Column(db.JSON)
        tool_output = db.Column(db.JSON)
        tool_error = db.Column(db.Text)
        tool_execution_time_ms = db.Column(db.Integer)

        def to_dict(self):
            return to_dict_helper(self)




    # --- Chat History Management Class ---
    class ChatHistoryManager:
        def __init__(self, session_id: str, user_id: str = 'user_1'):
            self.session_id = session_id
            self.user_id = user_id
            self._ensure_session_exists()

        def _ensure_session_exists(self):
            """Ensure the chat session exists in the database"""
            session = ChatSession.query.filter_by(session_id=self.session_id).first()
            if not session:
                session = ChatSession(
                    session_id=self.session_id,
                    title= "New Session",
                    user_id=self.user_id,
                )
                print("-----------------> New chat session created: ", session.session_id)
                db.session.add(session)
                db.session.commit()

        
        def add_message(self, trace_id: str, message_type: str, content: str, agent_id:str, **kwargs):
            """Add a message to the chat history"""
            message = ChatHistory(
                session_id=self.session_id,
                user_id=self.user_id,
                agent_id = agent_id,
                message_type=message_type,
                content=content,
                trace_id=trace_id,
                **kwargs
            )
            db.session.add(message)
            db.session.commit()
            return message

        def add_tool_call(self, agent_id: str, trace_id: str, tool_call_id: str, tool_name: str, tool_input: dict, content: str = None):
            """Log a tool call"""
            content = content or f"Calling tool: {tool_name}"
            print(f"Adding tool call: {tool_name} with ID: {tool_call_id}")
            return self.add_message(
                agent_id=agent_id,
                trace_id=trace_id,
                message_type='tool_call',
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                tool_input=tool_input,
                content=content
            )

        def add_tool_result(self, trace_id: str, tool_call_id: str, tool_name: str, tool_output: dict, 
                           content: str = None, error: str = None, execution_time_ms: int = None):
            """Log a tool result"""
            content = content or f"Tool {tool_name} result"
            return self.add_message(
                trace_id=trace_id,
                message_type='tool_result',
                content=content,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                tool_output=tool_output,
                tool_error=error,
                tool_execution_time_ms=execution_time_ms
            )

        def log_tool_usage(self, trace_id: str, tool_call_id: str, tool_name: str, tool_input: dict, 
                        tool_output: dict = None, error: str = None, execution_time_ms: int = None, 
                        tokens_used: int = None, message_id: str = None):
            """Log detailed tool usage metrics"""
            status = 'error' if error else 'success'
            
            # Get the tool_id from the tool name
            tool_id = db.session.query(ToolDefinition.tool_id).filter_by(name=tool_name).scalar()
            
            tool_usage = ToolUsage(
                session_id=self.session_id,
                trace_id=trace_id,
                message_id=message_id,
                tool_call_id=tool_call_id,
                tool_id=tool_id,  # Add the tool_id here
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                tool_error=error,
                execution_time_ms=execution_time_ms,
                status=status,
                completed_at=datetime.utcnow(),
                tokens_used=tokens_used
            )
            db.session.add(tool_usage)
            db.session.commit()
            return tool_usage

        def get_conversation_history(self, limit: int = 50):
            """Retrieve conversation history for this session"""
            messages = ChatHistory.query.filter_by(
                session_id=self.session_id
            ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
            
            return [msg.to_dict() for msg in reversed(messages)]

    # Make classes available globally in this module
    globals()['ChatHistory'] = ChatHistory
    globals()['ChatSession'] = ChatSession
    globals()['ToolUsage'] = ToolUsage
    globals()['ToolDefinition'] = ToolDefinition
    globals()['ChatHistoryManager'] = ChatHistoryManager


def handle_chat_sessions(request):
    """Handle chat sessions GET and POST requests"""
    user_id = 'user_1'  # In production, get from auth
    
    if request.method == 'GET':
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
        return jsonify([session.to_dict() for session in sessions])
    
    if request.method == 'POST':
        data = request.json
        session = ChatSession(
            user_id=user_id,
            title=data.get('title', 'New Chat Session'),
        )
        db.session.add(session)
        db.session.commit()
        return jsonify(session.to_dict()), 201

def get_session_tool_usage(session_id):
    """Get tool usage for a specific session"""
    usage = ToolUsage.query.filter_by(session_id=session_id).order_by(ToolUsage.started_at.desc()).all()
    return jsonify([u.to_dict() for u in usage])

def export_chat_session(session_id):
    """Export a complete chat session with tool usage"""
    chat_manager = ChatHistoryManager(session_id)
    history = chat_manager.get_conversation_history(limit=1000)
    
    # Get tool usage for this session
    tool_usage = ToolUsage.query.filter_by(session_id=session_id).all()
    
    export_data = {
        "session_id": session_id,
        "exported_at": datetime.utcnow().isoformat(),
        "chat_history": history,
        "tool_usage": [usage.to_dict() for usage in tool_usage],
        "summary": {
            "total_messages": len(history),
            "total_tool_calls": len(tool_usage),
            "unique_tools_used": len(set(usage.tool_name for usage in tool_usage)),
            "average_tool_execution_time": np.mean([usage.execution_time_ms for usage in tool_usage if usage.execution_time_ms]) if tool_usage else 0
        }
    }
    
    return jsonify(export_data)

def clear_chat_history():
    """Clear all chat history data - USE WITH CAUTION"""
    try:
        # Delete in order to respect foreign key constraints
        ToolUsage.query.delete()
        ChatHistory.query.delete()
        ChatSession.query.delete()

        db.session.commit()
        return jsonify({"message": "All chat history cleared successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to clear chat history: {str(e)}"}), 500

def clear_session_data(session_id):
    """Clear chat history for a specific session"""
    try:
        # Delete in order to respect foreign key constraints
        ToolUsage.query.filter_by(session_id=session_id).delete()
        ChatHistory.query.filter_by(session_id=session_id).delete()
        ChatSession.query.filter_by(session_id=session_id).delete()
        
        db.session.commit()
        return jsonify({"message": f"Session {session_id} data cleared successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to clear session data: {str(e)}"}), 500
def initialize_tool_definitions():
    """Initialize tool definitions in the database"""
    tools_data = [
        {
            "name": "get_user_accounts",
            "description": "Retrieves all accounts for a given user",
            "input_schema": {"type": "object", "properties": {}},
            "cost_per_call_cents": 0
        },
        {
            "name": "get_transactions_summary",
            "description": "Provides spending summary with time period and account filters",
            "input_schema": {
                "type": "object",
                "properties": {
                    "time_period": {"type": "string"},
                    "account_name": {"type": "string"}
                }
            },
            "cost_per_call_cents": 0
        },
        {
            "name": "search_support_documents",
            "description": "Searches knowledge base for customer support answers",
            "input_schema": {
                "type": "object",
                "properties": {"user_question": {"type": "string"}},
                "required": ["user_question"]
            },
            "cost_per_call_cents": 2
        },
        {
            "name": "create_new_account",
            "description": "Creates a new bank account for the user",
            "input_schema": {
                "type": "object",
                "properties": {
                    "account_type": {"type": "string", "enum": ["checking", "savings", "credit"]},
                    "name": {"type": "string"},
                    "balance": {"type": "number"}
                },
                "required": ["account_type", "name"]
            },
            "cost_per_call_cents": 0
        },
        {
            "name": "transfer_money",
            "description": "Transfers money between accounts or to external accounts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "from_account_name": {"type": "string"},
                    "to_account_name": {"type": "string"},
                    "amount": {"type": "number"},
                    "to_external_details": {"type": "object"}
                },
                "required": ["from_account_name", "amount"]
            },
            "cost_per_call_cents": 0
        }
    ]
    
    for tool_data in tools_data:
        existing_tool = ToolDefinition.query.filter_by(name=tool_data["name"]).first()
        if not existing_tool:
            tool_def = ToolDefinition(**tool_data)
            db.session.add(tool_def)
    
    db.session.commit()

def initialize_agent_definitions():
    """Initialize agent definitions in the database"""
    agents_data = [
                {
            "name": "banking_agent_v1",
            "description": "A customer support banking agent to help answer questions about their account and other general banking inquiries.",
            "llm_config": {
                "model": "gpt-4.1",
                "rate_limit": 50,
                "token_limit": 1000
            },
            "prompt_template": "You are a banking assistant. Answer the user's questions about their bank accounts."
        }

    ]
    
    for agent in agents_data:
        existing_agent = AgentDefinition.query.filter_by(name=agent["name"]).first()
        if not existing_agent:
            agent_def = AgentDefinition(**agent)
            db.session.add(agent_def)

    db.session.commit()