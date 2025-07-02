import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, PiggyBank, Shield } from 'lucide-react';
import type { Account, Transaction } from '../types/banking';

interface DashboardProps {
  accounts: Account[];
  recentTransactions: Transaction[];
}

const Dashboard: React.FC<DashboardProps> = ({ accounts, recentTransactions }) => {
  const totalBalance = accounts.reduce((sum, account) => sum + account.balance, 0);
  const monthlySpending = recentTransactions
    .filter(t => t.type === 'payment' && new Date(t.created_at).getMonth() === new Date().getMonth())
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 rounded-2xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Welcome back, John!</h2>
        <p className="text-blue-100 mb-6">Here's an overview of your financial activity</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Balance</p>
                <p className="text-2xl font-bold">${totalBalance.toLocaleString()}</p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Monthly Spending</p>
                <p className="text-2xl font-bold">${monthlySpending.toLocaleString()}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Active Accounts</p>
                <p className="text-2xl font-bold">{accounts.length}</p>
              </div>
              <Shield className="h-8 w-8 text-blue-200" />
            </div>
          </div>
        </div>
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <div key={account.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                {account.account_type === 'checking' && <CreditCard className="h-6 w-6 text-blue-600" />}
                {account.account_type === 'savings' && <PiggyBank className="h-6 w-6 text-green-600" />}
                {account.account_type === 'credit' && <CreditCard className="h-6 w-6 text-red-600" />}
                <div>
                  <h3 className="font-semibold text-gray-900">{account.name}</h3>
                  <p className="text-sm text-gray-500">***{account.account_number.slice(-4)}</p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-gray-900">${account.balance.toLocaleString()}</p>
              <p className="text-sm text-gray-500 capitalize">{account.account_type} Account</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Transactions</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {recentTransactions.slice(0, 5).map((transaction) => (
            <div key={transaction.id} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-full ${
                  transaction.type === 'payment' ? 'bg-red-100' :
                  transaction.type === 'transfer' ? 'bg-blue-100' :
                  'bg-green-100'
                }`}>
                  {transaction.type === 'payment' && <TrendingDown className="h-4 w-4 text-red-600" />}
                  {transaction.type === 'transfer' && <TrendingUp className="h-4 w-4 text-blue-600" />}
                  {transaction.type === 'deposit' && <TrendingUp className="h-4 w-4 text-green-600" />}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{transaction.description}</p>
                  <p className="text-sm text-gray-500">{transaction.category}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold ${
                  transaction.type === 'payment' ? 'text-red-600' : 'text-green-600'
                }`}>
                  {transaction.type === 'payment' ? '-' : '+'}${transaction.amount.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">
                  {new Date(transaction.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;