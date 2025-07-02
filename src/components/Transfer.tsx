import React, { useState } from 'react';
import { ArrowRight, Check, AlertCircle, CreditCard, PiggyBank, ExternalLink, PlusCircle } from 'lucide-react';
import type { Account, Transaction } from '../types/banking';

interface TransferProps {
  accounts: Account[];
  onTransactionComplete: (transaction: Omit<Transaction, 'id' | 'created_at' | 'status'>, fromAccountName: string, toAccountName?: string) => void;
  onAccountCreate: (accountData: { account_type: 'checking' | 'savings', name: string, balance: number }) => Promise<any>;
}

const Transfer: React.FC<TransferProps> = ({ accounts, onTransactionComplete, onAccountCreate }) => {
  const [transferType, setTransferType] = useState<'internal' | 'external'>('internal');
  const [fromAccount, setFromAccount] = useState('');
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  
  // State for creating a new account
  const [isCreatingNewAccount, setIsCreatingNewAccount] = useState(false);
  const [newAccountName, setNewAccountName] = useState('');
  const [newAccountType, setNewAccountType] = useState<'checking' | 'savings'>('checking');
  
  // State for external transfers remains the same
  const [externalRecipient, setExternalRecipient] = useState({
    name: '',
    accountNumber: '',
    routingNumber: '',
    bankName: ''
  });


  const getAccountIcon = (type: string) => {
    switch (type) {
      case 'checking': return <CreditCard className="h-5 w-5 text-blue-600" />;
      case 'savings': return <PiggyBank className="h-5 w-5 text-green-600" />;
      default: return <CreditCard className="h-5 w-5 text-gray-600" />;
    }
  };

  const handleTransfer = async () => {
    const fromAcc = accounts.find(acc => acc.id === fromAccount);
    if (!fromAcc || !amount) return;

    setIsProcessing(true);

    try {
        let toAccName: string | undefined = undefined;

        if (isCreatingNewAccount && newAccountName) {
            // Step 1: Create the new account first
            const newAccountResponse = await onAccountCreate({
                name: newAccountName,
                account_type: newAccountType,
                balance: 0 // Start with 0 balance before transfer
            });
            // The new account's name is what we'll use for the transfer tool
            toAccName = newAccountResponse.name;
        } else if (transferType === 'internal') {
            const toAcc = accounts.find(acc => acc.id === toAccount);
            toAccName = toAcc?.name;
        }

        // Step 2: Perform the transaction via the backend handler
        const newTransactionData = {
            amount: parseFloat(amount),
            type: 'transfer' as 'transfer',
            description: description || (transferType === 'internal' ? 'Internal Transfer' : `Transfer to ${externalRecipient.name}`),
            category: 'Transfer',
            // Backend handles linking accounts by name now via the tool
        };
        
        await onTransactionComplete(newTransactionData, fromAcc.name, toAccName);
        
        setShowConfirmation(true);
        setTimeout(() => {
            // Reset form
            setShowConfirmation(false);
            setFromAccount('');
            setToAccount('');
            setAmount('');
            setDescription('');
            setIsCreatingNewAccount(false);
            setNewAccountName('');
        }, 3000);

    } catch (error) {
        console.error("Transfer failed:", error);
        // Add user-facing error message
    } finally {
        setIsProcessing(false);
    }
  };

  const selectedFromAccount = accounts.find(acc => acc.id === fromAccount);
  const selectedToAccount = accounts.find(acc => acc.id === toAccount);
  const transferAmount = parseFloat(amount) || 0;

  if (showConfirmation) {
    return (
      <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Transfer Successful!</h2>
        <p className="text-gray-600">${transferAmount.toLocaleString()} has been transferred.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Transfer Money</h2>
        
        {/* Form Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
                {/* From Account */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">From Account</label>
                    <select value={fromAccount} onChange={(e) => setFromAccount(e.target.value)} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">Select account...</option>
                        {accounts.map((account) => (
                            <option key={account.id} value={account.id}>
                                {account.name} - ${account.balance.toLocaleString()}
                            </option>
                        ))}
                    </select>
                </div>

                {/* To Account (Internal) or New Account Form */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">To Account</label>
                    <div className="space-y-4">
                        <select value={toAccount} onChange={(e) => setToAccount(e.target.value)} disabled={isCreatingNewAccount} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100">
                            <option value="">Select an existing account...</option>
                            {accounts.filter(acc => acc.id !== fromAccount).map((account) => (
                                <option key={account.id} value={account.id}>{account.name}</option>
                            ))}
                        </select>
                        
                        <div className="relative flex items-start">
                            <div className="flex items-center h-5">
                                <input id="new-account-checkbox" type="checkbox" checked={isCreatingNewAccount} onChange={(e) => setIsCreatingNewAccount(e.target.checked)} className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded" />
                            </div>
                            <div className="ml-3 text-sm">
                                <label htmlFor="new-account-checkbox" className="font-medium text-gray-700">Create a new account for this transfer</label>
                            </div>
                        </div>

                        {isCreatingNewAccount && (
                            <div className="p-4 border rounded-lg space-y-3 bg-blue-50">
                                <input type="text" value={newAccountName} onChange={e => setNewAccountName(e.target.value)} placeholder="New Account Name" className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                                <select value={newAccountType} onChange={e => setNewAccountType(e.target.value as any)} className="w-full px-3 py-2 border border-gray-300 rounded-md">
                                    <option value="checking">Checking</option>
                                    <option value="savings">Savings</option>
                                </select>
                            </div>
                        )}
                    </div>
                </div>

                {/* Amount */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
                    <div className="relative">
                        <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                        <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="0.00" />
                    </div>
                    {selectedFromAccount && transferAmount > selectedFromAccount.balance && (
                        <p className="mt-1 text-sm text-red-600 flex items-center"><AlertCircle className="h-4 w-4 mr-1"/>Insufficient funds</p>
                    )}
                </div>
            </div>

            {/* Transfer Preview */}
            <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Transfer Summary</h3>
                {/* Preview logic can be simplified or enhanced as needed */}
                <div className="space-y-4">
                    {selectedFromAccount && (
                        <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                           <p>From: {selectedFromAccount.name}</p> <span className="text-red-600">-${transferAmount.toLocaleString()}</span>
                        </div>
                    )}
                    <div className="flex justify-center"><ArrowRight className="h-6 w-6 text-gray-400" /></div>
                    {isCreatingNewAccount && newAccountName ? (
                         <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                            <p>To New Account: {newAccountName}</p> <span className="text-green-600">+${transferAmount.toLocaleString()}</span>
                         </div>
                    ) : selectedToAccount && (
                        <div className="flex items-center justify-between p-4 bg-white rounded-lg">
                             <p>To: {selectedToAccount.name}</p> <span className="text-green-600">+${transferAmount.toLocaleString()}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>

        <div className="mt-8 flex justify-center">
            <button onClick={handleTransfer} disabled={isProcessing || !fromAccount || !amount || (!toAccount && !isCreatingNewAccount) || (isCreatingNewAccount && !newAccountName)} className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center">
                {isProcessing ? 'Processing...' : 'Complete Transfer'}
            </button>
        </div>
      </div>
    </div>
  );
};

export default Transfer;
