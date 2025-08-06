import React from 'react';
import { DollarSign, TrendingUp, TrendingDown, Users, FileText, Clock, CheckCircle } from 'lucide-react';
import type { Vendor, Invoice } from '../types/accounts-receivable';

interface DashboardProps {
  vendors: Vendor[];
  invoices: Invoice[];
}

const Dashboard: React.FC<DashboardProps> = ({ vendors, invoices }) => {
  const totalOutstanding = invoices
    .filter(inv => !inv.paid)
    .reduce((sum, inv) => sum + inv.amount, 0);
  
  const overdueAmount = invoices
    .filter(inv => inv.status === 'Overdue')
    .reduce((sum, inv) => sum + inv.amount, 0);
  
  const paidThisMonth = invoices
    .filter(inv => inv.paid && new Date(inv.paid_date || '').getMonth() === new Date().getMonth())
    .reduce((sum, inv) => sum + inv.amount, 0);

  const activeVendors = vendors.filter(v => v.is_active).length;
  const pendingInvoices = invoices.filter(inv => inv.status === 'Pending').length;
  const overdueInvoices = invoices.filter(inv => inv.status === 'Overdue').length;

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 rounded-2xl p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Welcome to Zava AR</h2>
        <p className="text-blue-100 mb-6">Here's an overview of your accounts receivable</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total Outstanding</p>
                <p className="text-2xl font-bold">${totalOutstanding.toLocaleString()}</p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Collected This Month</p>
                <p className="text-2xl font-bold">${paidThisMonth.toLocaleString()}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-200" />
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Active Vendors</p>
                <p className="text-2xl font-bold">{activeVendors}</p>
              </div>
              <Users className="h-8 w-8 text-blue-200" />
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <FileText className="h-6 w-6 text-blue-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Pending Invoices</h3>
                <p className="text-sm text-gray-500">Awaiting payment</p>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-gray-900">{pendingInvoices}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Clock className="h-6 w-6 text-red-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Overdue</h3>
                <p className="text-sm text-gray-500">Past due date</p>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-red-600">{overdueInvoices}</p>
            <p className="text-sm text-gray-500">${overdueAmount.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Paid Invoices</h3>
                <p className="text-sm text-gray-500">This month</p>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-green-600">
              {invoices.filter(inv => inv.paid && new Date(inv.paid_date || '').getMonth() === new Date().getMonth()).length}
            </p>
            <p className="text-sm text-gray-500">${paidThisMonth.toLocaleString()}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Users className="h-6 w-6 text-purple-600" />
              <div>
                <h3 className="font-semibold text-gray-900">Active Vendors</h3>
                <p className="text-sm text-gray-500">Total vendors</p>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-gray-900">{activeVendors}</p>
            <p className="text-sm text-gray-500">of {vendors.length} total</p>
          </div>
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Invoices</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {invoices.slice(0, 5).map((invoice) => {
            const vendor = vendors.find(v => v.id === invoice.vendor_id);
            return (
              <div key={invoice.id} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-full ${
                    invoice.status === 'Paid' ? 'bg-green-100' :
                    invoice.status === 'Overdue' ? 'bg-red-100' :
                    'bg-yellow-100'
                  }`}>
                    {invoice.status === 'Paid' && <CheckCircle className="h-5 w-5 text-green-600" />}
                    {invoice.status === 'Overdue' && <Clock className="h-5 w-5 text-red-600" />}
                    {invoice.status === 'Pending' && <FileText className="h-5 w-5 text-yellow-600" />}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{invoice.invoice_number}</p>
                    <p className="text-sm text-gray-500">{vendor?.name || 'Unknown Vendor'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${
                    invoice.status === 'Paid' ? 'text-green-600' : 
                    invoice.status === 'Overdue' ? 'text-red-600' : 
                    'text-yellow-600'
                  }`}>
                    ${invoice.amount.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-500">
                    Due: {new Date(invoice.due_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
