import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthContextType, RegisterData } from '../types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Mock users data for development (since Django backend isn't running)
const mockUsers: (User & { password: string })[] = [
  {
    id: '1',
    email: 'user@quickfund.com',
    password: 'password123',
    firstName: 'John',
    lastName: 'Doe',
    phone: '+234-801-234-5678',
    role: 'user',
    createdAt: '2024-01-15T10:00:00Z',
    isVerified: true,
    isPhoneVerified: true,
    isBvnVerified: false,
    creditScore: 720,
    monthlyIncome: 250000,
    occupation: 'Software Engineer'
  },
  {
    id: '2',
    email: 'admin@quickfund.com',
    password: 'admin123',
    firstName: 'Admin',
    lastName: 'User',
    phone: '+234-801-234-5679',
    role: 'admin',
    createdAt: '2024-01-01T10:00:00Z',
    isVerified: true,
    isPhoneVerified: true,
    isBvnVerified: true,
    creditScore: 800,
    monthlyIncome: 500000,
    occupation: 'Administrator'
  }
];

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth data
    const initializeAuth = async () => {
      const storedUser = localStorage.getItem('quickfund_user');
      const token = localStorage.getItem('access_token');
      
      if (storedUser && token) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (error) {
          // Invalid stored data, clear it
          localStorage.removeItem('quickfund_user');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Check against mock users
      const foundUser = mockUsers.find(u => u.email === email && u.password === password);
      
      if (foundUser) {
        const { password: _, ...userWithoutPassword } = foundUser;
        
        // Mock JWT tokens
        const mockTokens = {
          access: `mock_access_token_${Date.now()}`,
          refresh: `mock_refresh_token_${Date.now()}`
        };
        
        // Store tokens and user data
        localStorage.setItem('access_token', mockTokens.access);
        localStorage.setItem('refresh_token', mockTokens.refresh);
        localStorage.setItem('quickfund_user', JSON.stringify(userWithoutPassword));
        
        setUser(userWithoutPassword);
        setIsLoading(false);
        return true;
      }
      
      setIsLoading(false);
      return false;
    } catch (error) {
      setIsLoading(false);
      return false;
    }
  };

  const register = async (userData: RegisterData): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Check if user already exists
      const existingUser = mockUsers.find(u => u.email === userData.email);
      if (existingUser) {
        setIsLoading(false);
        return false;
      }
      
      const newUser: User = {
        id: Date.now().toString(),
        email: userData.email,
        firstName: userData.firstName,
        lastName: userData.lastName,
        phone: userData.phone,
        role: 'user',
        createdAt: new Date().toISOString(),
        isVerified: false,
        isPhoneVerified: false,
        isBvnVerified: false,
        dateOfBirth: userData.dateOfBirth,
        occupation: userData.occupation,
        monthlyIncome: userData.monthlyIncome
      };
      
      // Mock JWT tokens
      const mockTokens = {
        access: `mock_access_token_${Date.now()}`,
        refresh: `mock_refresh_token_${Date.now()}`
      };
      
      // Store tokens and user data
      localStorage.setItem('access_token', mockTokens.access);
      localStorage.setItem('refresh_token', mockTokens.refresh);
      localStorage.setItem('quickfund_user', JSON.stringify(newUser));
      
      setUser(newUser);
      setIsLoading(false);
      return true;
    } catch (error) {
      setIsLoading(false);
      return false;
    }
  };

  const logout = async () => {
    try {
      // In a real app, this would call the API logout endpoint
      // await apiService.logout();
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      setUser(null);
      localStorage.removeItem('quickfund_user');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem('quickfund_user', JSON.stringify(updatedUser));
  };

  const value: AuthContextType = {
    user,
    login,
    register,
    logout,
    updateUser,
    isLoading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};