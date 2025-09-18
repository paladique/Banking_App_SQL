import requests
import msal
import json
import traceback
from mssql_python import connect
from typing import Dict, Tuple, Optional, List

# --- configuration helper ---------------------------------------------------
def load_config(path: str = "config.json") -> Dict:
    return json.load(open(path))


# --- Fabric API helpers ----------------------------------------------------
def make_client(access_token: str) -> requests.Session:
    client = requests.Session()
    client.headers.update({"Authorization": "Bearer " + access_token})
    client.base_url = "https://api.fabric.microsoft.com/v1/"
    return client


def list_sql_databases(client: requests.Session, workspace_id: str) -> List[Dict]:
    resp = client.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases")
    resp.raise_for_status()
    return resp.json().get("value", [])


def get_workspace_id(client: requests.Session) -> str:
    resp = client.get("https://api.fabric.microsoft.com/v1/workspaces")
    resp.raise_for_status()
    return resp.json()["value"][0]["id"]


def find_database_by_displayname(databases: List[Dict], display_name: str) -> Optional[Dict]:
    target = display_name.lower()
    return next((db for db in databases if db.get("displayName", "").lower() == target), None)


def build_conn_string_from_props(server_fqdn: str, database_name: str,
                                 encrypt: bool = True,
                                 trust_server_certificate: bool = False,
                                 authentication: str = "ActiveDirectoryInteractive") -> str:
    # Normalize to driver-friendly values: Encrypt=yes/no, TrustServerCertificate=yes/no
    enc = "yes" if encrypt else "no"
    tsc = "yes" if trust_server_certificate else "no"
    return f"Server={server_fqdn};Database={{{database_name}}};Encrypt={enc};TrustServerCertificate={tsc};Authentication={authentication}"


# --- DB helpers -------------------------------------------------------------
def safe_connect(conn_str: str):
    """Return (conn, cursor). Caller must close both (cursor.close(); conn.close())."""
    conn = connect(conn_str)
    cursor = conn.cursor()
    return conn, cursor


def exec_script(cursor, script: str):
    """Execute a multi-statement SQL script via cursor.execute then commit outside."""
    cursor.execute(script)


def close_quietly(cursor, conn):
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if conn:
            conn.close()
    except Exception:
        pass


# --- schema / data operations ----------------------------------------------
def create_core_schema(cursor):
    """
    Create core tables (users, accounts, transactions) after dropping dependent objects
    in a safe order.
    """
    sql = """
-- Drop dependent tables first, then referenced ones
IF OBJECT_ID('tool_usage', 'U') IS NOT NULL DROP TABLE tool_usage;
IF OBJECT_ID('chat_history', 'U') IS NOT NULL DROP TABLE chat_history;
IF OBJECT_ID('tool_definitions', 'U') IS NOT NULL DROP TABLE tool_definitions;
IF OBJECT_ID('agent_definitions', 'U') IS NOT NULL DROP TABLE agent_definitions;
IF OBJECT_ID('chat_sessions', 'U') IS NOT NULL DROP TABLE chat_sessions;
IF OBJECT_ID('transactions', 'U') IS NOT NULL DROP TABLE transactions;
IF OBJECT_ID('accounts', 'U') IS NOT NULL DROP TABLE accounts;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

CREATE TABLE users (
    id NVARCHAR(255) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);

CREATE TABLE accounts (
    id NVARCHAR(255) PRIMARY KEY,
    user_id NVARCHAR(255) FOREIGN KEY REFERENCES users(id),
    account_number NVARCHAR(255) UNIQUE NOT NULL,
    account_type NVARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);

CREATE TABLE transactions (
    id NVARCHAR(255) PRIMARY KEY,
    from_account_id NVARCHAR(255) FOREIGN KEY REFERENCES accounts(id),
    to_account_id NVARCHAR(255) FOREIGN KEY REFERENCES accounts(id),
    amount DECIMAL(15, 2) NOT NULL,
    type NVARCHAR(255) NOT NULL,
    description NTEXT,
    category NVARCHAR(255),
    status NVARCHAR(255) NOT NULL,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);
"""
    exec_script(cursor, sql)


