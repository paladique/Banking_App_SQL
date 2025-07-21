# 🏦  AI Banking App with SQL, Flask and Typescript

**AI Banking App** is an interactive web application designed to simulate a modern banking dashboard. Its primary purpose is to serve as an educational tool, demonstrating how SQL-based databases are leveraged across different types of workloads: **OLTP**, **OLAP**, and **AI-driven analysis**.

Through a hands-on interface, users can see the practical difference between writing a new transaction to the database, running complex analytical queries on historical data, and using natural language to ask an AI to query the database for them.

---

## ✨ Features

- **Dashboard**: A central hub to view account balance and navigate the application.
- **Transactions (OLTP)**: View a real-time list of all past transactions. This demonstrates a typical high-volume, read-heavy OLTP workload.
- **Money Transfer (OLTP)**: Perform transfers between accounts. This showcases a classic atomic, write-heavy OLTP operation that must be fast and reliable.
- **Financial Analytics (OLAP)**: Explore an analytics dashboard with charts and summaries of spending habits. This represents an OLAP workload, running complex, aggregate queries over a large dataset.
- **AI Agent (AI Workload)**: 
    - Ask questions about your finances in plain English (e.g., "How much did I spend on groceries last month?"). An AI agent translates your question into a SQL query, executes it, and returns the answer.
    - Get customer support from using RAG over documents
    - Open new account, transfer money in plain English through an action oriented data agent

---

## 🛠️ Tech Stack

| Layer    | Technology                            |
| -------- | ------------------------------------- |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Backend  | Python, Flask, LangChain              |
| Database | Azure SQL Database                    |
| AI       | Azure OpenAI API                      |

---

## 🚀 Getting Started - Run locally

### 🔧 Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later)
- [Python](https://www.python.org/) (v3.9 or later)
- An [Azure SQL Database](https://azure.microsoft.com/en-us/services/sql-database/) account with an Entra ID application registered
- An [Azure OpenAI API Key](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
- ODBC Driver for SQL Server 18
- Recommend VSCode as tested in VS Code only

---

### 📅 1. Clone the Repository

```bash
git clone https://github.com/arno756/Banking_App_SQL.git
cd Banking_App_SQL
```


### ⚙️ 2. Configure the Backend (Flask API)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` directory:

```env
DB_SERVER="<YOUR_AZURE_SQL_CONNECTION_STRING_URI.database.windows.net>"
DB_DATABASE="banking_app"
DB_DRIVER="ODBC Driver 18 for SQL Server"

AZURE_CLIENT_ID="<YOUR_AZURE_CLIENT_ID>"
AZURE_CLIENT_SECRET="<YOUR_AZURE_CLIENT_SECRET>"
AZURE_TENANT_ID="<YOUR_AZURE_TENANT_ID>"

AZURE_OPENAI_KEY="<YOUR_OPENAI_API_KEY>"
AZURE_OPENAI_ENDPOINT="<YOUR_OPENAI_ENDPOINT.openai.azure.com/>"
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

```

---

### 💻 3. Configure the Frontend (React + Vite)

From the root project directory:

```bash
npm install
```

---

### ▶️ 4. Run Jupyter Notebook to create embeddings from the PDF Document

You need to ingest embeddings from the PDF in the SQL Database

a. Copy the .env file in the folder **Data_Ingest**.
b. From the folder **Data_Ingest** create a new virtual Python environment:

```bash
python3 -m venv new_env
source new_env/bin/activate  # Or .\new_env\Scripts\activate on Windows
pip install -r requirements.txt
```

c. Open the Jupyter Python Notebook in the path: Backend/Documentation ingestion_pdf_Bank_App.ipynb
d. Run all the cells in the notebook

### ▶️ 5. Run the Application

#### Terminal 1: Start Backend

```bash
cd backend
python3 app.py
```

Backend will run on: [http://127.0.0.1:5001](http://127.0.0.1:5001)

#### Terminal 2: Start Frontend

Go to the root of your folder.

```bash
npm run dev
```

Frontend will run on: [http://localhost:5173](http://localhost:5173)

---

## 🤝 Contributing

Contributions are welcome!\
If you have suggestions for improvements or find any bugs, feel free to [open an issue](https://github.com/Banking_App_SQL/issues) or submit a pull request.
