import { useState, useEffect } from 'react';
import { AxiosResponse } from 'axios';
import mockApiService from '../services/mockApi';

// Add type definition for ImportMeta.env
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_USE_MOCK_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

// Check if we should use mock API (when Django backend is not available)
const USE_MOCK_API = !import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_USE_MOCK_API === 'true';

export function useApi<T = any>(
  apiCall: () => Promise<AxiosResponse<T>>,
  options: UseApiOptions = {}
) {
  const { immediate = true, onSuccess, onError } = options;
  
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiCall();
      setState({
        data: response.data,
        loading: false,
        error: null,
      });
      
      if (onSuccess) {
        onSuccess(response.data);
      }
      
      return response.data;
    } catch (error: any) {
      // Handle network errors gracefully
      let errorMessage = 'An error occurred';
      
      if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
        errorMessage = 'Unable to connect to server. Using offline mode.';
      } else {
        errorMessage = error.response?.data?.message || error.message || 'An error occurred';
      }
      
      setState({
        data: null,
        loading: false,
        error: errorMessage,
      });
      
      if (onError) {
        onError(error);
      }
      
      throw error;
    }
  };

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, []);

  return {
    ...state,
    execute,
    refetch: execute,
  };
}

export function useMutation<T = any, P = any>(
  apiCall: (params: P) => Promise<AxiosResponse<T>>,
  options: UseApiOptions = {}
) {
  const { onSuccess, onError } = options;
  
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = async (params: P) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const response = await apiCall(params);
      setState({
        data: response.data,
        loading: false,
        error: null,
      });
      
      if (onSuccess) {
        onSuccess(response.data);
      }
      
      return response.data;
    } catch (error: any) {
      // Handle network errors gracefully
      let errorMessage = 'An error occurred';
      
      if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
        errorMessage = 'Unable to connect to server. Please try again.';
      } else {
        errorMessage = error.response?.data?.message || error.message || 'An error occurred';
      }
      
      setState({
        data: null,
        loading: false,
        error: errorMessage,
      });
      
      if (onError) {
        onError(error);
      }
      
      throw error;
    }
  };

  return {
    ...state,
    mutate,
  };
}