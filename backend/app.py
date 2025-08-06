import os
import urllib.parse
import uuid
from datetime import datetime, timezone
import json
from dateutil.relativedelta import relativedelta
import numpy as np
from decimal import Decimal

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_sqlserver import SQLServer_VectorStore

# --- Environment and App Initialization ---
load_dotenv(override=True)
app = Flask(__name__)
CORS(app)

# --- Azure OpenAI Configuration ---
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")


if not all([AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_DEPLOYMENT]):
    print("⚠️  Warning: One or more Azure OpenAI environment variables are not set.")
    ai_client = None
    embeddings_client = None
else:
    ai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version="2024-02-15-preview",
    )
    embeddings_client = AzureOpenAIEmbeddings(
        azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        openai_api_version="2024-02-15-preview",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
    )


# --- Database Configuration ---
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
client_id = os.getenv('AZURE_CLIENT_ID')
client_secret = os.getenv('AZURE_CLIENT_SECRET')

if not all([server, database, driver, client_id, client_secret]):
    raise ValueError("Database environment variables for Service Principal are not fully configured.")

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={client_id};"
    f"PWD={client_secret};"
    "Authentication=ActiveDirectoryServicePrincipal;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)
sqlalchemy_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
app.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Vector Store Initialization ---
vector_store = None
if embeddings_client:
    vector_store = SQLServer_VectorStore(
        connection_string=sqlalchemy_url,
        table_name="DocsChunks_Embeddings",
        embedding_function=embeddings_client,
        embedding_length=1536, # Added the required embedding length
        distance_strategy=DistanceStrategy.COSINE,
    )

# --- Database Models ---
# Helper function to get timezone-aware UTC datetime
def utc_now():
    return datetime.now(timezone.utc)

