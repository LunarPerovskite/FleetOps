import { useState, useEffect, createContext, useContext } from 'react';
import { authAPI } from '../lib/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  org_id: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('fleetops_token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);
  
  const fetchUser = async () => {
    try {
      setIsLoading(true);
      const response = await authAPI.me();
      setUser(response);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch user');
      localStorage.removeItem('fleetops_token');
    } finally {
      setIsLoading(false);
    }
  };
  
  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await authAPI.login(email, password);
      localStorage.setItem('fleetops_token', response.access_token);
      await fetchUser();
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  const register = async (data: any) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await authAPI.register(data);
      localStorage.setItem('fleetops_token', response.access_token);
      await fetchUser();
    } catch (err: any) {
      setError(err.message || 'Registration failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  const logout = () => {
    localStorage.removeItem('fleetops_token');
    setUser(null);
    setError(null);
    window.location.href = '/login';
  };
  
  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
