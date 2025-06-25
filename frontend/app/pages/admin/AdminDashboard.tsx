import React from 'react';
import { Users, DollarSign, FileText, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import Card from '../../components/UI/Card';

const AdminDashboard: React.FC = () => {
  // Mock data for admin dashboard
  const stats = [
    {
      title: 'Total Users',
      value: '2,847',
      change: '+12%',
      changeType: 'positive',
      icon: Users,
      color: 'text-primary-600',
      bgColor: 'bg-primary-100'
    },
    {
      title: 'Active Loans',
      value: '1,234',
      change: '+8%',
      changeType: 'positive',
      icon: DollarSign,
      color: 'text-success-600',
      bgColor: 'bg-success-100'
    },
    {
      title: 'Pending Applications',
      value: '89',
      change: '+23%',
      changeType: 'positive',
      icon: FileText,
      color: 'text-warning-600',
      bgColor: 'bg-warning-100'
    },
    {
      title: 'Total Funded',
      value: '$2.4M',
      change: '+15%',
      changeType: 'positive',
      icon: TrendingUp,
      color: 'text-success-600',
      bgColor: 'bg-success-100'
    }
  ];

  const recentApplications = [
    {
      id: '1',
      applicant: 'John Smith',
      amount: 5000,
      purpose: 'Home Improvement',
      status: 'pending',
      appliedAt: '2024-01-15T10:30:00Z',
      creditScore: 720
    },
    {
      id: '2',
      applicant: 'Sarah Johnson',
      amount: 3500,
      purpose: 'Debt Consolidation',
      status: 'approved',
      appliedAt: '2024-01-15T09:15:00Z',
      creditScore: 680
    },
    {
      id: '3',
      applicant: 'Mike Davis',
      amount: 7500,
      purpose: 'Business Expansion',
      status: 'under_review',
      appliedAt: '2024-01-15T08:45:00Z',
      creditScore: 750
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

  const formatStatus = (status: string) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">
            Overview of loan applications and system metrics
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} hover>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className={`text-sm ${
                    stat.changeType === 'positive' ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {stat.change} from last month
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Applications */}
          <Card>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Recent Applications</h2>
              <a href="/admin/applications" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
                View All
              </a>
            </div>
            
            <div className="space-y-4">
              {recentApplications.map((application) => (
                <div key={application.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {application.applicant.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{application.applicant}</p>
                        <p className="text-sm text-gray-600">
                          ${application.amount.toLocaleString()} • {application.purpose}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(application.status)}`}>
                      {formatStatus(application.status)}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Score: {application.creditScore}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* System Alerts */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">System Alerts</h2>
            
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-4 bg-warning-50 border border-warning-200 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-warning-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-warning-800">High Application Volume</p>
                  <p className="text-sm text-warning-700">
                    89 applications pending review. Consider increasing review capacity.
                  </p>
                  <p className="text-xs text-warning-600 mt-1">2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-4 bg-success-50 border border-success-200 rounded-lg">
                <CheckCircle className="h-5 w-5 text-success-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-success-800">System Update Complete</p>
                  <p className="text-sm text-success-700">
                    Credit scoring model updated successfully. Improved accuracy by 12%.
                  </p>
                  <p className="text-xs text-success-600 mt-1">1 day ago</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-4 bg-primary-50 border border-primary-200 rounded-lg">
                <FileText className="h-5 w-5 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-primary-800">Monthly Report Ready</p>
                  <p className="text-sm text-primary-700">
                    January 2024 lending report is available for download.
                  </p>
                  <p className="text-xs text-primary-600 mt-1">3 days ago</p>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Quick Stats */}
        <div className="mt-8">
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Statistics</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary-600 mb-2">94.2%</div>
                <div className="text-sm text-gray-600">Approval Rate</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-success-600 mb-2">2.1%</div>
                <div className="text-sm text-gray-600">Default Rate</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-warning-600 mb-2">4.2 min</div>
                <div className="text-sm text-gray-600">Avg Processing Time</div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;