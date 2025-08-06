export interface Vendor {
  id: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  tax_id?: string;
  payment_terms_days: number;
  credit_limit: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  vendor_id: string;
  amount: number;
  description?: string;
  invoice_date: string;
  due_date: string;
  paid: boolean;
  paid_date?: string;
  status: 'Paid' | 'Pending' | 'Overdue';
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: string;
  invoice_id: string;
  amount: number;
  payment_date: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  created_at: string;
}

export interface VendorRequest {
  id: string;
  vendor_id?: string;
  request_type: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  summary?: string;
  response?: string;
  created_at: string;
  processed_at?: string;
}

export interface ARMessage {
  id: string;
  message: string;
  is_user: boolean;
  timestamp: string;
  type?: 'text' | 'payment' | 'invoice' | 'insight';
}

export interface ARInsight {
  category: string;
  amount: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
}
