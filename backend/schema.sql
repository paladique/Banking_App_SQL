-- Drop tables if they exist to start from a clean slate
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS vendor_requests;
DROP TABLE IF EXISTS vendors;

-- Create the 'vendors' table (enhanced with business fields)
CREATE TABLE vendors (
    id NVARCHAR(255) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    phone NVARCHAR(50),
    address NVARCHAR(500),
    tax_id NVARCHAR(50),
    payment_terms_days INT DEFAULT 30,
    credit_limit DECIMAL(15, 2),
    is_active BIT DEFAULT 1,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET()
);

-- Create the 'invoices' table (fixed naming consistency and added business fields)
CREATE TABLE invoices (
    id NVARCHAR(255) PRIMARY KEY,
    invoice_number NVARCHAR(100) UNIQUE NOT NULL,
    vendor_id NVARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description NVARCHAR(1000),
    invoice_date DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    due_date DATETIMEOFFSET NOT NULL,
    paid BIT DEFAULT 0,
    paid_date DATETIMEOFFSET NULL,
    status AS CASE 
        WHEN paid = 1 THEN 'Paid'
        WHEN due_date < SYSDATETIMEOFFSET() THEN 'Overdue'
        ELSE 'Pending'
    END,
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    updated_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    CONSTRAINT FK_invoices_vendor_id FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Create payments table to track partial payments
CREATE TABLE payments (
    id NVARCHAR(255) PRIMARY KEY,
    invoice_id NVARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    payment_date DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    payment_method NVARCHAR(50),
    reference_number NVARCHAR(100),
    notes NVARCHAR(1000),
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    CONSTRAINT FK_payments_invoice_id FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

-- Create vendor_requests table (fixed naming consistency and added business fields)
CREATE TABLE vendor_requests (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    vendor_id NVARCHAR(255),
    request_type NVARCHAR(100) NOT NULL,
    status NVARCHAR(50) DEFAULT 'Pending',
    summary NVARCHAR(MAX),
    response NVARCHAR(MAX),
    created_at DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    processed_at DATETIMEOFFSET NULL,
    CONSTRAINT FK_vendor_requests_vendor_id FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Create indexes for better performance in Azure SQL
CREATE NONCLUSTERED INDEX IX_invoices_vendor_id ON invoices(vendor_id);
CREATE NONCLUSTERED INDEX IX_invoices_status ON invoices(paid, due_date);
CREATE NONCLUSTERED INDEX IX_payments_invoice_id ON payments(invoice_id);
CREATE NONCLUSTERED INDEX IX_vendor_requests_vendor_id ON vendor_requests(vendor_id);
CREATE NONCLUSTERED INDEX IX_vendor_requests_status ON vendor_requests(status);