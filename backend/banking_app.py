# import urllib.parse
import uuid
from datetime import datetime
import json
import time
from dateutil.relativedelta import relativedelta
# from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_sqlserver import SQLServer_VectorStore
# from langchain_community.callbacks.manager import get_openai_callback

from shared.db_connect import create_azuresql_connection
import requests  # For calling analytics service

# Load Environment variables and initialize app
import os
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

# --- Azure OpenAI Configuration ---
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Analytics service URL
ANALYTICS_SERVICE_URL = "http://127.0.0.1:5002"

if not all([AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT]):
    print("⚠️  Warning: One or more Azure OpenAI environment variables are not set.")
    ai_client = None
    embeddings_client = None
else:
    ai_client = AzureOpenAI(
        azure_deployment=AZURE_OPENAI_DEPLOYMENT,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-10-21",
        api_key=AZURE_OPENAI_KEY
    )
    embeddings_client = AzureOpenAIEmbeddings(
        azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        openai_api_version="2024-10-21",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    )

# Database configuration for Azure SQL (banking data)
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': create_azuresql_connection,
    'poolclass': QueuePool,
    'pool_size': 5,
    'max_overflow': 10,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_reset_on_return': 'rollback'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Vector Store Initialization
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
connection_string_vector = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)
vector_store = None
if embeddings_client:
    vector_store = SQLServer_VectorStore(
        connection_string=connection_string_vector,
        table_name="DocsChunks_Embeddings",
        embedding_function=embeddings_client,
        embedding_length=1536,
        distance_strategy=DistanceStrategy.COSINE,
    )

def to_dict_helper(instance):
    d = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            d[column.name] = value.isoformat()
        else:
            d[column.name] = value
    return d

# Banking Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"user_{uuid.uuid4()}")
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accounts = db.relationship('Account', backref='user', lazy=True)

    def to_dict(self):
        return to_dict_helper(self)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"acc_{uuid.uuid4()}")
    user_id = db.Column(db.String(255), db.ForeignKey('users.id'), nullable=False)
    account_number = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4().int)[:12])
    account_type = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return to_dict_helper(self)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"txn_{uuid.uuid4()}")
    from_account_id = db.Column(db.String(255), db.ForeignKey('accounts.id'))
    to_account_id = db.Column(db.String(255), db.ForeignKey('accounts.id'))
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return to_dict_helper(self)

# Analytics Service Integration
def call_analytics_service(endpoint, method='POST', data=None):
    """Helper function to call analytics service"""
    try:
        url = f"{ANALYTICS_SERVICE_URL}/api/{endpoint}"
        if method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        else:
            response = requests.get(url, timeout=5)
        return response.json() if response.status_code < 400 else None
    except Exception as e:
        print(f"Analytics service call failed: {e}")
        return None

# AI Chatbot Tool Definitions (same as before)
def get_user_accounts(user_id='user_1'):
    """Retrieves all accounts for a given user."""
    try:
        accounts = Account.query.filter_by(user_id=user_id).all()
        if not accounts:
            return "No accounts found for this user."
        return json.dumps([
            {"name": acc.name, "account_type": acc.account_type, "balance": acc.balance} 
            for acc in accounts
        ])
    except Exception as e:
        return f"Error retrieving accounts: {str(e)}"

def get_transactions_summary(user_id='user_1', time_period='this month', account_name=None):
    """Provides a summary of the user's spending. Can be filtered by a time period and a specific account."""
    try:
        query = db.session.query(Transaction.category, db.func.sum(Transaction.amount).label('total_spent')).filter(
            Transaction.type == 'payment'
        )
        if account_name:
            account = Account.query.filter_by(user_id=user_id, name=account_name).first()
            if not account:
                return json.dumps({"status": "error", "message": f"Account '{account_name}' not found."})
            query = query.filter(Transaction.from_account_id == account.id)
        else:
            user_accounts = Account.query.filter_by(user_id=user_id).all()
            account_ids = [acc.id for acc in user_accounts]
            query = query.filter(Transaction.from_account_id.in_(account_ids))

        end_date = datetime.utcnow()
        if 'last 6 months' in time_period.lower():
            start_date = end_date - relativedelta(months=6)
        elif 'this year' in time_period.lower():
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0)
        else:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
        
        query = query.filter(Transaction.created_at.between(start_date, end_date))
        results = query.group_by(Transaction.category).order_by(db.func.sum(Transaction.amount).desc()).all()
        total_spending = sum(r.total_spent for r in results)
        
        summary_details = {
            "total_spending": round(total_spending, 2),
            "period": time_period,
            "account_filter": account_name or "All Accounts",
            "top_categories": [{"category": r.category, "amount": round(r.total_spent, 2)} for r in results[:3]]
        }

        if not results:
            return json.dumps({"status": "success", "summary": f"You have no spending for the period '{time_period}' in account '{account_name or 'All Accounts'}'."})

        return json.dumps({"status": "success", "summary": summary_details})
    except Exception as e:
        print(f"ERROR in get_transactions_summary: {e}")
        return json.dumps({"status": "error", "message": f"An error occurred while generating the transaction summary."})

