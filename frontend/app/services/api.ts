import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Remove these interfaces from here and add them to a .d.ts file for global scope

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.data.access);
              originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    return this.api.post('/auth/login/', { email, password });
  }

  async register(userData: any) {
    return this.api.post('/auth/register/', userData);
  }

  async logout() {
    return this.api.post('/auth/logout/');
  }

  async refreshToken(refreshToken: string) {
    return this.api.post('/auth/token/refresh/', { refresh: refreshToken });
  }

  async resetPassword(email: string) {
    return this.api.post('/auth/password/reset/', { email });
  }

  async changePassword(oldPassword: string, newPassword: string) {
    return this.api.post('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  // User endpoints
  async getUserProfile() {
    return this.api.get('/users/profile/');
  }

  async updateUserProfile(data: any) {
    return this.api.patch('/users/profile/update/', data);
  }

  async verifyPhone(phoneNumber: string) {
    return this.api.post('/users/verify/phone/', { phone_number: phoneNumber });
  }

  async confirmPhoneVerification(code: string) {
    return this.api.post('/users/verify/phone/confirm/', { verification_code: code });
  }

  async verifyBVN(bvn: string) {
    return this.api.post('/users/verify/bvn/', { bvn });
  }

  // Loan endpoints
  async getLoans(params?: any) {
    return this.api.get('/loans/', { params });
  }

  async getLoanDetail(loanId: string) {
    return this.api.get(`/loans/${loanId}/`);
  }

  async applyForLoan(loanData: any) {
    return this.api.post('/loans/apply/', loanData);
  }

  async calculateLoan(amount: number, term: number) {
    return this.api.post('/loans/calculator/', { amount, term });
  }

  async getLoanHistory() {
    return this.api.get('/loans/history/');
  }

  async getActiveLoans() {
    return this.api.get('/loans/active/');
  }

  async getOverdueLoans() {
    return this.api.get('/loans/overdue/');
  }

  // Payment endpoints
  async initiatePayment(paymentData: any) {
    return this.api.post('/payments/initiate/', paymentData);
  }

  async verifyPayment(reference: string) {
    return this.api.get(`/payments/verify/${reference}/`);
  }

  async getPaymentHistory(params?: any) {
    return this.api.get('/payments/history/', { params });
  }

  async getPaymentMethods() {
    return this.api.get('/payments/methods/');
  }

  async addPaymentMethod(methodData: any) {
    return this.api.post('/payments/methods/add/', methodData);
  }

  async removePaymentMethod(methodId: string) {
    return this.api.delete(`/payments/methods/${methodId}/remove/`);
  }

  async createVirtualAccount() {
    return this.api.post('/payments/virtual-accounts/create/');
  }

  // Repayment endpoints
  async getRepayments(params?: any) {
    return this.api.get('/repayments/', { params });
  }

  async getRepaymentSchedule(loanId?: string) {
    const url = loanId ? `/repayments/schedule/${loanId}/` : '/repayments/schedule/';
    return this.api.get(url);
  }

  async makeEarlyRepayment(loanId: string, amount: number) {
    return this.api.post(`/repayments/early/${loanId}/`, { amount });
  }

  async getOverdueRepayments() {
    return this.api.get('/repayments/overdue/');
  }

  // Notification endpoints
  async getNotifications(params?: any) {
    return this.api.get('/notifications/', { params });
  }

  async markNotificationRead(notificationId: string) {
    return this.api.patch(`/notifications/${notificationId}/read/`);
  }

  async markAllNotificationsRead() {
    return this.api.patch('/notifications/mark-all-read/');
  }

  async getNotificationPreferences() {
    return this.api.get('/notifications/preferences/');
  }

  async updateNotificationPreferences(preferences: any) {
    return this.api.patch('/notifications/preferences/', preferences);
  }

  // Admin endpoints
  async getAdminDashboard() {
    return this.api.get('/admin/dashboard/');
  }

  async getAdminUsers(params?: any) {
    return this.api.get('/admin/users/', { params });
  }

  async getAdminLoans(params?: any) {
    return this.api.get('/admin/loans/', { params });
  }

  async approveLoan(loanId: string) {
    return this.api.post(`/loans/${loanId}/approve/`);
  }

  async rejectLoan(loanId: string, reason: string) {
    return this.api.post(`/loans/${loanId}/reject/`, { reason });
  }

  async disburseLoan(loanId: string) {
    return this.api.post(`/loans/${loanId}/disburse/`);
  }

  async getAdminReports(type: string, params?: any) {
    return this.api.get(`/admin/reports/${type}/`, { params });
  }

  async exportReport(type: string, format: string = 'csv') {
    return this.api.get(`/admin/reports/export/`, {
      params: { type, format },
      responseType: 'blob',
    });
  }

  // Analytics endpoints
  async getAnalyticsOverview() {
    return this.api.get('/analytics/overview/');
  }

  async getLoanAnalytics(params?: any) {
    return this.api.get('/analytics/loans/', { params });
  }

  async getPaymentAnalytics(params?: any) {
    return this.api.get('/analytics/payments/', { params });
  }

  async getUserAnalytics(params?: any) {
    return this.api.get('/analytics/users/', { params });
  }

  async getPerformanceMetrics() {
    return this.api.get('/analytics/performance/');
  }

  // System endpoints
  async getSystemHealth() {
    return this.api.get('/system/health/');
  }

  async getSystemLogs(params?: any) {
    return this.api.get('/system/logs/', { params });
  }
}

export const apiService = new ApiService();
export default apiService;