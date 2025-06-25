import React, { useState } from 'react';
import { Calendar, DollarSign, Download, CreditCard, AlertCircle, CheckCircle } from 'lucide-react';
import Card from '../../components/UI/Card';
import Button from '../../components/UI/Button';

const UserLoans: React.FC = () => {
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);

  // Mock loan data
  const loans = [
    {
      id: '1',
      amount: 5000,
      currentBalance: 3200,
      purpose: 'Home Improvement',
      status: 'active',
      interestRate: 7.99,
      monthlyPayment: 245,
      nextPaymentDate: '2024-02-15',
      totalPaid: 1800,
      paymentsRemaining: 14,
      startDate: '2023-08-15',
      endDate: '2025-08-15'
    },
    {
      id: '2',
      amount: 3500,
      currentBalance: 2100,
      purpose: 'Debt Consolidation',
      status: 'active',
      interestRate: 9.99,
      monthlyPayment: 180,
      nextPaymentDate: '2024-02-20',
      totalPaid: 1400,
      paymentsRemaining: 12,
      startDate: '2023-10-20',
      endDate: '2025-10-20'
    },
    {
      id: '3',
      amount: 2000,
      currentBalance: 0,
      purpose: 'Medical Expenses',
      status: 'completed',
      interestRate: 6.99,
      monthlyPayment: 0,
      nextPaymentDate: '',
      totalPaid: 2140,
      paymentsRemaining: 0,
      startDate: '2022-05-10',
      endDate: '2023-05-10'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-success-100 text-success-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      case 'overdue':
        return 'bg-error-100 text-error-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleMakePayment = (loanId: string) => {
    // Mock payment processing
    alert(`Payment processing for loan ${loanId} - This would integrate with payment gateway`);
  };

  const handleDownloadAgreement = (loanId: string) => {
    // Mock PDF download
    alert(`Downloading loan agreement for loan ${loanId} - This would generate a PDF`);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Loans</h1>
          <p className="text-gray-600">
            Manage your loans and make payments
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <div className="flex items-center">
              <div className="bg-primary-100 p-3 rounded-lg">
                <DollarSign className="h-6 w-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Outstanding</p>
                <p className="text-2xl font-bold text-gray-900">₦5,300</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="bg-success-100 p-3 rounded-lg">
                <CheckCircle className="h-6 w-6 text-success-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Paid</p>
                <p className="text-2xl font-bold text-gray-900">₦5,340</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="bg-warning-100 p-3 rounded-lg">
                <Calendar className="h-6 w-6 text-warning-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Next Payment</p>
                <p className="text-2xl font-bold text-gray-900">₦245</p>
                <p className="text-xs text-gray-500">Due Feb 15</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Loans List */}
        <div className="space-y-6">
          {loans.map((loan) => (
            <Card key={loan.id} padding="none">
              <div className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Loan #{loan.id} - {loan.purpose}
                      </h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(loan.status)}`}>
                        {loan.status.charAt(0).toUpperCase() + loan.status.slice(1)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Original Amount</p>
                        <p className="font-semibold">${loan.amount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Current Balance</p>
                        <p className="font-semibold">₦{loan.currentBalance.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Interest Rate</p>
                        <p className="font-semibold">{loan.interestRate}% APR</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Monthly Payment</p>
                        <p className="font-semibold">
                          {loan.status === 'completed' ? 'Completed' : `$${loan.monthlyPayment}`}
                        </p>
                      </div>
                    </div>

                    {loan.status === 'active' && (
                      <div className="mt-4 p-3 bg-primary-50 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="h-4 w-4 text-primary-600" />
                          <span className="text-sm text-primary-800">
                            Next payment of ${loan.monthlyPayment} due on {loan.nextPaymentDate}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 lg:mt-0 lg:ml-6 flex flex-col space-y-2">
                    {loan.status === 'active' && (
                      <Button
                        onClick={() => handleMakePayment(loan.id)}
                        icon={CreditCard}
                        iconPosition="left"
                        size="sm"
                      >
                        Make Payment
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      onClick={() => handleDownloadAgreement(loan.id)}
                      icon={Download}
                      iconPosition="left"
                      size="sm"
                    >
                      Download Agreement
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => setSelectedLoan(selectedLoan === loan.id ? null : loan.id)}
                      size="sm"
                    >
                      {selectedLoan === loan.id ? 'Hide Details' : 'View Details'}
                    </Button>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedLoan === loan.id && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Loan Details</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Start Date:</span>
                            <span>{loan.startDate}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">End Date:</span>
                            <span>{loan.endDate}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Paid:</span>
                            <span>${loan.totalPaid.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Payments Remaining:</span>
                            <span>{loan.paymentsRemaining}</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Payment Progress</h4>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span>Progress</span>
                              <span>{Math.round(((loan.amount - loan.currentBalance) / loan.amount) * 100)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary-600 h-2 rounded-full"
                                style={{
                                  width: `${((loan.amount - loan.currentBalance) / loan.amount) * 100}%`
                                }}
                              ></div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-600">
                            ${(loan.amount - loan.currentBalance).toLocaleString()} of ${loan.amount.toLocaleString()} paid
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>

        {loans.length === 0 && (
          <Card className="text-center py-12">
            <DollarSign className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No loans found
            </h3>
            <p className="text-gray-600 mb-4">
              You don't have any loans yet. Apply for your first loan to get started.
            </p>
            <Button>Apply for Loan</Button>
          </Card>
        )}
      </div>
    </div>
  );
};

export default UserLoans;