def search_support_documents(user_question: str):
    """Searches the knowledge base for answers to customer support questions using vector search."""
    if not vector_store:
        return "The vector store is not configured."
    try:
        results = vector_store.similarity_search_with_score(user_question, k=3)
        relevant_docs = [doc.page_content for doc, score in results if score < 0.5]
        
        if not relevant_docs:
            return "No relevant support documents found to answer this question."

        context = "\n\n---\n\n".join(relevant_docs)
        return context

    except Exception as e:
        print(f"ERROR in search_support_documents: {e}")
        return "An error occurred while searching for support documents."

def create_new_account(user_id='user_1', account_type='checking', name=None, balance=0.0):
    """Creates a new bank account for the user."""
    if not name:
        return json.dumps({"status": "error", "message": "An account name is required."})
    try:
        new_account = Account(user_id=user_id, account_type=account_type, balance=balance, name=name)
        db.session.add(new_account)
        db.session.commit()
        return json.dumps({
            "status": "success", "message": f"Successfully created new {account_type} account '{name}' with balance ${balance:.2f}.",
            "account_id": new_account.id, "account_name": new_account.name
        })
    except Exception as e:
        db.session.rollback()
        return f"Error creating account: {str(e)}"

def transfer_money(user_id='user_1', from_account_name=None, to_account_name=None, amount=0.0, to_external_details=None):
    """Transfers money between user's accounts or to an external account."""
    if not from_account_name or (not to_account_name and not to_external_details) or amount <= 0:
        return json.dumps({"status": "error", "message": "Missing required transfer details."})
    try:
        from_account = Account.query.filter_by(user_id=user_id, name=from_account_name).first()
        if not from_account:
            return json.dumps({"status": "error", "message": f"Account '{from_account_name}' not found."})
        if from_account.balance < amount:
            return json.dumps({"status": "error", "message": "Insufficient funds."})
        
        to_account = None
        if to_account_name:
            to_account = Account.query.filter_by(user_id=user_id, name=to_account_name).first()
            if not to_account:
                 return json.dumps({"status": "error", "message": f"Recipient account '{to_account_name}' not found."})
        
        new_transaction = Transaction(
            from_account_id=from_account.id, to_account_id=to_account.id if to_account else None,
            amount=amount, type='transfer', description=f"Transfer to {to_account_name or to_external_details.get('name', 'External')}",
            category='Transfer', status='completed'
        )
        from_account.balance -= amount
        if to_account:
            to_account.balance += amount
        db.session.add(new_transaction)
        db.session.commit()
        return json.dumps({"status": "success", "message": f"Successfully transferred ${amount:.2f}."})
    except Exception as e:
        db.session.rollback()
        return f"Error during transfer: {str(e)}"