# Helper function to make datetime timezone-aware (UTC) if it's naive
def make_utc_aware(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Helper function to convert model instances to dictionaries
def to_dict_helper(instance):
    d = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            d[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            d[column.name] = float(value)
        else:
            d[column.name] = value
    return d

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"vendor_{uuid.uuid4()}")
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(500))
    tax_id = db.Column(db.String(50))
    payment_terms_days = db.Column(db.Integer, default=30)
    credit_limit = db.Column(db.Numeric(15, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    invoices = db.relationship('Invoice', backref='vendor', lazy=True)
    vendor_requests = db.relationship('VendorRequest', backref='vendor', lazy=True)

    def to_dict(self):
        return to_dict_helper(self)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"invoice_{uuid.uuid4()}")
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    vendor_id = db.Column(db.String(255), db.ForeignKey('vendors.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(1000))
    invoice_date = db.Column(DateTime(timezone=True), default=utc_now)
    due_date = db.Column(DateTime(timezone=True), nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(DateTime(timezone=True))
    created_at = db.Column(DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    payments = db.relationship('Payment', backref='invoice', lazy=True)

    @property
    def status(self):
        if self.paid:
            return 'Paid'
        elif self.due_date < utc_now():
            return 'Overdue'
        else:
            return 'Pending'

    def to_dict(self):
        d = to_dict_helper(self)
        d['status'] = self.status  # Add computed status
        return d

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.String(255), primary_key=True, default=lambda: f"payment_{uuid.uuid4()}")
    invoice_id = db.Column(db.String(255), db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(DateTime(timezone=True), default=utc_now)
    payment_method = db.Column(db.String(50))
    reference_number = db.Column(db.String(100))
    notes = db.Column(db.String(1000))
    created_at = db.Column(DateTime(timezone=True), default=utc_now)

    def to_dict(self):
        return to_dict_helper(self)

class VendorRequest(db.Model):
    __tablename__ = 'vendor_requests'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = db.Column(db.String(255), db.ForeignKey('vendors.id'))
    request_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    summary = db.Column(db.Text)
    response = db.Column(db.Text)
    created_at = db.Column(DateTime(timezone=True), default=utc_now)
    processed_at = db.Column(DateTime(timezone=True))

    def to_dict(self):
        return to_dict_helper(self)

# --- AI Chatbot Tool Definitions ---

def get_vendors(status='active'):
    """Retrieves vendors, optionally filtered by status."""
    try:
        if status == 'active':
            vendors = Vendor.query.filter_by(is_active=True).all()
        else:
            vendors = Vendor.query.all()
        
        if not vendors:
            return "No vendors found."
        
        return json.dumps([
            {
                "name": vendor.name, 
                "email": vendor.email, 
                "payment_terms_days": vendor.payment_terms_days,
                "credit_limit": float(vendor.credit_limit) if vendor.credit_limit else 0,
                "is_active": vendor.is_active
            } 
            for vendor in vendors
        ])
    except Exception as e:
        return f"Error retrieving vendors: {str(e)}"

def get_invoices_summary(status='all', vendor_name=None, time_period='this month'):
    """Provides a summary of invoices. Can be filtered by status, vendor, and time period."""
    try:
        query = Invoice.query
        
        # Filter by status
        if status == 'outstanding':
            query = query.filter_by(paid=False)
        elif status == 'overdue':
            query = query.filter(Invoice.due_date < utc_now(), Invoice.paid == False)
        elif status == 'paid':
            query = query.filter_by(paid=True)
        
        # Filter by vendor
        if vendor_name:
            vendor = Vendor.query.filter_by(name=vendor_name).first()
            if not vendor:
                return json.dumps({"status": "error", "message": f"Vendor '{vendor_name}' not found."})
            query = query.filter_by(vendor_id=vendor.id)
        
        # Filter by time period
        end_date = utc_now()
        if 'last 6 months' in time_period.lower():
            start_date = end_date - relativedelta(months=6)
        elif 'this year' in time_period.lower():
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0)
        else:
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
        
        query = query.filter(Invoice.invoice_date.between(start_date, end_date))
        invoices = query.all()
        
        if not invoices:
            return json.dumps({
                "status": "success", 
                "summary": f"No invoices found for the specified criteria."
            })
        
        total_amount = sum(float(inv.amount) for inv in invoices)
        outstanding_amount = sum(float(inv.amount) for inv in invoices if not inv.paid)
        overdue_amount = sum(float(inv.amount) for inv in invoices if inv.status == 'Overdue')
        
        summary_details = {
            "total_invoices": len(invoices),
            "total_amount": round(total_amount, 2),
            "outstanding_amount": round(outstanding_amount, 2),
            "overdue_amount": round(overdue_amount, 2),
            "period": time_period,
            "vendor_filter": vendor_name or "All Vendors"
        }
        
        return json.dumps({"status": "success", "summary": summary_details})
    except Exception as e:
        print(f"ERROR in get_invoices_summary: {e}")
        return json.dumps({"status": "error", "message": f"An error occurred while generating the invoices summary."})

def search_support_documents(user_question: str):
    """Searches the knowledge base for answers to customer support questions using vector search."""
    if not vector_store:
        return "The vector store is not configured."
    try:
        # Use the vector store to find similar documents
        results = vector_store.similarity_search_with_score(user_question, k=3)
        
        # Filter results by a relevance threshold
        relevant_docs = [doc.page_content for doc, score in results if score < 0.5]
        
        if not relevant_docs:
            return "No relevant support documents found to answer this question."

        # Combine the content of relevant documents into a single context string
        context = "\n\n---\n\n".join(relevant_docs)
        return context

    except Exception as e:
        print(f"ERROR in search_support_documents: {e}")
        return "An error occurred while searching for support documents."

def create_new_vendor(name=None, email=None, phone=None, payment_terms_days=30, credit_limit=0):
    """Creates a new vendor."""
    if not name or not email:
        return json.dumps({"status": "error", "message": "Vendor name and email are required."})
    try:
        new_vendor = Vendor(
            name=name, 
            email=email, 
            phone=phone,
            payment_terms_days=payment_terms_days,
            credit_limit=credit_limit
        )
        db.session.add(new_vendor)
        db.session.commit()
        return json.dumps({
            "status": "success", 
            "message": f"Successfully created new vendor '{name}' with {payment_terms_days} day payment terms.",
            "vendor_id": new_vendor.id, 
            "vendor_name": new_vendor.name
        })
    except Exception as e:
        db.session.rollback()
        return f"Error creating vendor: {str(e)}"

def process_payment(invoice_id=None, amount=0.0, payment_method='check', notes=None):
    """Process a payment against an invoice."""
    if not invoice_id or amount <= 0:
        return json.dumps({"status": "error", "message": "Invoice ID and payment amount are required."})
    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return json.dumps({"status": "error", "message": f"Invoice '{invoice_id}' not found."})
        
        if invoice.paid:
            return json.dumps({"status": "error", "message": "Invoice is already marked as paid."})
        
        # Create payment record
        new_payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=payment_method,
            notes=notes
        )
        
        # Check if this payment covers the full invoice amount
        existing_payments = Payment.query.filter_by(invoice_id=invoice_id).all()
        total_payments = sum(float(p.amount) for p in existing_payments) + float(amount)
        
        if total_payments >= float(invoice.amount):
            invoice.paid = True
            invoice.paid_date = utc_now()
        
        db.session.add(new_payment)
        db.session.commit()
        
        return json.dumps({
            "status": "success", 
            "message": f"Successfully processed payment of ${amount:.2f} for invoice {invoice.invoice_number}."
        })
    except Exception as e:
        db.session.rollback()
        return f"Error processing payment: {str(e)}"
        
# --- API Routes ---
@app.route('/api/vendors', methods=['GET', 'POST'])
def handle_vendors():
    if request.method == 'GET':
        vendors = Vendor.query.all()
        return jsonify([vendor.to_dict() for vendor in vendors])
    if request.method == 'POST':
        data = request.json
        vendor_str = create_new_vendor(
            name=data.get('name'), 
            email=data.get('email'), 
            phone=data.get('phone'),
            payment_terms_days=data.get('payment_terms_days', 30),
            credit_limit=data.get('credit_limit', 0)
        )
        return jsonify(json.loads(vendor_str)), 201

@app.route('/api/invoices', methods=['GET', 'POST'])
def handle_invoices():
    if request.method == 'GET':
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
        return jsonify([invoice.to_dict() for invoice in invoices])
    if request.method == 'POST':
        data = request.json
        # Create new invoice (this would typically be done through an invoice creation function)
        try:
            new_invoice = Invoice(
                invoice_number=data.get('invoice_number'),
                vendor_id=data.get('vendor_id'),
                amount=data.get('amount'),
                description=data.get('description'),
                due_date=make_utc_aware(datetime.strptime(data.get('due_date'), '%Y-%m-%d')) if data.get('due_date') else utc_now() + relativedelta(days=30)
            )
            db.session.add(new_invoice)
            db.session.commit()
            return jsonify(new_invoice.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

@app.route('/api/payments', methods=['GET', 'POST'])
def handle_payments():
    if request.method == 'GET':
        payments = Payment.query.order_by(Payment.created_at.desc()).all()
        return jsonify([payment.to_dict() for payment in payments])
    if request.method == 'POST':
        data = request.json
        result_str = process_payment(
            invoice_id=data.get('invoice_id'),
            amount=data.get('amount'),
            payment_method=data.get('payment_method', 'check'),
            notes=data.get('notes')
        )
        result = json.loads(result_str)
        status_code = 201 if result.get("status") == "success" else 400
        return jsonify(result), status_code

@app.route('/api/vendor-requests', methods=['GET', 'POST'])
def handle_vendor_requests():
    if request.method == 'GET':
        requests = VendorRequest.query.order_by(VendorRequest.created_at.desc()).all()
        return jsonify([req.to_dict() for req in requests])
    if request.method == 'POST':
        data = request.json
        try:
            new_request = VendorRequest(
                vendor_id=data.get('vendor_id'),
                request_type=data.get('request_type'),
                summary=data.get('summary')
            )
            db.session.add(new_request)
            db.session.commit()
            return jsonify(new_request.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

@app.route('/api/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """Get a summary of key AR metrics for the dashboard."""
    try:
        total_outstanding = db.session.query(db.func.sum(Invoice.amount)).filter_by(paid=False).scalar() or 0
        total_overdue = db.session.query(db.func.sum(Invoice.amount)).filter(
            Invoice.paid == False, 
            Invoice.due_date < utc_now()
        ).scalar() or 0
        
        active_vendors = Vendor.query.filter_by(is_active=True).count()
        pending_invoices = Invoice.query.filter_by(paid=False).count()
        overdue_invoices = Invoice.query.filter(
            Invoice.paid == False,
            Invoice.due_date < utc_now()
        ).count()
        
        # Collections this month
        start_of_month = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        collections_this_month = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_date >= start_of_month
        ).scalar() or 0
        
        return jsonify({
            "total_outstanding": round(float(total_outstanding), 2),
            "total_overdue": round(float(total_overdue), 2),
            "collections_this_month": round(float(collections_this_month), 2),
            "active_vendors": active_vendors,
            "pending_invoices": pending_invoices,
            "overdue_invoices": overdue_invoices
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    if not ai_client:
        return jsonify({"error": "Azure OpenAI client is not configured."}), 503

    data = request.json
    messages = data.get("messages", [])

    tools = [
        {"type": "function", "function": {
            "name": "get_vendors",
            "description": "Get a list of vendors, optionally filtered by status.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "status": {"type": "string", "enum": ["active", "all"], "description": "Filter vendors by status"}
                }
            }
        }},
        {"type": "function", "function": {
            "name": "get_invoices_summary",
            "description": "Get a summary of invoices, filterable by status, vendor, and time period.",
             "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["all", "outstanding", "overdue", "paid"], "description": "Filter by invoice status"},
                    "vendor_name": {"type": "string", "description": "Filter by specific vendor name"},
                    "time_period": {"type": "string", "description": "e.g., 'this month', 'last 6 months'."}
                },
            }
        }},
        {"type": "function", "function": {
            "name": "search_support_documents",
            "description": "Use this for accounts receivable support questions, policies, or process questions.",
             "parameters": {
                "type": "object",
                "properties": {"user_question": {"type": "string", "description": "The user's full question."}},
                "required": ["user_question"]
            }
        }},
        {"type": "function", "function": {
            "name": "create_new_vendor",
            "description": "Creates a new vendor in the system.",
            "parameters": {"type": "object", "properties": {
                "name": {"type": "string", "description": "The vendor name."},
                "email": {"type": "string", "description": "The vendor email address."},
                "phone": {"type": "string", "description": "The vendor phone number."},
                "payment_terms_days": {"type": "number", "description": "Payment terms in days."},
                "credit_limit": {"type": "number", "description": "Credit limit amount."}
            }, "required": ["name", "email"]
            }
        }},
        {"type": "function", "function": {
            "name": "process_payment",
            "description": "Process a payment against an invoice.",
            "parameters": {"type": "object", "properties": {
                "invoice_id": {"type": "string", "description": "The invoice ID to pay against."}, 
                "amount": {"type": "number", "description": "Payment amount."},
                "payment_method": {"type": "string", "description": "Payment method (check, wire, ach, etc.)"},
                "notes": {"type": "string", "description": "Payment notes or reference."}
                }, "required": ["invoice_id", "amount"]
            }
        }}
    ]

    # First API call to decide if a tool should be used
    response = ai_client.chat.completions.create(model=AZURE_OPENAI_DEPLOYMENT, messages=messages, tools=tools, tool_choice="auto")
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)
        available_functions = {
            "get_vendors": get_vendors,
            "get_invoices_summary": get_invoices_summary,
            "search_support_documents": search_support_documents,
            "create_new_vendor": create_new_vendor,
            "process_payment": process_payment,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            
            tool_message_content = function_response
            # If the tool call was for RAG, prepend the instruction to the content.
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
        final_message = second_response.choices[0].message.content
        return jsonify({"response": final_message})

    # If no tool is called, just return the model's direct response
    return jsonify({"response": response_message.content})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
