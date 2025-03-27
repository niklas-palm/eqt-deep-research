import { useAuth } from './auth';
import { toast } from 'sonner';
import { useCallback } from 'react';
import { authConfig } from './auth-config';

// API error handling
class ApiError extends Error {
  statusCode: number;
  isAuthError: boolean;
  details?: any;
  
  constructor(message: string, statusCode: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.isAuthError = statusCode === 401 || statusCode === 403;
    this.details = details;
  }
}

/**
 * Handle authentication errors by clearing session and redirecting
 */
const handleAuthError = () => {
  // Don't redirect if already on login page
  if (window.location.pathname.includes('/login')) return;
  
  toast.error('Session Expired', {
    description: 'Please sign in again.',
  });
  
  // Clear auth storage
  sessionStorage.clear();
  localStorage.removeItem('oidc.user');
  
  // Redirect to login
  setTimeout(() => {
    window.location.href = `/login?expired=true`;
  }, 1000);
};

// Hook for API calls
export const useApi = () => {
  const { getIdToken } = useAuth();

  // Core API request function
  const apiRequest = useCallback(async <T>(
    endpoint: string,
    options: RequestInit = {},
    authType: 'auth' | 'public' = 'auth'
  ): Promise<T> => {
    try {
      // Set up headers based on authentication type
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options.headers as Record<string, string>
      };
      
      if (authType === 'auth') {
        const token = await getIdToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
      }
      
      // Make request
      const requestUrl = `${authConfig.apiUrl}${endpoint}`;
      
      const response = await fetch(requestUrl, {
        ...options,
        headers
      });
      
      // Handle errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || `API error: ${response.status}`;
        
        // Create ApiError with details for special handling
        throw new ApiError(errorMessage, response.status, errorData);
      }
      
      const data = await response.json();
      return data as T;
    } catch (error) {
      // Handle authentication errors
      if (error instanceof ApiError && error.isAuthError) {
        handleAuthError();
      } 
      // Handle other errors
      else {
        toast.error('Error', {
          description: error instanceof Error ? error.message : 'An unexpected error occurred',
        });
      }
      
      throw error;
    }
  }, [getIdToken]);

  // Public health endpoint (no auth)
  const getHello = useCallback(() => {
    return apiRequest<{ message: string }>('/api/public/health', {}, 'public');
  }, [apiRequest]);

  // Protected profile endpoint (requires auth)
  const getProfile = useCallback(() => {
    return apiRequest<{ userId: string; email: string; message: string }>('/api/auth/me');
  }, [apiRequest]); // This dependency is stable since apiRequest is wrapped in useCallback with getIdToken

  
  // Research API methods
  const createResearch = useCallback((query: string, isDeepResearch: boolean = false) => {
    return apiRequest<{ 
      job_id: string;
      status: string;
      message: string;
    }>('/api/auth/research', {
      method: 'POST',
      body: JSON.stringify({
        query,
        deep_research: isDeepResearch
      })
    });
  }, [apiRequest]);
  
  const getResearchStatus = useCallback((jobId: string) => {
    return apiRequest<{
      jobId: string;
      status: string;
      message?: string;
      result?: string;
      error?: string;
      created_at: string;
      updated_at: string;
    }>(`/api/auth/research/${jobId}`);
  }, [apiRequest]);

  // Return all API methods
  return {
    getHello,
    getProfile,
    createResearch,
    getResearchStatus
  };
};