def insert_core_data(cursor):
    SQL_USER_INSERT = """
INSERT INTO users (id, name, email, created_at)
VALUES (?, ?, ?, ?);
"""
    SQL_ACCOUNT_INSERT = """
INSERT INTO accounts (id, user_id, account_number, account_type, balance, name, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?);
"""
    SQL_TRANSACTION_INSERT = """
INSERT INTO transactions (id, from_account_id, to_account_id, amount, type, description, category, status, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
    users_data = [
        ("user_1", "John Doe", "john.doe@example.com", "2025-06-24T02:44:13.180Z"),
        ("user_2", "Jane Smith", "jane.smith@example.com", "2025-06-24T02:44:13.180Z"),
        ("user_3", "Alice Johnson", "alice.johnson@example.com", "2025-06-24T02:44:13.180Z"),
        ("user_4", "Bob Brown", "bob.brown@example.com", "2025-06-24T02:44:13.180Z"),
        ("user_5", "Charlie Davis", "charlie.davis@example.com", "2025-06-24T02:44:13.180Z"),
        ("user_6", "Diana Evans", "diana.evans@example.com", "2025-06-24T02:44:13.180Z"),
    ]
    accounts_data = [
        ('acc_1', 'user_1', '123456789', 'checking', 4822.50, 'Primary Checking', '2025-06-24T02:44:13.197Z'),
        ('acc_2', 'user_1', '987654321', 'savings', 13015.00, 'High-Yield Savings', '2025-06-24T02:44:13.197Z'),
        ('acc_3', 'user_1', '112233445', 'credit', -490.00, 'Platinum Credit Card', '2025-06-24T02:44:13.197Z'),
        ('acc_4', 'user_2', '223344556', 'checking', 3050.75, 'Everyday Checking', '2025-06-24T02:44:13.197Z'),
        ('acc_5', 'user_2', '665544332', 'savings', 8450.00, 'Vacation Savings', '2025-06-24T02:44:13.197Z'),
        ('acc_6', 'user_3', '334455667', 'checking', 1500.00, 'Student Checking', '2025-06-24T02:44:13.197Z'),
        ('acc_7', 'user_3', '778899001', 'credit', -1200.00, 'Student Credit Card', '2025-06-24T02:44:13.197Z'),
        ('acc_8', 'user_4', '445566778', 'checking', 7200.00, 'Joint Checking', '2025-06-24T02:44:13.197Z'),
        ('acc_9', 'user_5', '556677889', 'savings', 5600.00, 'Emergency Fund', '2025-06-24T02:44:13.197Z'),
        ('acc_10', 'user_6', '667788990', 'checking', 4300.25, 'Business Checking', '2025-06-24T02:44:13.197Z'),
        ('acc_11', 'user_6', '998877665', 'credit', -750.00, 'Business Credit Card', '2025-06-24T02:44:13.197Z'),
        ('acc_12', 'user_5', '776655443', 'checking', 2200.00, 'Secondary Checking', '2025-06-24T02:44:13.197Z'),
    ]
    transactions_data = [
        ('txn_1', 'acc_1', None, 75.00, 'payment', 'Grocery Store', 'Groceries', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_2', 'acc_1', None, 1200.00, 'payment', 'Rent Payment', 'Housing', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_3', None, 'acc_1', 3000.00, 'deposit', 'Paycheck', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_4', 'acc_1', 'acc_2', 500.00, 'transfer', 'Monthly Savings', 'Transfer', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_5', 'acc_3', None, 150.00, 'payment', 'Dinner with Friends', 'Food', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_6', 'acc_1', None, 25.50, 'payment', 'Coffee Shop', 'Food', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_7', 'acc_2', None, 200.00, 'payment', 'Electronics Store', 'Shopping', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_8', None, 'acc_2', 1500.00, 'deposit', 'Freelance Project', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_9', 'acc_4', None, 60.00, 'payment', 'Gas Station', 'Transportation', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_10', 'acc_4', None, 300.00, 'payment', 'Utility Bill', 'Utilities', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_11', None, 'acc_4', 2500.00, 'deposit', 'Salary Deposit', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_12', 'acc_5', None, 100.00, 'payment', 'Bookstore', 'Education', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_13', None, 'acc_5', 800.00, 'deposit', 'Tax Refund', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_14', 'acc_6', None, 45.00, 'payment', 'Fast Food Restaurant', 'Food', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_15', None, 'acc_6', 1200.00, 'deposit', 'Parent Gift', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_16', 'acc_7', None, 300.00, 'payment', 'Online Shopping', 'Shopping', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_17', None, 'acc_7', 500.00, 'deposit', 'Scholarship', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_18', 'acc_8', None, 400.00, 'payment', 'Home Improvement Store', 'Home', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_19', None, 'acc_8', 3500.00, 'deposit', 'Bonus Payment', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_20', 'acc_9', None, 75.00, 'payment', 'Pharmacy', 'Health', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_21', None, 'acc_9', 600.00, 'deposit', 'Gift from Friend', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_22', 'acc_10', None, 250.00, 'payment', 'Office Supplies Store', 'Business Expenses', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_23', None, 'acc_10', 4000.00, 'deposit', 'Client Payment', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_24', 'acc_11', None, 100.00, 'payment', 'Business Lunch', 'Business Expenses', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_25', None, 'acc_11', 1200.00, 'deposit', 'Investor Funding', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_26', 'acc_12', None, 60.00, 'payment', 'Grocery Store', 'Groceries', 'completed', '2025-06-24T02:44:13.217Z'),
        ('txn_27', None, 'acc_12', 700.00, 'deposit', 'Side Business Income', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
    ]
    cursor.executemany(SQL_USER_INSERT, users_data)
    cursor.executemany(SQL_ACCOUNT_INSERT, accounts_data)
    cursor.executemany(SQL_TRANSACTION_INSERT, transactions_data)


def create_banking_app_schema(cursor):
    """
    Create schema for banking_app (agent/tool/chat tables). Must ensure chat_sessions exists
    before creating FK from chat_history.
    """
    sql = """
