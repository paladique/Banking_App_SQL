import React, { useState } from 'react';
import { DollarSign, FileText, User, CreditCard, Check, AlertCircle } from 'lucide-react';
import type { Vendor, Invoice } from '../types/accounts-receivable';

interface TransferProps {
  vendors: Vendor[];
  onPaymentComplete: (paymentData: any, fromAccountName: string, toAccountName?: string) => void;
  onVendorCreate: (vendorData: { name: string, email: string, phone?: string }) => Promise<any>;
}

const Transfer: React.FC<TransferProps> = ({ vendors, onPaymentComplete, onVendorCreate }) => {
  const [paymentType, setPaymentType] = useState<'invoice' | 'vendor'>('invoice');
  const [selectedVendor, setSelectedVendor] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState('');
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('check');
  const [notes, setNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  // State for creating a new vendor
  const [isCreatingNewVendor, setIsCreatingNewVendor] = useState(false);
  const [newVendorName, setNewVendorName] = useState('');
  const [newVendorEmail, setNewVendorEmail] = useState('');
  const [newVendorPhone, setNewVendorPhone] = useState('');

  // Mock invoices for the selected vendor (in real app, this would come from props)
  const mockInvoices: Invoice[] = [
    {
      id: 'inv-001',
      invoice_number: 'INV-001',
      vendor_id: selectedVendor,
      amount: 1500.00,
      description: 'Office supplies delivery',
      invoice_date: '2025-07-15',
      due_date: '2025-08-15',
      paid: false,
      status: 'Pending',
      created_at: '2025-07-15',
      updated_at: '2025-07-15'
    },
    {
      id: 'inv-002',
      invoice_number: 'INV-002',
      vendor_id: selectedVendor,
      amount: 2300.50,
      description: 'Marketing services',
      invoice_date: '2025-07-20',
      due_date: '2025-08-20',
      paid: false,
      status: 'Overdue',
      created_at: '2025-07-20',
      updated_at: '2025-07-20'
    }
  ];

  const vendorInvoices = selectedVendor ? mockInvoices.filter(inv => inv.vendor_id === selectedVendor) : [];

  const handlePayment = async () => {
    if (!amount || (!selectedInvoice && paymentType === 'invoice')) return;

    setIsProcessing(true);

    try {
      const paymentData = {
        invoice_id: paymentType === 'invoice' ? selectedInvoice : undefined,
        vendor_id: selectedVendor,
        amount: parseFloat(amount),
        payment_method: paymentMethod,
        description: notes || 'Payment processed via AR system'
      };

      if (isCreatingNewVendor && newVendorName && newVendorEmail) {
        // Create the new vendor first
        await onVendorCreate({
          name: newVendorName,
          email: newVendorEmail,
          phone: newVendorPhone || undefined
        });
      }

      await onPaymentComplete(paymentData, 'Zava', selectedVendor);
      
      setShowConfirmation(true);
      setTimeout(() => {
        // Reset form
        setShowConfirmation(false);
        setSelectedVendor('');
        setSelectedInvoice('');
        setAmount('');
        setNotes('');
        setIsCreatingNewVendor(false);
        setNewVendorName('');
        setNewVendorEmail('');
        setNewVendorPhone('');
      }, 3000);

    } catch (error) {
      console.error("Payment failed:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const selectedVendorObj = vendors.find(v => v.id === selectedVendor);
  const selectedInvoiceObj = vendorInvoices.find(inv => inv.id === selectedInvoice);
  const paymentAmount = parseFloat(amount) || 0;

  if (showConfirmation) {
    return (
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Processed!</h2>
        <p className="text-gray-600">${paymentAmount.toLocaleString()} has been processed successfully.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Process Payment</h2>
        
        {/* Payment Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Payment Type</label>
          <div className="flex space-x-4">
            <button
              onClick={() => setPaymentType('invoice')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                paymentType === 'invoice' 
                  ? 'border-blue-500 bg-blue-50 text-blue-700' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <FileText className="h-6 w-6 mx-auto mb-2" />
              <div className="font-medium">Invoice Payment</div>
              <div className="text-sm text-gray-500">Pay specific invoice</div>
            </button>
            <button
              onClick={() => setPaymentType('vendor')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                paymentType === 'vendor' 
                  ? 'border-blue-500 bg-blue-50 text-blue-700' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <User className="h-6 w-6 mx-auto mb-2" />
              <div className="font-medium">Vendor Payment</div>
              <div className="text-sm text-gray-500">General payment to vendor</div>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Payment Form */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Vendor</label>
              <select
                value={selectedVendor}
                onChange={(e) => setSelectedVendor(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Choose a vendor...</option>
                {vendors.filter(v => v.is_active).map(vendor => (
                  <option key={vendor.id} value={vendor.id}>{vendor.name}</option>
                ))}
              </select>
              
              <button
                onClick={() => setIsCreatingNewVendor(!isCreatingNewVendor)}
                className="mt-2 text-sm text-blue-600 hover:text-blue-500"
              >
                {isCreatingNewVendor ? 'Cancel' : '+ Create New Vendor'}
              </button>
            </div>

            {isCreatingNewVendor && (
              <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                <h4 className="font-medium text-gray-900">Create New Vendor</h4>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Vendor Name</label>
                  <input
                    type="text"
                    value={newVendorName}
                    onChange={(e) => setNewVendorName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter vendor name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={newVendorEmail}
                    onChange={(e) => setNewVendorEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="vendor@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone (Optional)</label>
                  <input
                    type="tel"
                    value={newVendorPhone}
                    onChange={(e) => setNewVendorPhone(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>
            )}

            {paymentType === 'invoice' && selectedVendor && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Invoice</label>
                <select
                  value={selectedInvoice}
                  onChange={(e) => setSelectedInvoice(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Choose an invoice...</option>
                  {vendorInvoices.map(invoice => (
                    <option key={invoice.id} value={invoice.id}>
                      {invoice.invoice_number} - ${invoice.amount.toLocaleString()} ({invoice.status})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Payment Amount</label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                />
              </div>
              {selectedInvoiceObj && (
                <p className="mt-1 text-sm text-gray-500">
                  Invoice amount: ${selectedInvoiceObj.amount.toLocaleString()}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Payment Method</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="check">Check</option>
                <option value="ach">ACH Transfer</option>
                <option value="wire">Wire Transfer</option>
                <option value="credit_card">Credit Card</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Notes (Optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Add any notes about this payment..."
              />
            </div>
          </div>

          {/* Payment Summary */}
          <div className="bg-gray-50 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Payment Summary</h3>
            
            {selectedVendorObj && (
              <div className="mb-4 p-4 bg-white rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <User className="h-5 w-5 text-gray-400" />
                  <span className="font-medium">{selectedVendorObj.name}</span>
                </div>
                <p className="text-sm text-gray-500">{selectedVendorObj.email}</p>
                {selectedVendorObj.phone && (
                  <p className="text-sm text-gray-500">{selectedVendorObj.phone}</p>
                )}
              </div>
            )}

            {selectedInvoiceObj && (
              <div className="mb-4 p-4 bg-white rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <FileText className="h-5 w-5 text-gray-400" />
                  <span className="font-medium">{selectedInvoiceObj.invoice_number}</span>
                </div>
                <p className="text-sm text-gray-500 mb-1">
                  Amount: ${selectedInvoiceObj.amount.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">
                  Due: {new Date(selectedInvoiceObj.due_date).toLocaleDateString()}
                </p>
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-2 ${
                  selectedInvoiceObj.status === 'Paid' ? 'bg-green-100 text-green-800' :
                  selectedInvoiceObj.status === 'Overdue' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {selectedInvoiceObj.status}
                </span>
              </div>
            )}

            {paymentAmount > 0 && (
              <div className="mb-4 p-4 bg-white rounded-lg">
                <div className="flex items-center space-x-3 mb-2">
                  <CreditCard className="h-5 w-5 text-gray-400" />
                  <span className="font-medium">Payment Details</span>
                </div>
                <p className="text-sm text-gray-500 mb-1">
                  Amount: ${paymentAmount.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500 capitalize">
                  Method: {paymentMethod.replace('_', ' ')}
                </p>
              </div>
            )}

            {selectedInvoiceObj && paymentAmount > selectedInvoiceObj.amount && (
              <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start space-x-2">
                <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                <div className="text-sm text-yellow-700">
                  Payment amount exceeds invoice amount by ${(paymentAmount - selectedInvoiceObj.amount).toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 flex justify-center">
          <button
            onClick={handlePayment}
            disabled={isProcessing || !amount || (!selectedVendor && !isCreatingNewVendor)}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? 'Processing...' : `Process Payment`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Transfer;
