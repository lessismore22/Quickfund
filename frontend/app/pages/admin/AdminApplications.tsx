import React, { useState } from 'react';
import { Search, Filter, Download, Eye, Check, X, Clock } from 'lucide-react';
import Card from '../../components/UI/Card';
import Input from '../../components/UI/Input';
import Button from '../../components/UI/Button';

const AdminApplications: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedApplication, setSelectedApplication] = useState<string | null>(null);

  // Mock applications data
  const applications = [
    {
      id: '1',
      applicant: {
        firstName: 'John',
        lastName: 'Smith',
        email: 'john.smith@email.com',
        phone: '+1-555-0101'
      },
      amount: 5000,
      purpose: 'Home Improvement',
      term: 24,
      status: 'pending',
      creditScore: 720,
      monthlyIncome: 6500,
      employmentType: 'Full-time Employee',
      appliedAt: '2024-01-15T10:30:00Z',
      interestRate: 7.99,
      monthlyPayment: 245
    },
    {
      id: '2',
      applicant: {
        firstName: 'Sarah',
        lastName: 'Johnson',
        email: 'sarah.j@email.com',
        phone: '+1-555-0102'
      },
      amount: 3500,
      purpose: 'Debt Consolidation',
      term: 18,
      status: 'approved',
      creditScore: 680,
      monthlyIncome: 5200,
      employmentType: 'Full-time Employee',
      appliedAt: '2024-01-15T09:15:00Z',
      approvedAt: '2024-01-15T09:45:00Z',
      interestRate: 9.99,
      monthlyPayment: 215
    },
    {
      id: '3',
      applicant: {
        firstName: 'Mike',
        lastName: 'Davis',
        email: 'mike.davis@email.com',
        phone: '+1-555-0103'
      },
      amount: 7500,
      purpose: 'Business Expansion',
      term: 36,
      status: 'under_review',
      creditScore: 750,
      monthlyIncome: 8500,
      employmentType: 'Self-employed',
      appliedAt: '2024-01-15T08:45:00Z',
      interestRate: 6.99,
      monthlyPayment: 231
    },
    {
      id: '4',
      applicant: {
        firstName: 'Emily',
        lastName: 'Brown',
        email: 'emily.brown@email.com',
        phone: '+1-555-0104'
      },
      amount: 2500,
      purpose: 'Medical Expenses',
      term: 12,
      status: 'rejected',
      creditScore: 580,
      monthlyIncome: 3200,
      employmentType: 'Part-time Employee',
      appliedAt: '2024-01-14T16:20:00Z',
      rejectedAt: '2024-01-14T17:15:00Z',
      rejectionReason: 'Insufficient income relative to requested amount'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-success-100 text-success-800';
      case 'pending':
        return 'bg-warning-100 text-warning-800';
      case 'under_review':
        return 'bg-primary-100 text-primary-800';
      case 'rejected':
        return 'bg-error-100 text-error-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <Check className="h-4 w-4" />;
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'under_review':
        return <Eye className="h-4 w-4" />;
      case 'rejected':
        return <X className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatStatus = (status: string) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const handleApprove = (applicationId: string) => {
    alert(`Approving application ${applicationId} - This would update the database`);
  };

  const handleReject = (applicationId: string) => {
    const reason = prompt('Please provide a rejection reason:');
    if (reason) {
      alert(`Rejecting application ${applicationId} with reason: ${reason}`);
    }
  };

  const handleExport = () => {
    alert('Exporting applications data to CSV - This would generate a downloadable file');
  };

  const filteredApplications = applications.filter(app => {
    const matchesSearch = 
      app.applicant.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.applicant.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.applicant.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.purpose.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Loan Applications</h1>
          <p className="text-gray-600">
            Review and manage loan applications
          </p>
        </div>

        {/* Filters and Search */}
        <Card className="mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search applications..."
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
                <option value="pending">Pending</option>
                <option value="under_review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
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

        {/* Applications List */}
        <div className="space-y-4">
          {filteredApplications.map((application) => (
            <Card key={application.id} padding="none">
              <div className="p-6">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-4">
                      <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {application.applicant.firstName[0]}{application.applicant.lastName[0]}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {application.applicant.firstName} {application.applicant.lastName}
                        </h3>
                        <p className="text-sm text-gray-600">{application.applicant.email}</p>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(application.status)}`}>
                        {getStatusIcon(application.status)}
                        <span className="ml-1">{formatStatus(application.status)}</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Loan Amount</p>
                        <p className="font-semibold">${application.amount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Purpose</p>
                        <p className="font-semibold">{application.purpose}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Credit Score</p>
                        <p className="font-semibold">{application.creditScore}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Monthly Income</p>
                        <p className="font-semibold">${application.monthlyIncome.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 lg:mt-0 lg:ml-6 flex flex-col space-y-2">
                    {application.status === 'pending' && (
                      <>
                        <Button
                          onClick={() => handleApprove(application.id)}
                          icon={Check}
                          iconPosition="left"
                          size="sm"
                        >
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleReject(application.id)}
                          icon={X}
                          iconPosition="left"
                          size="sm"
                        >
                          Reject
                        </Button>
                      </>
                    )}
                    <Button
                      variant="ghost"
                      onClick={() => setSelectedApplication(selectedApplication === application.id ? null : application.id)}
                      size="sm"
                    >
                      {selectedApplication === application.id ? 'Hide Details' : 'View Details'}
                    </Button>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedApplication === application.id && (
                  <div className="mt-6 pt-6 border-t border-gray-200">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Application Details</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Applied:</span>
                            <span>{new Date(application.appliedAt).toLocaleDateString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Term:</span>
                            <span>{application.term} months</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Interest Rate:</span>
                            <span>{application.interestRate}% APR</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Monthly Payment:</span>
                            <span>${application.monthlyPayment}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Employment:</span>
                            <span>{application.employmentType}</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Contact Information</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Phone:</span>
                            <span>{application.applicant.phone}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Email:</span>
                            <span>{application.applicant.email}</span>
                          </div>
                        </div>

                        {application.status === 'rejected' && application.rejectionReason && (
                          <div className="mt-4 p-3 bg-error-50 border border-error-200 rounded-lg">
                            <h5 className="font-medium text-error-800 mb-1">Rejection Reason</h5>
                            <p className="text-sm text-error-700">{application.rejectionReason}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>

        {filteredApplications.length === 0 && (
          <Card className="text-center py-12">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No applications found
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

export default AdminApplications;