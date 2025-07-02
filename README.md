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

## 🚀 Getting Started

### 🔧 Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later)
- [Python](https://www.python.org/) (v3.9 or later)
- An [Azure SQL Database](https://azure.microsoft.com/en-us/services/sql-database/) account
- An [OpenAI API Key](https://platform.openai.com/)

---

### 📅 1. Clone the Repository

```bash
git clone https://github.com/arno756/Banking_App_SQL.git
cd Banking_App_SQL
```

---

### 🛠️ 2. Set Up Azure SQL Database (Database)

#### a. Create a New Project

- Go to your [Azure SQL Database](https://azure.microsoft.com/en-us/services/sql-database/) and create a new project.

#### b. Create the Database Schema

- Navigate to the **Query Editor** in Azure SQL Database.
- Click **+ New Query**.
- Paste the contents of `schema.sql` (see below) and run the query.

#### c. Get Your Credentials

From **Connection strings** in Azure SQL Database, note:

- Database URI

---

### 📄 `schema.sql`

```sql
-- Create the accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL UNIQUE,
    balance NUMERIC(15, 2) NOT NULL CHECK (balance >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    type TEXT NOT NULL, -- 'debit' or 'credit'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Create policies to allow users to access their own data
CREATE POLICY "Allow individual user access to their own account" ON accounts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow individual user access to their own transactions" ON transactions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Allow user to insert their own transactions" ON transactions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Function to handle transfers and create transactions
CREATE OR REPLACE FUNCTION transfer_money(
    sender_id UUID,
    recipient_email TEXT,
    transfer_amount NUMERIC
)
RETURNS VOID AS $$
DECLARE
    recipient_id UUID;
BEGIN
    -- Find recipient user_id from email
    SELECT id INTO recipient_id FROM auth.users WHERE email = recipient_email;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Recipient not found';
    END IF;

    -- Debit sender
    UPDATE accounts SET balance = balance - transfer_amount WHERE user_id = sender_id;
    INSERT INTO transactions (user_id, description, amount, type) VALUES (sender_id, 'Transfer to ' || recipient_email, transfer_amount, 'debit');

    -- Credit recipient
    UPDATE accounts SET balance = balance + transfer_amount WHERE user_id = recipient_id;
    INSERT INTO transactions (user_id, description, amount, type) VALUES (recipient_id, 'Transfer from ' || (SELECT email FROM auth.users WHERE id = sender_id), transfer_amount, 'credit');
END;
$$ LANGUAGE plpgsql;
```

---

### ⚙️ 3. Configure the Backend (Flask API)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` directory:

```env
DATABASE_URL="<YOUR_AZURE_SQL_CONNECTION_STRING_URI>"
OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

---

### 💻 4. Configure the Frontend (React + Vite)

From the root project directory:

```bash
npm install
```

Create a `.env.local` file:

```env
VITE_AZURE_SQL_URL="<YOUR_AZURE_SQL_CONNECTION_STRING_URI>"
VITE_BACKEND_URL="http://127.0.0.1:5000"
```

---

### ▶️ 5. Run the Application

#### Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate
flask run
```

Backend will run on: [http://127.0.0.1:5000](http://127.0.0.1:5000)

#### Terminal 2: Start Frontend

```bash
npm run dev
```

Frontend will run on: [http://localhost:5173](http://localhost:5173)

---

## 🤝 Contributing

Contributions are welcome!\
If you have suggestions for improvements or find any bugs, feel free to [open an issue](https://github.com/<your-repo>/issues) or submit a pull request.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
