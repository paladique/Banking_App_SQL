export interface Account {
  id: string;
  user_id: string;
  account_number: string;
  account_type: 'checking' | 'savings' | 'credit';
  balance: number;
  name: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  from_account_id: string;
  to_account_id?: string;
  amount: number;
  type: 'transfer' | 'payment' | 'deposit' | 'withdrawal';
  description: string;
  category: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

export interface ChatMessage {
  id: string;
  message: string;
  is_user: boolean;
  timestamp: string;
  type?: 'text' | 'transaction' | 'insight';
}

export interface SpendingInsight {
  category: string;
  amount: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
}