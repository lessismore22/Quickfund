// Mock API service for development when Django backend is not available
import { User, LoanApplication, Loan, Payment, Repayment } from '../types';

// Mock data
const mockLoans: Loan[] = [
  {
    id: '1',
    applicationId: 'app-1',
    userId: '1',
    principalAmount: 100000,
    currentBalance: 65000,
    interestRate: 12.5,
    monthlyPayment: 9500,
    nextPaymentDate: '2024-02-15',
    totalPaid: 35000,
    paymentsRemaining: 8,
    status: 'active',
    startDate: '2023-08-15',
    endDate: '2024-08-15',
    purpose: 'Business Expansion',
    latePaymentFee: 0,
    gracePeriod: 7
  },
  {
    id: '2',
    applicationId: 'app-2',
    userId: '1',
    principalAmount: 50000,
    currentBalance: 25000,
    interestRate: 10.5,
    monthlyPayment: 4500,
    nextPaymentDate: '2024-02-20',
    totalPaid: 25000,
    paymentsRemaining: 6,
    status: 'active',
    startDate: '2023-10-20',
    endDate: '2024-10-20',
    purpose: 'Equipment Purchase',
    latePaymentFee: 0,
    gracePeriod: 7
  }
];

const mockRepayments: Repayment[] = [
  {
    id: '1',
    loanId: '1',
    amount: 9500,
    principalAmount: 8000,
    interestAmount: 1500,
    dueDate: '2024-02-15',
    status: 'pending',
    latePaymentFee: 0,
    installmentNumber: 9
  },
  {
    id: '2',
    loanId: '2',
    amount: 4500,
    principalAmount: 4000,
    interestAmount: 500,
    dueDate: '2024-02-20',
    status: 'pending',
    latePaymentFee: 0,
    installmentNumber: 7
  }
];

const mockNotifications = [
  {
    id: '1',
    userId: '1',
    title: 'Payment Reminder',
    message: 'Your loan payment of ₦9,500 is due on February 15, 2024',
    type: 'payment',
    isRead: false,
    createdAt: '2024-02-10T10:00:00Z',
    actionUrl: '/payments'
  },
  {
    id: '2',
    userId: '1',
    title: 'Loan Approved',
    message: 'Congratulations! Your loan application has been approved.',
    type: 'loan',
    isRead: false,
    createdAt: '2024-02-08T14:30:00Z',
    actionUrl: '/loans'
  }
];

class MockApiService {
  submitLoanApplication(submitLoanApplication: any, arg1: { onSuccess: () => void; onError: (error: any) => void; }): { mutate: any; loading: any; } {
      throw new Error('Method not implemented.');
  }
  // Simulate network delay
  private delay(ms: number = 500) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Mock response wrapper
  private mockResponse<T>(data: T) {
    return {
      data,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {}
    };
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    await this.delay(1000);
    // This will be handled by AuthContext
    throw new Error('Use AuthContext for login');
  }

  async register(userData: any) {
    await this.delay(1500);
    // This will be handled by AuthContext
    throw new Error('Use AuthContext for registration');
  }

  async logout() {
    await this.delay(300);
    return this.mockResponse({ message: 'Logged out successfully' });
  }

  async getUserProfile() {
    await this.delay(500);
    const user = JSON.parse(localStorage.getItem('quickfund_user') || 'null');
    return this.mockResponse(user);
  }

  // Loan endpoints
  async getActiveLoans() {
    await this.delay(800);
    const userId = JSON.parse(localStorage.getItem('quickfund_user') || '{}').id;
    const userLoans = mockLoans.filter(loan => loan.userId === userId && loan.status === 'active');
    return this.mockResponse({
      results: userLoans,
      count: userLoans.length,
      next: null,
      previous: null
    });
  }

  async getLoans(params?: any) {
    await this.delay(800);
    const userId = JSON.parse(localStorage.getItem('quickfund_user') || '{}').id;
    const userLoans = mockLoans.filter(loan => loan.userId === userId);
    return this.mockResponse({
      results: userLoans,
      count: userLoans.length,
      next: null,
      previous: null
    });
  }

