import React, { useState } from 'react';
import { Search, Download, Eye, DollarSign, Calendar, AlertTriangle } from 'lucide-react';
import Card from '../../components/UI/Card';
import Input from '../../components/UI/Input';
import Button from '../../components/UI/Button';

const AdminLoans: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);

  // Mock loans data
  const loans = [
    {
      id: '1',
      borrower: {
        firstName: 'John',
        lastName: 'Smith',
        email: 'john.smith@email.com',
        phone: '+1-555-0101'
      },
      principalAmount: 5000,
      currentBalance: 3200,
      interestRate: 7.99,
      monthlyPayment: 245,
      nextPaymentDate: '2024-02-15',
      totalPaid: 1800,
      paymentsRemaining: 14,
      status: 'active',
      startDate: '2023-08-15',
      endDate: '2025-08-15',
      purpose: 'Home Improvement'
    },
    {
      id: '2',
      borrower: {
        firstName: 'Sarah',
        lastName: 'Johnson',
        email: 'sarah.j@email.com',
        phone: '+1-555-0102'
      },
      principalAmount: 3500,
      currentBalance: 2100,
      interestRate: 9.99,
      monthlyPayment: 180,
      nextPaymentDate: '2024-02-20',
      totalPaid: 1400,
      paymentsRemaining: 12,
      status: 'active',
      startDate: '2023-10-20',
      endDate: '2025-10-20',
      purpose: 'Debt Consolidation'
    },
    {
      id: '3',
      borrower: {
        firstName: 'Mike',
        lastName: 'Davis',
        email: 'mike.davis@email.com',
        phone: '+1-555-0103'
      },
      principalAmount: 2000,
      currentBalance: 0,
      interestRate: 6.99,
      monthlyPayment: 0,
      nextPaymentDate: '',
      totalPaid: 2140,
      paymentsRemaining: 0,
      status: 'completed',
      startDate: '2022-05-10',
      endDate: '2023-05-10',
      purpose: 'Medical Expenses'
    },
    {
      id: '4',
      borrower: {
        firstName: 'Emily',
        lastName: 'Brown',
        email: 'emily.brown@email.com',
        phone: '+1-555-0104'
      },
      principalAmount: 4500,
      currentBalance: 3800,
      interestRate: 12.99,
      monthlyPayment: 220,
      nextPaymentDate: '2024-01-10',
      totalPaid: 700,
      paymentsRemaining: 18,
      status: 'overdue',
      startDate: '2023-12-10',
      endDate: '2025-12-10',
      purpose: 'Car Repair'
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

  const handleExport = () => {
    alert('Exporting loans data to CSV - This would generate a downloadable file');
  };

  const filteredLoans = loans.filter(loan => {
    const matchesSearch = 
      loan.borrower.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loan.borrower.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loan.borrower.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      loan.purpose.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || loan.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate summary stats
  const totalLoans = loans.length;
  const activeLoans = loans.filter(l => l.status === 'active').length;
  const overdueLoans = loans.filter(l => l.status === 'overdue').length;
  const totalOutstanding = loans.reduce((sum, loan) => sum + loan.currentBalance, 0);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">All Loans</h1>
          <p className="text-gray-600">
            Monitor and manage all active loans
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <div className="flex items-center">
              <div className="bg-primary-100 p-3 rounded-lg">
                <DollarSign className="h-6 w-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Loans</p>
                <p className="text-2xl font-bold text-gray-900">{totalLoans}</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="bg-success-100 p-3 rounded-lg">
                <Calendar className="h-6 w-6 text-success-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Loans</p>
                <p className="text-2xl font-bold text-gray-900">{activeLoans}</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="bg-error-100 p-3 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-error-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Overdue</p>
                <p className="text-2xl font-bold text-gray-900">{overdueLoans}</p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="bg-warning-100 p-3 rounded-lg">
                <DollarSign className="h-6 w-6 text-warning-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Outstanding</p>
                <p className="text-2xl font-bold text-gray-900">${totalOutstanding.toLocaleString()}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search loans..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="overdue">Overdue</option>
              </select>
            </div>

            <Button
              variant="outline"
              icon={Download}
              iconPosition="left"
              onClick={handleExport}
            >
              Export CSV
            </Button>
          </div>
        </Card>

        {/* Loans List */}
        <div className="space-y-4">
          {filteredLoans.map((loan) => (
            <Card key={loan.id} padding="none">
              <div className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-4">
                      <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {loan.borrower.firstName[0]}{loan.borrower.lastName[0]}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {loan.borrower.firstName} {loan.borrower.lastName}
                        </h3>
                        <p className="text-sm text-gray-600">Loan #{loan.id} • {loan.purpose}</p>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(loan.status)}`}>
                        {loan.status.charAt(0).toUpperCase() + loan.status.slice(1)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Principal</p>
                        <p className="font-semibold">${loan.principalAmount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Balance</p>
                        <p className="font-semibold">${loan.currentBalance.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Rate</p>
                        <p className="font-semibold">{loan.interestRate}%</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Payment</p>
                        <p className="font-semibold">
                          {loan.status === 'completed' ? 'Completed' : `$${loan.monthlyPayment}`}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Next Due</p>
                        <p className="font-semibold">
                          {loan.nextPaymentDate || 'N/A'}
                        </p>
                      </div>
                    </div>

                    {loan.status === 'overdue' && (
                      <div className="mt-4 p-3 bg-error-50 border border-error-200 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <AlertTriangle className="h-4 w-4 text-error-600" />
                          <span className="text-sm text-error-800 font-medium">
                            Payment overdue - Contact borrower immediately
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 lg:mt-0 lg:ml-6 flex flex-col space-y-2">
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
                        <h4 className="font-semibold text-gray-900 mb-3">Borrower Contact</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Email:</span>
                            <span>{loan.borrower.email}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Phone:</span>
                            <span>{loan.borrower.phone}</span>
                          </div>
                        </div>

                        <div className="mt-4">
                          <h5 className="font-medium text-gray-900 mb-2">Payment Progress</h5>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full"
                              style={{
                                width: `${((loan.principalAmount - loan.currentBalance) / loan.principalAmount) * 100}%`
                              }}
                            ></div>
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            {Math.round(((loan.principalAmount - loan.currentBalance) / loan.principalAmount) * 100)}% completed
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

        {filteredLoans.length === 0 && (
          <Card className="text-center py-12">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No loans found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search criteria or filters.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AdminLoans;