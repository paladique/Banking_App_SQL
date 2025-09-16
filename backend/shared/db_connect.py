import struct
import pyodbc
import os
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
load_dotenv(override=True)

def create_azuresql_connection():
    """Create connection for banking database."""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")
    token_bytes = token.token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, attrs_before={1256: token_struct})

def fabricsql_connection_bank_db():
    """Create connection for fabric database."""
    fabric_conn_str = os.getenv("FABRIC_SQL_CONNECTION_URL_BANK_DATA")
    return pyodbc.connect(fabric_conn_str)

def fabricsql_connection_agentic_db():
    """Create connection for fabric database."""
    fabric_conn_str = os.getenv("FABRIC_SQL_CONNECTION_URL")
    return pyodbc.connect(fabric_conn_str)