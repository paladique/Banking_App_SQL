import React from 'react';
import { DollarSign, TrendingUp, TrendingDown, Target, Clock, Users, FileText, AlertTriangle } from 'lucide-react';
import type { Vendor, Invoice } from '../types/accounts-receivable';

interface AnalyticsProps {
  invoices: Invoice[];
  vendors: Vendor[];
}

const Analytics: React.FC<AnalyticsProps> = ({ invoices, vendors }) => {
  // Calculate key metrics
  const totalOutstanding = invoices.filter(inv => !inv.paid).reduce((sum, inv) => sum + inv.amount, 0);
  const totalOverdue = invoices.filter(inv => inv.status === 'Overdue').reduce((sum, inv) => sum + inv.amount, 0);
  const totalPaidThisMonth = invoices
    .filter(inv => inv.paid && new Date(inv.paid_date || '').getMonth() === new Date().getMonth())
    .reduce((sum, inv) => sum + inv.amount, 0);
  
  const activeVendors = vendors.filter(v => v.is_active).length;
  const overdueInvoices = invoices.filter(inv => inv.status === 'Overdue').length;
  const avgPaymentTerms = vendors.reduce((sum, v) => sum + v.payment_terms_days, 0) / vendors.length;
  
  // Days Sales Outstanding (DSO) - simplified calculation
  const avgInvoiceAmount = invoices.reduce((sum, inv) => sum + inv.amount, 0) / invoices.length;
  const dso = totalOutstanding / (avgInvoiceAmount / 30) || 0;

  // Aging analysis
  const currentDate = new Date();
  const aging = {
    current: 0,
    '1-30': 0,
    '31-60': 0,
    '61-90': 0,
    '90+': 0
  };

  invoices.filter(inv => !inv.paid).forEach(invoice => {
    const dueDate = new Date(invoice.due_date);
    const daysPastDue = Math.floor((currentDate.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24));
    
    if (daysPastDue <= 0) {
      aging.current += invoice.amount;
    } else if (daysPastDue <= 30) {
      aging['1-30'] += invoice.amount;
    } else if (daysPastDue <= 60) {
      aging['31-60'] += invoice.amount;
    } else if (daysPastDue <= 90) {
      aging['61-90'] += invoice.amount;
    } else {
      aging['90+'] += invoice.amount;
    }
  });

  // Vendor analysis
  const vendorAnalysis = vendors.map(vendor => {
    const vendorInvoices = invoices.filter(inv => inv.vendor_id === vendor.id);
    const outstandingAmount = vendorInvoices.filter(inv => !inv.paid).reduce((sum, inv) => sum + inv.amount, 0);
    const overdueAmount = vendorInvoices.filter(inv => inv.status === 'Overdue').reduce((sum, inv) => sum + inv.amount, 0);
    
    return {
      ...vendor,
      totalInvoices: vendorInvoices.length,
      outstandingAmount,
      overdueAmount,
      riskLevel: overdueAmount > vendor.credit_limit * 0.8 ? 'high' : 
                 overdueAmount > vendor.credit_limit * 0.5 ? 'medium' : 'low'
    };
  }).sort((a, b) => b.outstandingAmount - a.outstandingAmount);

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Total Outstanding</h3>
              <p className="text-3xl font-bold">${totalOutstanding.toLocaleString()}</p>
            </div>
            <DollarSign className="h-8 w-8 text-blue-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-red-500 to-red-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Overdue Amount</h3>
              <p className="text-3xl font-bold">${totalOverdue.toLocaleString()}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Collected This Month</h3>
              <p className="text-3xl font-bold">${totalPaidThisMonth.toLocaleString()}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-200" />
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Days Sales Outstanding</h3>
              <p className="text-3xl font-bold">{Math.round(dso)}</p>
            </div>
            <Clock className="h-8 w-8 text-purple-200" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Aging Analysis */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Aging Analysis</h3>
            <Clock className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            {Object.entries(aging).map(([period, amount]) => {
              const percentage = totalOutstanding > 0 ? (amount / totalOutstanding) * 100 : 0;
              return (
                <div key={period} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded ${
                      period === 'current' ? 'bg-green-500' :
                      period === '1-30' ? 'bg-yellow-500' :
                      period === '31-60' ? 'bg-orange-500' :
                      period === '61-90' ? 'bg-red-500' :
                      'bg-red-700'
                    }`}></div>
                    <span className="text-sm font-medium text-gray-700">
                      {period === 'current' ? 'Current' : `${period} days`}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">${amount.toLocaleString()}</p>
                    <p className="text-xs text-gray-500">{percentage.toFixed(1)}%</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Vendors by Outstanding */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Top Vendors by Outstanding</h3>
            <Users className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            {vendorAnalysis.slice(0, 5).map((vendor) => (
              <div key={vendor.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    vendor.riskLevel === 'high' ? 'bg-red-500' :
                    vendor.riskLevel === 'medium' ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}></div>
                  <div>
                    <p className="font-medium text-gray-900">{vendor.name}</p>
                    <p className="text-xs text-gray-500">{vendor.totalInvoices} invoices</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">${vendor.outstandingAmount.toLocaleString()}</p>
                  {vendor.overdueAmount > 0 && (
                    <p className="text-xs text-red-600">${vendor.overdueAmount.toLocaleString()} overdue</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Collection Efficiency */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Collection Performance</h3>
            <Target className="h-5 w-5 text-gray-400" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{activeVendors}</div>
              <div className="text-sm text-gray-600">Active Vendors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{overdueInvoices}</div>
              <div className="text-sm text-gray-600">Overdue Invoices</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{Math.round(avgPaymentTerms)}</div>
              <div className="text-sm text-gray-600">Avg Payment Terms</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {totalOutstanding > 0 ? Math.round((totalOverdue / totalOutstanding) * 100) : 0}%
              </div>
              <div className="text-sm text-gray-600">Overdue Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Vendor Risk Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendorAnalysis.filter(v => v.riskLevel === 'high').slice(0, 3).map((vendor) => (
            <div key={vendor.id} className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-red-900">{vendor.name}</h4>
                <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">High Risk</span>
              </div>
              <p className="text-sm text-red-700 mb-1">
                Outstanding: ${vendor.outstandingAmount.toLocaleString()}
              </p>
              <p className="text-sm text-red-700 mb-1">
                Overdue: ${vendor.overdueAmount.toLocaleString()}
              </p>
              <p className="text-sm text-red-700">
                Credit Limit: ${vendor.credit_limit.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
