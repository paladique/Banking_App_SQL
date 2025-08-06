import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/ARDashboard';
import Transactions from './components/ARTransactions';
import Transfer from './components/ARTransfer';
import Analytics from './components/ARAnalytics';
import ChatBot from './components/ChatBot';
import { MessageCircle, X } from 'lucide-react';
import type { Vendor, Invoice } from './types/accounts-receivable';

const API_URL = 'http://127.0.0.1:5001/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [vendors, setVendors] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAccountsReceivableData();
  }, []);

  const loadAccountsReceivableData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [vendorsResponse, invoicesResponse] = await Promise.all([
        fetch(`${API_URL}/vendors`),
        fetch(`${API_URL}/invoices`),
      ]);
      if (!vendorsResponse.ok || !invoicesResponse.ok) {
        throw new Error('Failed to fetch data from the server.');
      }
      const vendorsData = await vendorsResponse.json();
      const invoicesData = await invoicesResponse.json();
      setVendors(vendorsData);
      setInvoices(invoicesData);
    } catch (error) {
      console.error('Error loading accounts receivable data:', error);
      setError('Could not connect to the accounts receivable service. Please ensure the backend is running and refresh.');
    } finally {
      setLoading(false);
    }
  };

  // This function now just triggers a refresh, as the chatbot handles the transaction logic.
 const handleTransactionComplete = async (transactionData: any, fromAccountName: string, toAccountName?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_id: transactionData.invoice_id,
          amount: transactionData.amount,
          payment_method: transactionData.payment_method || 'check',
          notes: transactionData.description
        }),
      });

      if (!response.ok) {
        const errorResult = await response.json();
        throw new Error(errorResult.message || 'Failed to process payment.');
      }
      
      // Payment successful, now reload all data
      await loadAccountsReceivableData();

    } catch (error: any) {
      console.error('Error processing payment:', error);
      setError(error.message || 'An unexpected error occurred during the payment.');
    } finally {
      setLoading(false);
    }
  };

  // New function to handle vendor creation
  const handleVendorCreate = async (vendorData: { name: string, email: string, phone?: string }) => {
    try {
      const response = await fetch(`${API_URL}/vendors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(vendorData),
      });
      if (!response.ok) throw new Error('Vendor creation failed.');
      const newVendor = await response.json();
      // Refresh all data to get the new vendor list
      await loadAccountsReceivableData();
      return newVendor; // Return new vendor details if needed
    } catch (err) {
      console.error("Error creating vendor:", err);
      setError("There was an error creating the new vendor.");
      throw err; // Re-throw to be caught by the calling component
    }
  };


  const renderContent = () => {
    if (loading) return <div className="text-center p-8">Loading Accounts Receivable Data...</div>;
    if (error) return <div className="text-center p-8 text-red-600 bg-red-50 rounded-lg">{error}</div>;

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard vendors={vendors} invoices={invoices} />;
      case 'invoices':
        return <Transactions invoices={invoices} vendors={vendors} />;
      case 'payments':
        return <Transfer vendors={vendors} onPaymentComplete={handleTransactionComplete} onVendorCreate={handleVendorCreate} />;
      case 'analytics':
        return <Analytics invoices={invoices} vendors={vendors} />;
      default:
        return <Dashboard vendors={vendors} invoices={invoices} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Layout activeTab={activeTab} onTabChange={setActiveTab}>{renderContent()}</Layout>
      <button onClick={() => setIsChatOpen(!isChatOpen)} className={`fixed bottom-6 right-6 p-4 rounded-full shadow-lg transition-all z-40 ${isChatOpen ? 'bg-red-600' : 'bg-blue-600'} text-white`}>
        {isChatOpen ? <X/> : <MessageCircle/>}
      </button>
      {isChatOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-xl shadow-2xl border z-30">
          <ChatBot />
        </div>
      )}
    </div>
  );
}

export default App;