import { ReactNode, createContext, useContext } from 'react';
import { useAuth as useOidcAuth, AuthProvider as OidcAuthProvider } from 'react-oidc-context';
import { toast } from 'sonner';
import { authConfig } from './auth-config';

// User type definition
export interface User {
  email?: string;
  name?: string;
  sub?: string;
}

// Auth context interface
export interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  login: () => void;
  logout: () => void;
  getIdToken: () => Promise<string | null>;
}

// Create context with undefined fallback
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider wrapper component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  return (
    <OidcAuthProvider {...authConfig}>
      <AuthProviderInternal>{children}</AuthProviderInternal>
    </OidcAuthProvider>
  );
};

/**
 * Internal provider that handles the actual auth logic
 */
const AuthProviderInternal = ({ children }: { children: ReactNode }) => {
  const oidcAuth = useOidcAuth();

  // Extract user info from OIDC auth
  const user = oidcAuth.user ? {
    email: oidcAuth.user.profile.email,
    name: oidcAuth.user.profile.name,
    sub: oidcAuth.user.profile.sub,
  } : null;

  /**
   * Login function - redirects to Cognito hosted UI
   */
  const login = () => {
    oidcAuth.signinRedirect();
  };

  /**
   * Logout function - removes user
   */
  const logout = () => {
    oidcAuth.removeUser();
    toast.success('Signed out');
  };

  /**
   * Get ID token for API calls with automatic renewal
   */
  const getIdToken = async (): Promise<string | null> => {
    if (!oidcAuth.user) return null;

    // Check if token is expired and needs refresh
    if (oidcAuth.user.expired) {
      try {
        // Try to silently renew the token
        const user = await oidcAuth.signinSilent();
        return user?.id_token || null;
      } catch (error) {
        return null;
      }
    }

    return oidcAuth.user.id_token || null;
  };

  // Provide auth context to children
  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: oidcAuth.isAuthenticated,
        isLoading: oidcAuth.isLoading,
        user,
        login,
        logout,
        getIdToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
