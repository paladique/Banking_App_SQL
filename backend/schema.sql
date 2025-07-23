-- Drop tables if they exist to start from a clean slate
IF OBJECT_ID('transactions', 'U') IS NOT NULL DROP TABLE transactions;
IF OBJECT_ID('accounts', 'U') IS NOT NULL DROP TABLE accounts;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

-- Create the 'users' table
CREATE TABLE users (
    id NVARCHAR(255) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);

-- Create the 'accounts' table
CREATE TABLE accounts (
    id NVARCHAR(255) PRIMARY KEY,
    user_id NVARCHAR(255) FOREIGN KEY REFERENCES users(id),
    account_number NVARCHAR(255) UNIQUE NOT NULL,
    account_type NVARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL,
    name NVARCHAR(255) NOT NULL,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);

-- Create the 'transactions' table
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

-- Insert data into the 'users' table
INSERT INTO users (id, name, email, created_at) VALUES
('user_1', 'John Doe', 'john.doe@example.com', '2025-06-24T02:44:13.180Z');

-- Insert data into the 'accounts' table
INSERT INTO accounts (id, user_id, account_number, account_type, balance, name, created_at) VALUES
('acc_1', 'user_1', '123456789', 'checking', 4822.50, 'Primary Checking', '2025-06-24T02:44:13.197Z'),
('acc_2', 'user_1', '987654321', 'savings', 13015.00, 'High-Yield Savings', '2025-06-24T02:44:13.197Z'),
('acc_3', 'user_1', '112233445', 'credit', -490.00, 'Platinum Credit Card', '2025-06-24T02:44:13.197Z');

-- Insert data into the 'transactions' table
INSERT INTO transactions (id, from_account_id, to_account_id, amount, type, description, category, status, created_at) VALUES
('txn_1', 'acc_1', NULL, 75.00, 'payment', 'Grocery Store', 'Groceries', 'completed', '2025-06-24T02:44:13.217Z'),
('txn_2', 'acc_1', NULL, 1200.00, 'payment', 'Rent Payment', 'Housing', 'completed', '2025-06-24T02:44:13.217Z'),
('txn_3', NULL, 'acc_1', 3000.00, 'deposit', 'Paycheck', 'Income', 'completed', '2025-06-24T02:44:13.217Z'),
('txn_4', 'acc_1', 'acc_2', 500.00, 'transfer', 'Monthly Savings', 'Transfer', 'completed', '2025-06-24T02:44:13.217Z'),
('txn_5', 'acc_3', NULL, 150.00, 'payment', 'Dinner with Friends', 'Food', 'completed', '2025-06-24T02:44:13.217Z'),
('txn_6', 'acc_1', NULL, 25.50, 'payment', 'Coffee Shop', 'Food', 'completed', '2025-06-24T02:44:13.217Z');