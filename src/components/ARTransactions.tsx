import React, { useState } from 'react';
import { Search, Filter, FileText, Clock, CheckCircle, DollarSign, Calendar } from 'lucide-react';
import type { Vendor, Invoice } from '../types/accounts-receivable';

interface TransactionsProps {
  invoices: Invoice[];
  vendors: Vendor[];
}

const Transactions: React.FC<TransactionsProps> = ({ invoices, vendors }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedVendor, setSelectedVendor] = useState<string>('all');

  const getVendorName = (vendorId: string) => {
    const vendor = vendors.find(v => v.id === vendorId);
    return vendor ? vendor.name : 'Unknown Vendor';
  };

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (invoice.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         getVendorName(invoice.vendor_id).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = selectedStatus === 'all' || invoice.status === selectedStatus;
    const matchesVendor = selectedVendor === 'all' || invoice.vendor_id === selectedVendor;

    return matchesSearch && matchesStatus && matchesVendor;
  });

  const getInvoiceIcon = (status: string) => {
    switch (status) {
      case 'Paid':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'Overdue':
        return <Clock className="h-5 w-5 text-red-600" />;
      case 'Pending':
        return <FileText className="h-5 w-5 text-yellow-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Paid':
        return 'text-green-600 bg-green-50';
      case 'Overdue':
        return 'text-red-600 bg-red-50';
      case 'Pending':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const paidInvoices = invoices.filter(inv => inv.paid);
  const pendingInvoices = invoices.filter(inv => inv.status === 'Pending');
  const overdueInvoices = invoices.filter(inv => inv.status === 'Overdue');

  const totalPaid = paidInvoices.reduce((sum, inv) => sum + inv.amount, 0);
  const totalPending = pendingInvoices.reduce((sum, inv) => sum + inv.amount, 0);
  const totalOverdue = overdueInvoices.reduce((sum, inv) => sum + inv.amount, 0);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Invoice Management</h2>
        
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search invoices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedVendor}
            onChange={(e) => setSelectedVendor(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Vendors</option>
            {vendors.map(vendor => (
              <option key={vendor.id} value={vendor.id}>{vendor.name}</option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Paid">Paid</option>
            <option value="Overdue">Overdue</option>
          </select>

          <button className="flex items-center justify-center px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
            <Filter className="h-4 w-4 mr-2" />
            More Filters
          </button>
        </div>

        {/* Invoice Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Paid Invoices</p>
                <p className="text-2xl font-bold text-green-900">${totalPaid.toLocaleString()}</p>
                <p className="text-sm text-green-600">{paidInvoices.length} invoices</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">Pending Invoices</p>
                <p className="text-2xl font-bold text-yellow-900">${totalPending.toLocaleString()}</p>
                <p className="text-sm text-yellow-600">{pendingInvoices.length} invoices</p>
              </div>
              <FileText className="h-8 w-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">Overdue Invoices</p>
                <p className="text-2xl font-bold text-red-900">${totalOverdue.toLocaleString()}</p>
                <p className="text-sm text-red-600">{overdueInvoices.length} invoices</p>
              </div>
              <Clock className="h-8 w-8 text-red-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Invoices List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="divide-y divide-gray-200">
          {filteredInvoices.map((invoice) => {
            const vendor = vendors.find(v => v.id === invoice.vendor_id);
            return (
              <div key={invoice.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-full ${
                      invoice.status === 'Paid' ? 'bg-green-100' :
                      invoice.status === 'Overdue' ? 'bg-red-100' :
                      'bg-yellow-100'
                    }`}>
                      {getInvoiceIcon(invoice.status)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-3">
                        <p className="font-semibold text-gray-900">{invoice.invoice_number}</p>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>
                          {invoice.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{vendor?.name || 'Unknown Vendor'}</p>
                      {invoice.description && (
                        <p className="text-sm text-gray-500 mt-1">{invoice.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">${invoice.amount.toLocaleString()}</p>
                    <div className="flex items-center text-sm text-gray-500 mt-1">
                      <Calendar className="h-4 w-4 mr-1" />
                      Due: {new Date(invoice.due_date).toLocaleDateString()}
                    </div>
                    {invoice.paid && invoice.paid_date && (
                      <div className="flex items-center text-sm text-green-600 mt-1">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Paid: {new Date(invoice.paid_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Transactions;
