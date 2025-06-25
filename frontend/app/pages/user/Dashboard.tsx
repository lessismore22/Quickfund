import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DollarSign, CreditCard, Clock, TrendingUp, Plus, Eye, Bell, AlertTriangle } from 'lucide-react';
import Card from '../../components/UI/Card';
import Button from '../../components/UI/Button';
import { Link } from 'react-router-dom';
import { useApi } from '../../hooks/useApi';
import mockApiService from '../../services/mockApi';
import LoadingSpinner from '../../components/UI/LoadingSpinner';
Promise<{
  data: NotificationOptions;
  status: number;
  statusText: string;
  headers: Record<string, any>;
  config: Record<string, any>;
}>


const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Fetch dashboard data using mock API
  const { data: loans, loading: loansLoading } = useApi(() => mockApiService.getActiveLoans());
  const { data: notifications, loading: notificationsLoading } = useApi(() => 
    mockApiService.getNotifications({ limit: 5, unread: true })
  );
  const { data: repayments, loading: repaymentsLoading } = useApi(() => 
    mockApiService.getRepayments({ status: 'pending', limit: 1 })
  );

  // Calculate stats from real data
  const stats = React.useMemo(() => {
    if (!loans?.results) {
      return [
        {
          title: 'Active Loans',
          value: '0',
          icon: CreditCard,
          color: 'text-primary-600',
          bgColor: 'bg-primary-100'
        },
        {
          title: 'Total Borrowed',
          value: '₦0',
          icon: DollarSign,
          color: 'text-success-600',
          bgColor: 'bg-success-100'
        },
        {
          title: 'Next Payment',
          value: 'No payments due',
          icon: Clock,
          color: 'text-warning-600',
          bgColor: 'bg-warning-100'
        },
        {
          title: 'Credit Score',
          value: user?.creditScore?.toString() || 'N/A',
          icon: TrendingUp,
          color: 'text-success-600',
          bgColor: 'bg-success-100'
        }
      ];
    }

    const activeLoans = loans.results.filter((loan: any) => loan.status === 'active');
    const totalBorrowed = activeLoans.reduce((sum: number, loan: any) => sum + loan.principalAmount, 0);
    const nextPayment = repayments?.results?.[0];

    return [
      {
        title: 'Active Loans',
        value: activeLoans.length.toString(),
        icon: CreditCard,
        color: 'text-primary-600',
        bgColor: 'bg-primary-100'
      },
      {
        title: 'Total Borrowed',
        value: `₦${totalBorrowed.toLocaleString()}`,
        icon: DollarSign,
        color: 'text-success-600',
        bgColor: 'bg-success-100'
      },
      {
        title: 'Next Payment',
        value: nextPayment ? `₦${nextPayment.amount.toLocaleString()}` : 'No payments due',
        icon: Clock,
        color: 'text-warning-600',
        bgColor: 'bg-warning-100'
      },
      {
        title: 'Credit Score',
        value: user?.creditScore?.toString() || 'N/A',
        icon: TrendingUp,
        color: 'text-success-600',
        bgColor: 'bg-success-100'
      }
    ];
  }, [loans, repayments, user]);

  if (loansLoading || notificationsLoading || repaymentsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.firstName}!
          </h1>
          <p className="text-gray-600 mt-2">
            Here's an overview of your loans and account activity.
          </p>
        </div>

        {/* Verification Alert */}
        {(!user?.isPhoneVerified || !user?.isBvnVerified) && (
          <Card className="mb-8 border-warning-200 bg-warning-50">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-warning-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-warning-800">
                  Complete Your Profile Verification
                </h3>
                <p className="text-sm text-warning-700 mt-1">
                  {!user?.isPhoneVerified && 'Verify your phone number '}
                  {!user?.isPhoneVerified && !user?.isBvnVerified && 'and '}
                  {!user?.isBvnVerified && 'verify your BVN '}
                  to unlock higher loan limits and better rates.
                </p>
                <div className="mt-3 flex space-x-3">
                  {!user?.isPhoneVerified && (
                    <Button size="sm" variant="outline">
                      Verify Phone
                    </Button>
                  )}
                  {!user?.isBvnVerified && (
                    <Button size="sm" variant="outline">
                      Verify BVN
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} hover>
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-2 space-y-8">
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Link to="/apply">
                  <Button fullWidth icon={Plus} iconPosition="left" size="lg">
                    Apply for New Loan
                  </Button>
                </Link>
                <Link to="/loans">
                  <Button variant="outline" fullWidth icon={Eye} iconPosition="left" size="lg">
                    View All Loans
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Active Loans */}
            <Card>
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Your Active Loans</h2>
                <Link to="/loans">
                  <Button variant="ghost" size="sm">
                    View All
                  </Button>
                </Link>
              </div>
              
              {(loans?.results?.length ?? 0) > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Loan Details
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Monthly Payment
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Next Payment
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {loans && loans.results.slice(0, 3).map((loan: any) => (
                        <tr key={loan.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                Loan #{loan.id.slice(-8)}
                              </div>
                              <div className="text-sm text-gray-500">{loan.purpose}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ₦{loan.principalAmount.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            ₦{loan.monthlyPayment.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(loan.nextPaymentDate).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800 capitalize">
                              {loan.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <CreditCard className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Loans</h3>
                  <p className="text-gray-600 mb-4">Apply for your first loan to get started.</p>
                  <Link to="/apply">
                    <Button>Apply for Loan</Button>
                  </Link>
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Next Payment */}
            {repayments?.results?.[0] && (
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Next Payment Due</h3>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 mb-1">
                    ₦{repayments.results[0].amount.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600 mb-4">
                    Due {new Date(repayments.results[0].dueDate).toLocaleDateString()}
                  </div>
                  <Button variant="primary" size="sm" fullWidth>
                    Make Payment
                  </Button>
                </div>
              </Card>
            )}

            {/* Recent Notifications */}
            <Card>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Recent Notifications</h3>
                <Button variant="ghost" size="sm" icon={Bell}>
                  View All
                </Button>
              </div>
              
              {notifications?.results && notifications.results.length > 0 ? (
                <div className="space-y-3">
                  {notifications.results.slice(0, 3).map((notification: any) => (
                    <div key={notification.id} className="p-3 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-900">{notification.title}</h4>
                      <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(notification.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600">No new notifications</p>
              )}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;