import React, { useState } from 'react';
import { Search, Filter, Calendar, TrendingUp, TrendingDown, ArrowUpRight, Eye } from 'lucide-react';
import type { Account, Transaction } from '../types/banking';

interface TransactionsProps {
  transactions: Transaction[];
  accounts: Account[];
}

const Transactions: React.FC<TransactionsProps> = ({ transactions, accounts }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedAccount, setSelectedAccount] = useState<string>('all');

  const getAccountName = (accountId: string) => {
    const account = accounts.find(acc => acc.id === accountId);
    return account ? account.name : 'Unknown Account';
  };

  const filteredTransactions = transactions.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = selectedType === 'all' || transaction.type === selectedType;
    const matchesCategory = selectedCategory === 'all' || transaction.category === selectedCategory;
    const matchesAccount = selectedAccount === 'all' || transaction.from_account_id === selectedAccount;

    return matchesSearch && matchesType && matchesCategory && matchesAccount;
  });

  const categories = [...new Set(transactions.map(t => t.category))];
  const types = [...new Set(transactions.map(t => t.type))];

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'payment':
        return <TrendingDown className="h-5 w-5 text-red-600" />;
      case 'deposit':
        return <TrendingUp className="h-5 w-5 text-green-600" />;
      case 'transfer':
        return <ArrowUpRight className="h-5 w-5 text-blue-600" />;
      default:
        return <Eye className="h-5 w-5 text-gray-600" />;
    }
  };

  const getAmountColor = (type: string) => {
    switch (type) {
      case 'payment':
        return 'text-red-600';
      case 'deposit':
        return 'text-green-600';
      case 'transfer':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Transaction History</h2>
        
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Accounts</option>
            {accounts.map(account => (
              <option key={account.id} value={account.id}>{account.name}</option>
            ))}
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Types</option>
            {types.map(type => (
              <option key={type} value={type} className="capitalize">{type}</option>
            ))}
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <button className="flex items-center justify-center px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
            <Filter className="h-4 w-4 mr-2" />
            More Filters
          </button>
        </div>

        {/* Transaction Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Total Income</p>
                <p className="text-2xl font-bold text-green-700">
                  ${transactions.filter(t => t.type === 'deposit').reduce((sum, t) => sum + t.amount, 0).toLocaleString()}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600 font-medium">Total Expenses</p>
                <p className="text-2xl font-bold text-red-700">
                  ${transactions.filter(t => t.type === 'payment').reduce((sum, t) => sum + t.amount, 0).toLocaleString()}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-600" />
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Transfers</p>
                <p className="text-2xl font-bold text-blue-700">
                  ${transactions.filter(t => t.type === 'transfer').reduce((sum, t) => sum + t.amount, 0).toLocaleString()}
                </p>
              </div>
              <ArrowUpRight className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Transactions List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="divide-y divide-gray-200">
          {filteredTransactions.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">No transactions found matching your filters.</p>
            </div>
          ) : (
            filteredTransactions.map((transaction) => (
              <div key={transaction.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-full ${
                      transaction.type === 'payment' ? 'bg-red-100' :
                      transaction.type === 'transfer' ? 'bg-blue-100' :
                      'bg-green-100'
                    }`}>
                      {getTransactionIcon(transaction.type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{transaction.description}</h3>
                      <div className="flex items-center space-x-2 text-sm text-gray-500">
                        <span>{transaction.category}</span>
                        <span>•</span>
                        <span>{getAccountName(transaction.from_account_id)}</span>
                        {transaction.to_account_id && (
                          <>
                            <span>→</span>
                            <span>{getAccountName(transaction.to_account_id)}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-semibold ${getAmountColor(transaction.type)}`}>
                      {transaction.type === 'payment' ? '-' : '+'}${transaction.amount.toLocaleString()}
                    </p>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <span>{new Date(transaction.created_at).toLocaleDateString()}</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        transaction.status === 'completed' ? 'bg-green-100 text-green-800' :
                        transaction.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {transaction.status}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Transactions;