-- Create chat/agent/tool tables (assumes none of them exist)
CREATE TABLE chat_sessions (
    session_id NVARCHAR(255) PRIMARY KEY,
    user_id NVARCHAR(255) NOT NULL,
    title NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE agent_definitions (
    agent_id NVARCHAR(255) PRIMARY KEY,
    name NVARCHAR(255) UNIQUE NOT NULL,  
    description NVARCHAR(MAX),
    llm_config NVARCHAR(MAX) NOT NULL,
    prompt_template NVARCHAR(MAX) NOT NULL
);

CREATE TABLE tool_definitions (
    tool_id NVARCHAR(255) PRIMARY KEY,
    name NVARCHAR(255) UNIQUE NOT NULL,
    description NVARCHAR(MAX),
    input_schema NVARCHAR(MAX) NOT NULL,
    version NVARCHAR(50) DEFAULT '1.0.0',
    is_active BIT DEFAULT 1,
    cost_per_call_cents INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE chat_history (
    message_id NVARCHAR(255) PRIMARY KEY,
    session_id NVARCHAR(255) NOT NULL,
    trace_id NVARCHAR(255) NOT NULL,
    user_id NVARCHAR(255) NOT NULL,
    agent_id NVARCHAR(255),
    message_type NVARCHAR(50) NOT NULL,
    content NVARCHAR(MAX),
    model_name NVARCHAR(255),
    content_filter_results NVARCHAR(MAX) DEFAULT '{}',
    total_tokens INT,
    completion_tokens INT,
    prompt_tokens INT,
    finish_reason NVARCHAR(255),
    response_time_ms INT,
    trace_end NVARCHAR(255),
    tool_call_id NVARCHAR(255),
    tool_name NVARCHAR(255),
    tool_input NVARCHAR(MAX),
    tool_output NVARCHAR(MAX),
    tool_id NVARCHAR(255)
);

CREATE TABLE tool_usage (
    tool_call_id NVARCHAR(255) PRIMARY KEY,
    session_id NVARCHAR(255) NOT NULL,
    trace_id NVARCHAR(255),
    tool_id NVARCHAR(255) NOT NULL,
    tool_name NVARCHAR(255) NOT NULL,
    tool_input NVARCHAR(MAX) NOT NULL,
    tool_output NVARCHAR(MAX),
    status NVARCHAR(50) DEFAULT 'pending',
    tokens_used INT
);

ALTER TABLE chat_history 
ADD CONSTRAINT FK_chat_history_session 
FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id);
"""
    exec_script(cursor, sql)


# --- utility ---------------------------------------------------------------
def redact_conn_str(cs: str) -> str:
    return cs.replace("PWD=", "PWD=REDACTED").replace("Password=", "Password=REDACTED")


# --- orchestration ----------------------------------------------------------
def setup_customer_banking(client: requests.Session, workspace_id: str):
    databases = list_sql_databases(client, workspace_id)
    db = find_database_by_displayname(databases, "customer_banking_data")
    if not db:
        raise RuntimeError("No database with displayName 'customer_banking_data' found")
    banking_db_props = client.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases/{db.get('id')}").json().get("properties", {})
    dbname = banking_db_props.get("databaseName")
    server = banking_db_props.get("serverFqdn")
    if not dbname or not server:
        raise RuntimeError("Could not determine connection properties for customer_banking_data")
    conn_str = build_conn_string_from_props(server, dbname, encrypt=True, trust_server_certificate=False)
    print("Connecting to customer_banking_data with:", redact_conn_str(conn_str))
    conn, cursor = safe_connect(conn_str)
    try:
        create_core_schema(cursor)
        # commit schema creation
        conn.commit()
        insert_core_data(cursor)
        conn.commit()
        print("Inserted core sample data")
    except Exception:
        traceback.print_exc()
        raise
    finally:
        close_quietly(cursor, conn)


def setup_banking_app(client: requests.Session, workspace_id: str):
    databases = list_sql_databases(client, workspace_id)
    db = find_database_by_displayname(databases, "banking_app")
    if not db:
        raise RuntimeError("No database with displayName 'banking_app' found")
    banking_db_props = client.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases/{db.get('id')}").json().get("properties", {})
    dbname = banking_db_props.get("databaseName")
    server = banking_db_props.get("serverFqdn")
    if not dbname or not server:
        raise RuntimeError("Could not determine connection properties for banking_app")
    conn_str = build_conn_string_from_props(server, dbname, encrypt=True, trust_server_certificate=False)
    print("Connecting to banking_app with:", redact_conn_str(conn_str))
    conn, cursor = safe_connect(conn_str)
    try:
        create_banking_app_schema(cursor)
        conn.commit()
        print("Created agent/tool/chat tables in 'banking_app'")
    except Exception:
        traceback.print_exc()
        raise
    finally:
        close_quietly(cursor, conn)


def quick_select_users(client_conn_str: str):
    conn, cursor = safe_connect(client_conn_str)
    try:
        SQL_QUERY = "SELECT TOP 5 * FROM users"
        cursor.execute(SQL_QUERY)
        rows = cursor.fetchall()
        for r in rows:
            print(r)
    finally:
        close_quietly(cursor, conn)


def main():
    cfg = load_config()
    client = make_client(cfg["access_token"])
    workspace_id = get_workspace_id(client)
    print(f"My workspace ID: {workspace_id}")

    # Create the two SQL databases (API calls as in original script)
    client.post(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases", data={
        "displayName": "customer_banking_data",
        "description": "Customer banking data"
    })
    client.post(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases", data={
        "displayName": "banking_app",
        "description": "Stores agentic operational data"
    })

    # refresh list
    print("Enumerating SQL databases...")
    dbs = list_sql_databases(client, workspace_id)
    print([d.get("displayName") for d in dbs])

    # Setup customer_banking_data
    setup_customer_banking(client, workspace_id)

    # Setup banking_app
    setup_banking_app(client, workspace_id)

    # show a quick sample from users table
    # Rebuild a conn string for the customer_banking_data to query
    db = find_database_by_displayname(dbs, "customer_banking_data")
    props = client.get(f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/sqlDatabases/{db.get('id')}").json().get("properties", {})
    dbname = props.get("databaseName")
    server = props.get("serverFqdn")
    sample_conn = build_conn_string_from_props(server, dbname, encrypt=True, trust_server_certificate=False)
    quick_select_users(sample_conn)


if __name__ == "__main__":
    main()