# Banking API Routes
@app.route('/api/accounts', methods=['GET', 'POST'])
def handle_accounts():
    user_id = 'user_1'
    if request.method == 'GET':
        accounts = Account.query.filter_by(user_id=user_id).all()
        return jsonify([acc.to_dict() for acc in accounts])
    if request.method == 'POST':
        data = request.json
        account_str = create_new_account(user_id=user_id, account_type=data.get('account_type'), name=data.get('name'), balance=data.get('balance', 0))
        return jsonify(json.loads(account_str)), 201

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    user_id = 'user_1'
    if request.method == 'GET':
        accounts = Account.query.filter_by(user_id=user_id).all()
        account_ids = [acc.id for acc in accounts]
        transactions = Transaction.query.filter((Transaction.from_account_id.in_(account_ids)) | (Transaction.to_account_id.in_(account_ids))).order_by(Transaction.created_at.desc()).all()
        return jsonify([t.to_dict() for t in transactions])
    if request.method == 'POST':
        data = request.json
        result_str = transfer_money(
            user_id=user_id, from_account_name=data.get('from_account_name'), to_account_name=data.get('to_account_name'),
            amount=data.get('amount'), to_external_details=data.get('to_external_details')
        )
        result = json.loads(result_str)
        status_code = 201 if result.get("status") == "success" else 400
        return jsonify(result), status_code

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    agent_id = "agent_bd50a4ca-2bec-46c6-9c5d-97b7fb060bbc" # hardcoding for now, FIX later
    if not ai_client:
        return jsonify({"error": "Azure OpenAI client is not configured."}), 503

    data = request.json
    messages = data.get("messages", [])
    session_id = data.get("session_id")
    user_id = data.get("user_id", "user_1")

    #-------- Log user message to analytics service --------

    if messages and messages[-1].get("role") == "user":
        trace_id = f"traceID_{uuid.uuid4()}"
        analytics_data = {
            "user_session_id": session_id,
            "agent_id": agent_id,
            "user_id": user_id,
            "trace_id": trace_id,
            "message_type": "human",
            "content": messages[-1].get("content")
        }
        call_analytics_service("chat/log-message", data=analytics_data)
    #--------------------------------------------------------

    #-------- Tool Definitions for Banking agent ------------

    tools = [
        {"type": "function", "function": {
            "name": "get_user_accounts",
            "description": "Get a list of all bank accounts belonging to the current user.",
            "parameters": {"type": "object", "properties": {}}
        }},
        {"type": "function", "function": {
            "name": "get_transactions_summary",
            "description": "Get a summary of spending for the user, filterable by account and time period.",
             "parameters": {
                "type": "object",
                "properties": {
                    "time_period": {"type": "string", "description": "e.g., 'this month', 'last 6 months'."},
                    "account_name": {"type": "string", "description": "e.g., 'Primary Checking'."}
                },
            }
        }},
        {"type": "function", "function": {
            "name": "search_support_documents",
            "description": "Use this for customer support questions, such as 'how to do X', 'what are the fees for Y', or policy questions.",
             "parameters": {
                "type": "object",
                "properties": {"user_question": {"type": "string", "description": "The user's full question."}},
                "required": ["user_question"]
            }
        }},
        {"type": "function", "function": {
            "name": "create_new_account",
            "description": "Creates a new bank account for the user.",
            "parameters": {"type": "object", "properties": {
                "account_type": {"type": "string", "enum": ["checking", "savings", "credit"]},
                "name": {"type": "string", "description": "The desired name for the new account."},
                "balance": {"type": "number", "description": "The initial balance."}}, "required": ["account_type", "name"]
            }
        }},
        {"type": "function", "function": {
            "name": "transfer_money",
            "description": "Transfer funds between accounts or to an external account.",
            "parameters": {"type": "object", "properties": {
                "from_account_name": {"type": "string"}, "to_account_name": {"type": "string"}, "amount": {"type": "number"},
                "to_external_details": {"type": "object", "properties": {"name": {"type": "string"},"accountNumber": {"type": "string"},"routingNumber": {"type": "string"}}}
                }, "required": ["from_account_name", "amount"]
            }
        }}
    ]
    #--------------------------------------------------------
    start_time = time.time()
    response = ai_client.chat.completions.create(model=AZURE_OPENAI_DEPLOYMENT, messages=messages, tools=tools, tool_choice="auto")

    # tools to use ....
    response_message = response.choices[0].message
    first_response_time = int((time.time() - start_time) * 1000)
    tool_calls = response_message.tool_calls

    if tool_calls:
        print("using tools ...")
        messages.append(response_message)
        available_functions = {
            "get_user_accounts": get_user_accounts,
            "get_transactions_summary": get_transactions_summary,
            "search_support_documents": search_support_documents,
            "create_new_account": create_new_account,
            "transfer_money": transfer_money,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool
            tool_start_time = time.time()
            function_to_call = available_functions[function_name]
            content = response_message.content
            #-------- Log tool call details to analytics service --------

            analytics_data = {
                "user_session_id": session_id,
                "user_id": user_id,
                "agent_id": agent_id,
                "content": content,
                "trace_id": trace_id,
                "tool_call_id": tool_call.id,
                "tool_name": function_name,
                "tool_input": function_args
            }
            call_analytics_service("chat/log-tool-call", data=analytics_data)
            #--------------------------------------------------------
            
            
            try:
                function_response = function_to_call(**function_args)
                tool_execution_time = int((time.time() - tool_start_time) * 1000)
                tool_error = None
                tool_output = {"result": function_response}
                
            except Exception as e:
                tool_execution_time = int((time.time() - tool_start_time) * 1000)
                tool_error = str(e)
                function_response = f"Error executing {function_name}: {str(e)}"
                tool_output = {"error": str(e)}
                
            #------------------------------------------------------------
            #-------- Log tool call results to analytics service --------
            analytics_data = {
                "user_id": user_id,
                "user_session_id": session_id,
                "trace_id": trace_id,
                "agent_id": agent_id,
                "tool_call_id": tool_call.id,
                "tool_name": function_name,
                "tool_output": tool_output,
                "content": function_response[:500] + "..." if len(str(function_response)) > 500 else str(function_response),
                "error": tool_error,
                "execution_time_ms": tool_execution_time
            }
            call_analytics_service("chat/log-tool-result", data=analytics_data)
            #------------------------------------------------------------  
            #-------- Log tool call results to analytics service --------
            analytics_data = {
                "user_id": user_id,
                "user_session_id": session_id,
                'trace_id':trace_id,
                'tool_call_id':tool_call.id,
                'tool_name':function_name,
                'tool_input':function_args,
                'tool_output':tool_output,
                'error':tool_error,
                'execution_time_ms':tool_execution_time,
                'tokens_used':response.usage.total_tokens
            }
            call_analytics_service("chat/log_tool_usage_details", data=analytics_data) 
            #------------------------------------------------------------ 

            # Prepare content for final message format
            tool_message_content = function_response
            if function_name == 'search_support_documents':
                rag_instruction = "You are a customer support agent. Answer the user's last question based *only* on the following document context. If the context says no documents were found, inform the user you could not find an answer. Do not use your general knowledge. CONTEXT: "
                tool_message_content = rag_instruction + function_response

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_message_content,
            })
        
        # Second API call to get a natural language response based on the tool's output
        
        second_response = ai_client.chat.completions.create(model=AZURE_OPENAI_DEPLOYMENT, messages=messages)
        response_time_with_tool = int((time.time() - start_time) * 1000)
        
        print("second response trace:")
        for choice in second_response.choices:
            print(f"Choice: {choice}")
            print("-----------------------------------------")
        final_message = second_response.choices[0].message.content
        #-------- Log final results to analytics service --------
        analytics_data = {
            "user_session_id": session_id,
            "agent_id": agent_id,
            "user_id": user_id,
            "trace_id": trace_id,
            "message_type": "ai",
            "content": final_message,
            "model": AZURE_OPENAI_DEPLOYMENT,
            "response_time_ms": response_time_with_tool,
            "tool_calls_made": len(tool_calls)
        }
        call_analytics_service("chat/log-message", data=analytics_data)

        
        return jsonify({
            "response": final_message,
            "session_id": session_id,
            "tools_used": [tc.function.name for tc in tool_calls]
        })

    # If no tool is called, just return the model's direct response
    #-------- Log final results to analytics service (no tools used) --------
    analytics_data = {
        "user_session_id": session_id,
        "agent_id": agent_id,
        "user_id": user_id,
        "trace_id": trace_id,
        "message_type": "ai",
        "content": response_message.content,
        "model": AZURE_OPENAI_DEPLOYMENT,
        "response_time_ms": first_response_time,
        "tool_calls_made": 0
    }
    call_analytics_service("chat/log-message", data=analytics_data)
    #------------------------------------------------------------ 
    return jsonify({
        "response": response_message.content,
        "session_id": session_id,
        "tools_used": []
    })

if __name__ == '__main__':
    print("[Banking Service] Connecting to database...")
    print("You may be prompted for credentials...")
    
    with app.app_context():
        db.create_all()
        print("[Banking Service] Database initialized")

    print("Starting Banking Service on port 5001...")
    app.run(debug=False, port=5001, use_reloader=False)