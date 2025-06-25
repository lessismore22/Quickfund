export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone: string;
  role: 'user' | 'admin' | 'staff';
  createdAt: string;
  isVerified: boolean;
  isPhoneVerified: boolean;
  isBvnVerified: boolean;
  profilePicture?: string;
  dateOfBirth?: string;
  address?: string;
  occupation?: string;
  monthlyIncome?: number;
  creditScore?: number;
}

export interface LoanApplication {
  id: string;
  userId: string;
  amount: number;
  purpose: string;
  term: number; // in months
  status: 'pending' | 'approved' | 'rejected' | 'disbursed' | 'active' | 'completed' | 'defaulted';
  creditScore: number;
  interestRate: number;
  monthlyPayment: number;
  totalAmount: number;
  appliedAt: string;
  approvedAt?: string;
  disbursedAt?: string;
  rejectedAt?: string;
  rejectionReason?: string;
  employmentType: string;
  monthlyIncome: number;
  collateral?: string;
  guarantor?: {
    name: string;
    phone: string;
    email: string;
    relationship: string;
  };
}

export interface Loan {
  id: string;
  applicationId: string;
  userId: string;
  principalAmount: number;
  currentBalance: number;
  interestRate: number;
  monthlyPayment: number;
  nextPaymentDate: string;
  totalPaid: number;
  paymentsRemaining: number;
  status: 'active' | 'completed' | 'overdue' | 'defaulted';
  startDate: string;
  endDate: string;
  purpose: string;
  latePaymentFee: number;
  gracePeriod: number;
}

export interface Payment {
  id: string;
  loanId: string;
  amount: number;
  paymentDate: string;
  paymentMethod: 'card' | 'bank_transfer' | 'virtual_account' | 'ussd' | 'mobile_money';
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  transactionId: string;
  reference: string;
  gateway: 'paystack' | 'flutterwave' | 'interswitch';
  fees: number;
  description?: string;
}

export interface Repayment {
  id: string;
  loanId: string;
  amount: number;
  principalAmount: number;
  interestAmount: number;
  dueDate: string;
  paidDate?: string;
  status: 'pending' | 'paid' | 'overdue' | 'partial';
  paymentId?: string;
  latePaymentFee: number;
  installmentNumber: number;
}

export interface PaymentMethod {
  id: string;
  userId: string;
  type: 'card' | 'bank_account' | 'virtual_account';
  isDefault: boolean;
  isActive: boolean;
  cardDetails?: {
    last4: string;
    brand: string;
    expiryMonth: string;
    expiryYear: string;
    cardType: string;
  };
  bankDetails?: {
    accountNumber: string;
    bankName: string;
    accountName: string;
    bankCode: string;
  };
  virtualAccountDetails?: {
    accountNumber: string;
    bankName: string;
    accountName: string;
  };
}

export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'loan' | 'payment' | 'system';
  isRead: boolean;
  createdAt: string;
  actionUrl?: string;
  metadata?: Record<string, any>;
}

export interface NotificationPreferences {
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  loanUpdates: boolean;
  paymentReminders: boolean;
  promotionalEmails: boolean;
  securityAlerts: boolean;
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: RegisterData) => Promise<boolean>;
  logout: () => void;
  updateUser: (user: User) => void;
  isLoading: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone: string;
  dateOfBirth?: string;
  occupation?: string;
  monthlyIncome?: number;
}

export interface LoanFormData {
  amount: number;
  purpose: string;
  term: number;
  monthlyIncome: number;
  employmentType: string;
  creditHistory: string;
  collateral?: string;
  guarantor?: {
    name: string;
    phone: string;
    email: string;
    relationship: string;
  };
}

export interface AdminStats {
  totalUsers: number;
  activeLoans: number;
  totalDisbursed: number;
  defaultRate: number;
  pendingApplications: number;
  overdueLoans: number;
  monthlyGrowth: number;
  portfolioHealth: number;
}

export interface AnalyticsData {
  loanMetrics: {
    totalLoans: number;
    approvalRate: number;
    defaultRate: number;
    averageLoanAmount: number;
    averageTerm: number;
  };
  paymentMetrics: {
    totalPayments: number;
    onTimePaymentRate: number;
    averagePaymentAmount: number;
    collectionEfficiency: number;
  };
  userMetrics: {
    totalUsers: number;
    activeUsers: number;
    newUsersThisMonth: number;
    userRetentionRate: number;
  };
  financialMetrics: {
    totalRevenue: number;
    netIncome: number;
    operatingExpenses: number;
    profitMargin: number;
  };
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  database: 'ok' | 'slow' | 'down';
  redis: 'ok' | 'slow' | 'down';
  externalApis: 'ok' | 'slow' | 'down';
  responseTime: number;
  uptime: number;
  version: string;
}