  async applyForLoan(loanData: any) {
    await this.delay(2000);
    const newApplication: LoanApplication = {
      id: Date.now().toString(),
      userId: JSON.parse(localStorage.getItem('quickfund_user') || '{}').id,
      amount: loanData.amount,
      purpose: loanData.purpose,
      term: loanData.term,
      status: 'pending',
      creditScore: 720,
      interestRate: 12.5,
      monthlyPayment: Math.round((loanData.amount * 0.125) / 12 + loanData.amount / loanData.term),
      totalAmount: loanData.amount * 1.125,
      appliedAt: new Date().toISOString(),
      employmentType: loanData.employmentType,
      monthlyIncome: loanData.monthlyIncome,
      guarantor: loanData.guarantor
    };
    return this.mockResponse(newApplication);
  }

  async calculateLoan(amount: number, term: number) {
    await this.delay(300);
    const interestRate = 12.5; // 12.5% annual
    const monthlyRate = interestRate / 100 / 12;
    const monthlyPayment = Math.round(
      (amount * monthlyRate * Math.pow(1 + monthlyRate, term)) /
      (Math.pow(1 + monthlyRate, term) - 1)
    );
    
    return this.mockResponse({
      amount,
      term,
      interestRate,
      monthlyPayment,
      totalAmount: monthlyPayment * term
    });
  }

  // Repayment endpoints
  async getRepayments(params?: any) {
    await this.delay(600);
    const userId = JSON.parse(localStorage.getItem('quickfund_user') || '{}').id;
    const userRepayments = mockRepayments.filter(repayment => {
      const loan = mockLoans.find(l => l.id === repayment.loanId);
      return loan?.userId === userId;
    });
    
    let filteredRepayments = userRepayments;
    if (params?.status) {
      filteredRepayments = userRepayments.filter(r => r.status === params.status);
    }
    if (params?.limit) {
      filteredRepayments = filteredRepayments.slice(0, params.limit);
    }
    
    return this.mockResponse({
      results: filteredRepayments,
      count: filteredRepayments.length,
      next: null,
      previous: null
    });
  }

  // Notification endpoints
  async getNotifications(params?: any) {
    await this.delay(400);
    const userId = JSON.parse(localStorage.getItem('quickfund_user') || '{}').id;
    let userNotifications = mockNotifications.filter(n => n.userId === userId);
    
    if (params?.unread) {
      userNotifications = userNotifications.filter(n => !n.isRead);
    }
    if (params?.limit) {
      userNotifications = userNotifications.slice(0, params.limit);
    }
    
    return this.mockResponse({
      results: userNotifications,
      count: userNotifications.length,
      next: null,
      previous: null
    });
  }

  // Payment endpoints
  async initiatePayment(paymentData: any) {
    await this.delay(1000);
    return this.mockResponse({
      reference: `ref_${Date.now()}`,
      authorization_url: 'https://checkout.paystack.com/mock',
      access_code: 'mock_access_code'
    });
  }

  async verifyPayment(reference: string) {
    await this.delay(800);
    return this.mockResponse({
      status: 'success',
      reference,
      amount: 9500,
      currency: 'NGN'
    });
  }

  // Placeholder methods for other endpoints
  async refreshToken(refreshToken: string) {
    await this.delay(300);
    return this.mockResponse({
      access: `mock_access_token_${Date.now()}`,
      refresh: refreshToken
    });
  }

  async verifyPhone(phoneNumber: string) {
    await this.delay(1000);
    return this.mockResponse({ message: 'Verification code sent' });
  }

  async confirmPhoneVerification(code: string) {
    await this.delay(800);
    return this.mockResponse({ message: 'Phone verified successfully' });
  }

  async verifyBVN(bvn: string) {
    await this.delay(2000);
    return this.mockResponse({ message: 'BVN verified successfully' });
  }

  // Add other mock methods as needed...
  async updateUserProfile(data: any) {
    await this.delay(800);
    return this.mockResponse(data);
  }

  async getLoanDetail(loanId: string) {
    await this.delay(600);
    const loan = mockLoans.find(l => l.id === loanId);
    return this.mockResponse(loan);
  }

  async getPaymentHistory(params?: any) {
    await this.delay(600);
    return this.mockResponse({ results: [], count: 0 });
  }

  async getPaymentMethods() {
    await this.delay(400);
    return this.mockResponse({ results: [], count: 0 });
  }

  async addPaymentMethod(methodData: any) {
    await this.delay(800);
    return this.mockResponse(methodData);
  }

  async removePaymentMethod(methodId: string) {
    await this.delay(500);
    return this.mockResponse({ message: 'Payment method removed' });
  }
}

export const mockApiService = new MockApiService();
export default mockApiService;